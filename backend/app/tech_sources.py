"""Bounded official RSS/Atom retrieval, source dates and deterministic relevance ranking."""
import hashlib
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener
import xml.etree.ElementTree as ET

SOURCES=[
 {'id':'python','name':'Python Insider','category':'Python','topic_id':'python-for-ml','feed':'https://blog.python.org/feeds/posts/default?alt=rss','hosts':['blog.python.org','www.python.org','python.org']},
 {'id':'sklearn','name':'scikit-learn releases','category':'ML','topic_id':'ml-project','feed':'https://github.com/scikit-learn/scikit-learn/releases.atom','hosts':['github.com'],'path_prefix':'/scikit-learn/scikit-learn/'},
 {'id':'mlflow','name':'MLflow releases','category':'MLOps','topic_id':'mlops-basics','feed':'https://github.com/mlflow/mlflow/releases.atom','hosts':['github.com'],'path_prefix':'/mlflow/mlflow/'},
 {'id':'pytorch','name':'PyTorch Blog','category':'ML','topic_id':'neural-networks','feed':'https://pytorch.org/feed/','hosts':['pytorch.org','www.pytorch.org']},
 {'id':'huggingface','name':'Hugging Face Transformers releases','category':'AI','topic_id':'embeddings','feed':'https://github.com/huggingface/transformers/releases.atom','hosts':['github.com'],'path_prefix':'/huggingface/transformers/'},
 {'id':'openai','name':'OpenAI News','category':'AI','topic_id':'agents','feed':'https://openai.com/news/rss.xml','hosts':['openai.com','www.openai.com']},
]
MAX_FEED_BYTES=2_000_000
WINDOW_DAYS=30

class PlainText(HTMLParser):
    def __init__(self):super().__init__();self.parts=[];self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style'):self.skip+=1
    def handle_endtag(self,tag):
        if tag in ('script','style'):self.skip=max(0,self.skip-1)
    def handle_data(self,data):
        if not self.skip:self.parts.append(data)

def plain(value):
    parser=PlainText();parser.feed(value or '')
    return re.sub(r'\s+',' ',' '.join(parser.parts)).strip()

def safe_link(url,source):
    parts=urlsplit(url.strip())
    if parts.scheme!='https' or parts.hostname not in source['hosts'] or parts.username or parts.password or parts.port not in (None,443):
        raise ValueError('Unapproved source URL')
    if source.get('path_prefix') and not parts.path.startswith(source['path_prefix']):raise ValueError('Wrong repository or source path')
    # Release and blog identities do not depend on tracking queries or fragments.
    return urlunsplit(('https',parts.netloc.lower(),parts.path,'',''))

class OfficialRedirect(HTTPRedirectHandler):
    def __init__(self,source):self.source=source
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        safe_link(newurl,self.source)
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def download_feed(source):
    request=Request(source['feed'],headers={'User-Agent':'Mozilla/5.0 LearningCoach/1.0','Accept':'application/rss+xml, application/atom+xml, application/xml'})
    with build_opener(OfficialRedirect(source)).open(request,timeout=15) as response:
        safe_link(response.url,source)
        content=response.read(MAX_FEED_BYTES+1)
    if len(content)>MAX_FEED_BYTES:raise ValueError('Feed exceeds size limit')
    return content

def parse_date(raw):
    if not raw:return None
    try:
        precision='date' if re.fullmatch(r'\d{4}-\d{2}-\d{2}',raw.strip()) else 'timestamp'
        try:value=datetime.fromisoformat(raw.strip().replace('Z','+00:00'))
        except ValueError:value=parsedate_to_datetime(raw.strip())
        # Do not invent the timezone of an unqualified timestamp.
        if value.tzinfo is None and precision!='date':return None
        return value.replace(tzinfo=timezone.utc) if precision=='date' else value.astimezone(timezone.utc),precision
    except (ValueError,TypeError,OverflowError):return None

def parse_feed(content,source,now):
    if len(content)>MAX_FEED_BYTES or b'<!DOCTYPE' in content.upper() or b'<!ENTITY' in content.upper():raise ValueError('Unsupported feed content')
    root=ET.fromstring(content)
    atom='{http://www.w3.org/2005/Atom}'
    entries=root.findall('./channel/item') if root.tag=='rss' else root.findall(atom+'entry') if root.tag==atom+'feed' else []
    if root.tag not in ('rss',atom+'feed'):raise ValueError('Expected RSS or Atom')
    articles=[]
    for entry in entries[:100]:
        if root.tag=='rss':
            title=plain(entry.findtext('title'));url=entry.findtext('link','')
            published=entry.findtext('pubDate') or entry.findtext('{http://purl.org/dc/elements/1.1/}date')
            updated=None;body=entry.findtext('description') or entry.findtext('{http://purl.org/rss/1.0/modules/content/}encoded') or ''
        else:
            title=plain(entry.findtext(atom+'title'))
            links=entry.findall(atom+'link');url=next((l.get('href','') for l in links if l.get('rel','alternate')=='alternate'),'')
            published=entry.findtext(atom+'published');updated=entry.findtext(atom+'updated')
            body=entry.findtext(atom+'content') or entry.findtext(atom+'summary') or ''
        parsed=parse_date(published or updated)
        if not parsed or not title:continue
        when,precision=parsed
        if when>now or when<now-timedelta(days=WINDOW_DAYS):continue
        try:url=safe_link(url,source)
        except (ValueError,TypeError):continue
        excerpt=plain(body)[:1800]
        if not excerpt:excerpt=title
        articles.append({'id':hashlib.sha256(url.encode()).hexdigest()[:24],'title':title[:220],
            'url':url,'source_id':source['id'],'source':source['name'],'category':source['category'],
            'topic_id':source['topic_id'],'source_date':when.isoformat(),'date_kind':'published' if published else 'updated',
            'date_precision':precision,'source_excerpt':excerpt})
    return articles

def fetch_updates(now):
    def one(source):
        try:
            articles=parse_feed(download_feed(source),source,now)
            return articles,{'id':source['id'],'name':source['name'],'status':'ok','recent_entries':len(articles),'feed_url':source['feed']}
        except Exception:
            return [],{'id':source['id'],'name':source['name'],'status':'unavailable','recent_entries':0,'feed_url':source['feed']}
    with ThreadPoolExecutor(max_workers=6) as pool:results=list(pool.map(one,SOURCES))
    return [article for articles,_ in results for article in articles],[status for _,status in results]

SIGNALS={'security':9,'vulnerability':9,'breaking':7,'deprecated':6,'deprecation':6,'release':4,'released':4,
         'introducing':4,'launch':4,'performance':3,'inference':3,'training':3,'evaluation':3,'tracking':3,
         'pipeline':3,'model':2,'agent':2,'retrieval':2,'transformer':2,'benchmark':2}

def relevance(article):
    title=article['title'].casefold();text=title+' '+article['source_excerpt'].casefold()
    score=sum(weight*(2 if word in title else 1) for word,weight in SIGNALS.items() if re.search(r'\b'+re.escape(word)+r's?\b',text))
    version=re.search(r'\bv?(\d+)\.(\d+)\.(\d+)\b',title)
    if version:score+=6 if version[3]=='0' else 2
    if re.search(r'\b(alpha|beta|preview)\b|\drc\d',title):score-=8
    if any(term in title for term in ('ambassadors','sponsors','welcomes','members','conference','model catalog','partner','investment','funding')):score-=40
    return score

def select_updates(articles):
    ranked=sorted(articles,key=lambda a:(relevance(a),a['source_date']),reverse=True)
    selected=[];seen_urls=set();seen_sources=set()
    # Diversity: at most one item per official source; never pad with irrelevant posts.
    for article in ranked:
        if relevance(article)<4 or article['url'] in seen_urls or article['source_id'] in seen_sources:continue
        selected.append(article);seen_urls.add(article['url']);seen_sources.add(article['source_id'])
        if len(selected)==5:break
    return selected
