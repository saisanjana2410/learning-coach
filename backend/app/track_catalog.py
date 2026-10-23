"""Import the supplied five-track roadmap into reusable topic identities."""
import re
from pathlib import Path

ROLE_NAMES={
 'AI Engineer':'ai-engineer','React Frontend Developer':'react-frontend',
 'Python Developer':'python-developer','GenAI Engineer':'genai-engineer',
 'MERN Full Stack Developer':'mern-full-stack',
}
LEVEL_DESCRIPTIONS={
 'beginner':'New to the area; guided explanations and exercises.',
 'foundational':'Knows basics; builds small applications and practices core libraries.',
 'intermediate':'Can build projects; learns integrations, testing and debugging.',
 'advanced':'Focuses on system design, performance, security and production reliability.',
}

def slug(value):return re.sub(r'[^a-z0-9]+','-',value.casefold()).strip('-')

def resolve_role(title):
    text=title.casefold().strip()
    for name,role_id in ROLE_NAMES.items():
        if text in (name.casefold(),role_id):return role_id
    if 'genai' in text or 'generative ai' in text:return 'genai-engineer'
    if 'mern' in text or 'full stack' in text or 'full-stack' in text:return 'mern-full-stack'
    if 'react' in text or 'frontend' in text or 'front-end' in text:return 'react-frontend'
    if 'python' in text:return 'python-developer'
    if any(word in text for word in ('ai','ml','machine learning','artificial intelligence')):return 'ai-engineer'
    return None

MODULE_TITLES={
 'python':'Python','ml':'Machine learning','math':'Math and statistics','data-analysis':'Data analysis',
 'deep-learning':'Deep learning','ai':'AI and LLM applications','engineering':'APIs and deployment',
 'mlops':'MLOps','responsible-ai':'Responsible AI','system-design':'System design',
 'web':'Web fundamentals','html':'HTML','css':'CSS','javascript':'JavaScript','react':'React',
 'typescript':'TypeScript','ui':'UI engineering','testing':'Testing and debugging','security':'Security',
 'databases':'Databases','node':'Node.js','express':'Express.js','mongodb':'MongoDB',
 'git':'Git and collaboration','automation':'Files and automation',
}

def module_for_section(title):
    text=title.casefold()
    if 'python' in text or text=='functions and modules':return 'python'
    if 'mathematics' in text:return 'math'
    if 'data analysis' in text:return 'data-analysis'
    if text in ('machine learning fundamentals','model evaluation','feature engineering'):return 'ml'
    if text in ('deep learning','specialized ai'):return 'deep-learning'
    if text=='mlops':return 'mlops'
    if text=='responsible ai':return 'responsible-ai'
    if 'system design' in text or 'advanced backend' in text or 'advanced full stack' in text:return 'system-design'
    if 'deployment' in text or text in ('web apis','production frontend','full stack integration'):return 'engineering'
    if 'authentication' in text or 'security' in text:return 'security'
    if 'testing' in text or text=='error handling and testing':return 'testing'
    if text=='files and automation':return 'automation'
    if text=='databases':return 'databases'
    if text in ('web fundamentals','web foundations','html and css'):return 'web'
    if text=='html':return 'html'
    if text=='css':return 'css'
    if 'javascript' in text:return 'javascript'
    if 'typescript' in text:return 'typescript'
    if 'react' in text or text=='state management':return 'react'
    if text=='ui engineering':return 'ui'
    if text=='node.js':return 'node'
    if text=='express.js':return 'express'
    if text=='mongodb':return 'mongodb'
    if text=='async and background work':return 'python'
    return 'ai'

def topic_aliases(title,module):
    text=title.casefold()
    if module=='javascript':
        if 'functions' in text or 'scope' in text or 'closures' in text:return ['javascript-functions']
        if 'promises' in text or 'async/await' in text:return ['javascript-async']
        if 'arrays and objects' in text:return ['javascript-collections']
    direct={
      'python syntax and data types':['python-basics'],'variables and types':['python-basics'],
      'conditions, loops and functions':['python-control-flow','python-functions'],
      'conditions and loops':['python-control-flow'], 'lists, dictionaries and comprehensions':['python-collections'],
      'strings and collections':['python-strings','python-collections'], 'oop and exception handling':['python-oop','python-exceptions'],
      'python functions and oop':['python-functions','python-oop'], 'functions and return values':['python-functions'],
      'arguments and keyword parameters':['python-functions'],'scope and closures':['python-functions'],
      'virtual environments and packages':['python-packages'],'virtual environments and pip':['python-packages'],
      'modules and packages':['python-packages'],'comprehensions':['python-collections'],
      'iterators and generators':['python-collections'],'decorators':['python-functions'],
      'numpy arrays and broadcasting':['numpy'],'pandas dataframes':['pandas'],
      'linear algebra: vectors, matrices and tensors':['linear-algebra'],'matrix operations and dot products':['linear-algebra'],
      'probability and distributions':['probability'],'derivatives, gradients and optimization':['optimization'],
      'supervised vs unsupervised learning':['ml-introduction'],'linear and logistic regression':['linear-regression','classification'],
      'decision trees and random forests':['ensembles'],'knn, svm and clustering':['ml-neighbors','ml-svm','clustering'],
      'accuracy, precision, recall and f1':['model-evaluation'],'confusion matrices and roc-auc':['model-evaluation'],
      'cross-validation':['model-evaluation'],'data leakage and reproducible pipelines':['feature-engineering'],
      'fastapi fundamentals':['apis'],'fastapi routing':['apis'],'fastapi inference endpoints':['apis'],
      'request validation':['apis'],'pydantic validation':['apis'],'dependency injection':['apis'],
      'http clients and apis':['http-clients'],'http and rest':['web-http'],'internet and http':['web-http'],
      'http, https and dns':['web-http'],'client-server architecture':['web-client-server'],
      'git and github':['git-basics'],'command line':['command-line'],
      'semantic html':['html-semantics'],'forms and validation':['html-forms'] if module in ('html','web') else [module+'-forms'],
      'flexbox and grid':['css-layout'],'responsive design':['css-responsive'],
      'responsive design and media queries':['css-responsive'],'accessibility':['web-accessibility'],
      'accessibility fundamentals':['web-accessibility'],
      'jsx and components':['react-components'],'props and state':['react-props','react-state'],
      'props and component composition':['react-props'],'state and event handling':['react-state'],
      'usestate and useeffect':['react-hooks'],'hooks':['react-hooks'],'custom hooks':['react-custom-hooks'],
      'routing':['react-routing'],'react router':['react-routing'],'context api':['react-context'],
      'typescript basics':['typescript-basics'],'types and interfaces':['typescript-basics'],
      'async programming':['python-async'],'async/await and event loops':['python-async'],
      'password hashing':['security-passwords'],'jwt and sessions':['security-sessions'],
      'jwt and cookie sessions':['security-sessions'],'environment variables and secrets':['security-secrets'],
      'model monitoring and drift':['mlops-monitoring'],'docker':['deployment'],
      'docker containers':['deployment'],'cloud deployment':['deployment'],
    }
    if text in direct:return direct[text]
    if text=='git, security, testing, deployment':return ['git-basics','security-basics','testing-basics','deployment']
    return [module+'-'+slug(title)]

TOPIC_TITLES={
 'python-control-flow':'Conditions and loops','python-strings':'Strings','python-packages':'Packages and virtual environments',
 'python-exceptions':'Exceptions','python-async':'Async Python','ml-introduction':'Supervised and unsupervised learning',
 'git-basics':'Git and GitHub','security-basics':'Security fundamentals','testing-basics':'Testing fundamentals',
 'web-http':'HTTP and the web','web-client-server':'Client and server architecture','http-clients':'HTTP clients',
}
TOPIC_OWNER={'git-basics':'git','security-basics':'security','testing-basics':'testing','deployment':'engineering',
             'apis':'engineering','http-clients':'engineering','command-line':'git',
             'typescript-basics':'typescript','web-accessibility':'web'}
PREREQUISITES={
 'python-functions':['python-basics'],'python-collections':['python-basics'],'python-oop':['python-functions'],
 'python-packages':['python-basics'],'numpy':['python-collections'],'pandas':['numpy'],
 'linear-regression':['linear-algebra'],'feature-engineering':['ml-introduction'],
 'react-components':['javascript-functions'],'react-hooks':['react-components'],'apis':['python-functions'],
}

def build_track_catalog(modules,submodules):
    source=Path(__file__).with_name('catalog')/'role_tracks.txt'
    lines=[line.strip() for line in source.read_text(encoding='utf-8-sig').splitlines() if line.strip()]
    roles={rid:{'id':rid,'title':title,'description':f'Learning and interview preparation for {title}.','sections':[],'projects':[]} for title,rid in ROLE_NAMES.items()}
    topics={sid:{**entry,'difficulty':list(LEVEL_DESCRIPTIONS),'estimated_hours':None,'prerequisite_topic_ids':[],
                  'learning_objectives':[]} for sid,entry in submodules.items()}
    current=None;section=None;project_mode=False;links={};source_records=[]
    for line in lines:
        if line=='Suggested project ladder':project_mode=True;current=None;continue
        if line in ROLE_NAMES:current=roles[ROLE_NAMES[line]];section=None;continue
        if current is None:continue
        if project_mode:
            match=re.match(r'^(Beginner|Foundational|Intermediate|Advanced):\s*(.+)$',line)
            if match:current['projects'].append({'id':current['id']+'-'+match[1].lower(),'role_id':current['id'],
                'level':match[1].lower(),'title':match[2],'requirements':[],'evaluation_rubric':[], 'status':'planned'})
            continue
        match=re.match(r'^(\d{2})\.\s+(.+)$',line)
        if match:
            section={'id':current['id']+'-'+match[1],'title':match[2],'ordering':int(match[1]),'module_id':module_for_section(match[2]),'topic_ids':[],'source_topics':[]}
            current['sections'].append(section);continue
        if section is None:continue
        ids=topic_aliases(line,section['module_id'])
        section['source_topics'].append({'title':line,'topic_ids':ids})
        source_records.append({'role_id':current['id'],'section_id':section['id'],'title':line,'topic_ids':ids})
        for topic_id in ids:
            owner=topics[topic_id]['module_id'] if topic_id in topics else TOPIC_OWNER.get(topic_id,section['module_id'])
            if topic_id not in topics:
                topics[topic_id]={'id':topic_id,'title':TOPIC_TITLES.get(topic_id,line),'module_id':owner,'available':False,
                    'difficulty':list(LEVEL_DESCRIPTIONS),'estimated_hours':None,'prerequisite_topic_ids':[],'learning_objectives':[]}
            if line not in topics[topic_id]['learning_objectives']:topics[topic_id]['learning_objectives'].append(line)
            if topic_id not in section['topic_ids']:section['topic_ids'].append(topic_id)
            key=(current['id'],topic_id)
            link=links.setdefault(key,{'role_id':current['id'],'topic_id':topic_id,'importance':'core',
                'recommended_order':len([x for x in links if x[0]==current['id']])+1,'source_titles':[],'section_ids':[],
                'context':f'Apply this shared topic in {current["title"]} work.','source_kind':'supplied_catalog'})
            link['source_titles'].append(line)
            if section['id'] not in link['section_ids']:link['section_ids'].append(section['id'])
    for role in roles.values():
        if len(role['sections'])!=12 or len(role['projects'])!=4:raise ValueError('Incomplete supplied role catalog')
        for topic_id,owner in [('git-basics','git'),('security-basics','security'),('testing-basics','testing'),('deployment','engineering')]:
            topics.setdefault(topic_id,{'id':topic_id,'title':TOPIC_TITLES.get(topic_id,'Deployment'),'module_id':owner,'available':False,
                'difficulty':list(LEVEL_DESCRIPTIONS),'estimated_hours':None,'prerequisite_topic_ids':[],'learning_objectives':[TOPIC_TITLES.get(topic_id,'Deployment')]})
            links.setdefault((role['id'],topic_id),{'role_id':role['id'],'topic_id':topic_id,'importance':'supporting',
                'recommended_order':100,'source_titles':[],'section_ids':[],'context':f'Shared engineering foundation tailored to {role["title"]}.','source_kind':'supplied_cross_role_foundation'})
    module_index={m['id']:m for m in modules}
    for topic in topics.values():
        owner=topic['module_id']
        if owner not in module_index:
            m={'id':owner,'title':MODULE_TITLES.get(owner,owner.replace('-',' ').title()),'reason':'Shared curriculum subject used by the selected role track.', 'prerequisites':[],'submodules':[]}
            modules.append(m);module_index[owner]=m
        if topic['id'] not in {sid for sid,_,_ in module_index[owner]['submodules']}:
            module_index[owner]['submodules'].append((topic['id'],topic['title'],topic['available']))
        topic['prerequisite_topic_ids']=[p for p in PREREQUISITES.get(topic['id'],[]) if p in topics]
        if not topic['learning_objectives']:topic['learning_objectives']=[topic['title']]
    for m in modules:
        m['title']=MODULE_TITLES.get(m['id'],m['title'])
        if m['id']=='engineering':m['prerequisites']=[]
    submodules.update(topics)
    return {'version':'shared-curriculum-v1','roles':list(roles.values()),'topics':list(topics.values()),
            'role_topics':list(links.values()),'source_topics':source_records}
