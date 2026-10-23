from datetime import datetime, timedelta, timezone
import json
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.tech_sources import SOURCES, parse_feed, safe_link, select_updates, MAX_FEED_BYTES
from app.tech_updates import validate_summaries
from test_profile import PROFILE

NOW=datetime(2026,10,23,16,tzinfo=timezone.utc)

def article(source=None,slug='new-release',when=None):
    source=source or SOURCES[0]
    return {'id':source['id']+'-'+slug,'title':'Important security release for model training',
        'url':f'https://{source["hosts"][0]}{source.get("path_prefix","/")}{slug}',
        'source_id':source['id'],'source':source['name'],'category':source['category'],'topic_id':source['topic_id'],
        'source_date':(when or NOW-timedelta(hours=2)).isoformat(),'date_kind':'published','date_precision':'timestamp',
        'source_excerpt':'This official security release fixes a model training issue and improves evaluation reliability.'}

def coverage(status='ok'):
    return [{'id':s['id'],'name':s['name'],'status':status,'recent_entries':1,'feed_url':s['feed']} for s in SOURCES]

def fixture_summaries(articles):
    return {'items':[{'article_id':a['id'],'summary':'The source reports a security fix for model training.',
        'why_it_matters':'Training workflow reliability is relevant to the ML project.',
        'learning_action':'Read the release notes and reproduce a small baseline comparison.',
        'evidence':'fixes a model training issue'} for a in articles]}

def rss(items):return ('<rss version="2.0"><channel>'+items+'</channel></rss>').encode()
def item(title,url,date):return f'<item><title>{title}</title><link>{url}</link><pubDate>{date}</pubDate><description><![CDATA[<p>Model release with security fixes.</p><script>bad()</script>]]></description></item>'

def test_feed_parser_rejects_future_old_undated_untrusted_links_and_html():
    content=rss(
        item('A release','https://blog.python.org/a?utm_source=test','Fri, 23 Oct 2026 12:00:00 GMT')+
        item('Future','https://blog.python.org/future','Sat, 24 Oct 2026 12:00:00 GMT')+
        item('Old','https://blog.python.org/old','Tue, 01 Sep 2026 12:00:00 GMT')+
        item('Missing','https://blog.python.org/undated','')+
        item('Unsafe','javascript:alert(1)','Fri, 23 Oct 2026 12:00:00 GMT')+
        item('Third party','https://example.com/a','Fri, 23 Oct 2026 12:00:00 GMT'))
    result=parse_feed(content,SOURCES[0],NOW)
    assert len(result)==1
    assert result[0]['url']=='https://blog.python.org/a'
    assert result[0]['date_kind']=='published'
    assert 'bad()' not in result[0]['source_excerpt'] and '<p>' not in result[0]['source_excerpt']

def test_atom_updated_date_is_not_invented_publication_date():
    content=b'''<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>v1.9.0</title><link href="https://github.com/scikit-learn/scikit-learn/releases/tag/1.9.0"/><updated>2026-10-22T10:00:00Z</updated><content>Model performance release</content></entry></feed>'''
    result=parse_feed(content,SOURCES[1],NOW)
    assert result[0]['date_kind']=='updated'
    assert result[0]['source_date'].startswith('2026-10-22')

@pytest.mark.parametrize('url',['http://blog.python.org/a','https://blog.python.org.evil.test/a','https://user:password@blog.python.org/a','https://blog.python.org:8000/a','file:///etc/passwd'])
def test_only_official_https_links(url):
    with pytest.raises(ValueError):safe_link(url,SOURCES[0])

def test_wrong_repository_and_unsafe_xml_are_rejected():
    with pytest.raises(ValueError):safe_link('https://github.com/attacker/repo/releases/1',SOURCES[1])
    with pytest.raises(ValueError):parse_feed(b'<!DOCTYPE rss><rss/>',SOURCES[0],NOW)
    with pytest.raises(ValueError):parse_feed(b'x'*(MAX_FEED_BYTES+1),SOURCES[0],NOW)

def test_relevance_limits_diversity_and_no_filler():
    articles=[article(s) for s in SOURCES]+[article(SOURCES[0],'another')]
    selected=select_updates(articles)
    assert len(selected)==5 and len({a['source_id'] for a in selected})==5
    unimportant={**article(),'title':'Welcome our new members','source_excerpt':'Community team photographs.'}
    assert select_updates([unimportant])==[]
    corporate={**article(),'title':'A new AI safety and security partnership','source_excerpt':'A model evaluation partner and investment announcement.'}
    assert select_updates([corporate])==[]

def test_reading_is_offline_refresh_defaults_token_free_and_cache_survives_restart(tmp_path):
    calls=[];clock=[NOW]
    def fetcher(now):calls.append(now);return [article()],coverage()
    def forbidden(_):raise AssertionError('Token-free refresh must not call the model')
    url=f'sqlite:///{tmp_path.as_posix()}/digest.db'
    with TestClient(create_app(url,news_fetcher=fetcher,news_summarizer=forbidden,news_clock=lambda:clock[0])) as c:
        c.put('/api/v1/profile',json=PROFILE)
        assert c.get('/api/v1/tech-updates').json()['digest'] is None and calls==[]
        digest=c.post('/api/v1/tech-updates/refresh',json={}).json()
        assert digest['digest']['mode']=='source_excerpt' and len(calls)==1
        assert digest['digest']['items'][0]['related']['lesson_id']
        c.get('/api/v1/tech-updates');c.get('/api/v1/tech-updates')
        assert len(calls)==1
        assert c.post('/api/v1/tech-updates/refresh',json={}).json()['cache_reused'] is True
        assert len(calls)==1
        clock[0]+=timedelta(minutes=2)
        assert c.post('/api/v1/tech-updates/refresh',json={}).json()['cache_reused'] is True
        assert len(calls)==2
    with TestClient(create_app(url,news_fetcher=fetcher,news_clock=lambda:clock[0])) as c:
        assert c.get('/api/v1/tech-updates').json()['digest']['items'][0]['title']==article()['title']
        assert len(calls)==2

def test_ai_is_explicit_validated_and_reused_for_unchanged_sources(tmp_path):
    clock=[NOW];calls=[]
    def summarize(items):calls.append(items);return fixture_summaries(items)
    with TestClient(create_app(f'sqlite:///{tmp_path.as_posix()}/ai.db',news_fetcher=lambda n:([article()],coverage()),news_summarizer=summarize,news_clock=lambda:clock[0])) as c:
        c.put('/api/v1/profile',json=PROFILE)
        first=c.post('/api/v1/tech-updates/refresh',json={'use_ai':True}).json()
        assert first['digest']['mode']=='ai_summary' and len(calls)==1
        clock[0]+=timedelta(minutes=2)
        second=c.post('/api/v1/tech-updates/refresh',json={'use_ai':True}).json()
        assert second['cache_reused'] is True and len(calls)==1
    bad=fixture_summaries([article()]);bad['items'][0]['evidence']='An invented passage not in the source'
    with pytest.raises(ValueError):validate_summaries(bad,[article()])
    bad=fixture_summaries([article()]);bad['items'][0]['article_id']='wrong-source'
    with pytest.raises(ValueError):validate_summaries(bad,[article()])

def test_invalid_ai_falls_back_to_source_excerpts(tmp_path):
    def invalid(items):return {'items':[]}
    with TestClient(create_app(f'sqlite:///{tmp_path.as_posix()}/fallback.db',news_fetcher=lambda n:([article()],coverage()),news_summarizer=invalid,news_clock=lambda:NOW)) as c:
        c.put('/api/v1/profile',json=PROFILE)
        data=c.post('/api/v1/tech-updates/refresh',json={'use_ai':True}).json()
        assert data['digest']['mode']=='source_excerpt'
        assert 'failed source checks' in data['digest']['notice']

def test_saved_snapshots_survive_new_digest_and_can_be_removed(tmp_path):
    clock=[NOW];items=[[article()]]
    with TestClient(create_app(f'sqlite:///{tmp_path.as_posix()}/saved.db',news_fetcher=lambda n:(items[0],coverage()),news_clock=lambda:clock[0])) as c:
        c.put('/api/v1/profile',json=PROFILE)
        original=c.post('/api/v1/tech-updates/refresh',json={}).json()['digest']['items'][0]
        path=f'/api/v1/tech-updates/{original["id"]}/save'
        saved=c.put(path,json={'saved':True}).json()
        assert saved['saved_items'][0]['saved']
        assert len(c.put(path,json={'saved':True}).json()['saved_items'])==1
        clock[0]+=timedelta(days=1);items[0]=[article(slug='different')]
        data=c.post('/api/v1/tech-updates/refresh',json={}).json()
        assert data['digest']['items'][0]['id']!=original['id']
        assert data['saved_items'][0]['id']==original['id']
        assert c.put(path,json={'saved':False}).json()['saved_items']==[]

def test_failed_refresh_retains_previous_digest_and_reports_source_status(tmp_path):
    clock=[NOW];available=[True]
    def fetcher(n):return ([article()],coverage()) if available[0] else ([],coverage('unavailable'))
    with TestClient(create_app(f'sqlite:///{tmp_path.as_posix()}/failure.db',news_fetcher=fetcher,news_clock=lambda:clock[0])) as c:
        c.put('/api/v1/profile',json=PROFILE)
        first=c.post('/api/v1/tech-updates/refresh',json={}).json()
        clock[0]+=timedelta(days=1);available[0]=False
        failed=c.post('/api/v1/tech-updates/refresh',json={}).json()
        assert failed['digest']==first['digest']|{'items':[{**first['digest']['items'][0],'is_today':False}]}
        assert failed['last_successful_at']==first['last_successful_at']
        assert failed['notice'] and failed['needs_refresh']
        assert all(s['status']=='unavailable' for s in failed['sources'])

def test_source_date_and_today_use_profile_timezone(tmp_path):
    early=article(when=datetime(2026,10,23,1,tzinfo=timezone.utc))
    with TestClient(create_app(f'sqlite:///{tmp_path.as_posix()}/time.db',news_fetcher=lambda n:([early],coverage()),news_clock=lambda:NOW)) as c:
        c.put('/api/v1/profile',json=PROFILE)
        data=c.post('/api/v1/tech-updates/refresh',json={}).json()
        assert data['today']=='2026-10-23'
        assert data['digest']['items'][0]['source_day']=='2026-10-22'
        assert data['digest']['items'][0]['is_today'] is False
