from fastapi.testclient import TestClient
from app.main import create_app
from app.jobs import map_skill
from test_profile import PROFILE
from test_practice import result
import pytest
from app.jobs import ExtractedSkills,extract_skills

DESCRIPTION='Required: Python functions and NumPy. Preferred: QuantumFlux. You will build and evaluate production models.'
SKILLS=[{'name':'QuantumFlux','requirement':'preferred','evidence':'Preferred: QuantumFlux'},
        {'name':'NumPy','requirement':'required','evidence':'Python functions and NumPy'},
        {'name':'Python functions','requirement':'required','evidence':'Required: Python functions'}]

def test_analysis_requires_review_and_preserves_active_target_until_saved(tmp_path):
    url=f'sqlite:///{(tmp_path/"jobs.db").as_posix()}'
    with TestClient(create_app(url,job_extractor_fn=lambda d:{'skills':SKILLS})) as c:
        c.put('/api/v1/profile',json=PROFILE)
        draft=c.post('/api/v1/jobs/analyze',json={'title':'ML role','description':DESCRIPTION})
        assert draft.status_code==200
        assert c.get('/api/v1/curriculum').json()['job_plan'] is None
        saved=c.put(f'/api/v1/jobs/{draft.json()["id"]}/review',json={'skills':SKILLS})
        assert saved.status_code==200
        plan=c.get('/api/v1/curriculum').json()['job_plan']
        assert plan['counts']=={'available':1,'planned':1,'unmapped':1}
        statuses={x['name']:x['status'] for x in plan['items']}
        assert statuses['NumPy']=='planned' and statuses['QuantumFlux']=='unmapped'
        second=c.post('/api/v1/jobs/analyze',json={'title':'Another opportunity','description':DESCRIPTION}).json()
        assert c.get('/api/v1/jobs/current').json()['active']['id']==draft.json()['id']
        assert second['status']=='draft'
    with TestClient(create_app(url)) as c:
        assert c.get('/api/v1/curriculum').json()['job_plan']['title']=='ML role'
        assert c.get('/api/v1/jobs/current').json()['draft']['title']=='Another opportunity'

def test_unsupported_excerpts_and_duplicate_skills_are_rejected(tmp_path):
    url=f'sqlite:///{(tmp_path/"evidence.db").as_posix()}'
    with TestClient(create_app(url,job_extractor_fn=lambda d:{'skills':[{'name':'Python','requirement':'required','evidence':'Invented excerpt'}]})) as c:
        c.put('/api/v1/profile',json=PROFILE)
        assert c.post('/api/v1/jobs/analyze',json={'title':'Bad extraction','description':DESCRIPTION}).status_code==502
        assert c.get('/api/v1/jobs/current').json()['draft'] is None
    with TestClient(create_app(url,job_extractor_fn=lambda d:{'skills':SKILLS})) as c:
        draft=c.post('/api/v1/jobs/analyze',json={'title':'Review','description':DESCRIPTION}).json()
        path=f'/api/v1/jobs/{draft["id"]}/review'
        assert c.put(path,json={'skills':[dict(SKILLS[0],evidence='Not in the description')]}).status_code==422
        assert c.put(path,json={'skills':[SKILLS[0],dict(SKILLS[0],name='quantumflux')]}).status_code==422
        assert c.put(path,json={'skills':[]}).status_code==422
        assert c.get('/api/v1/curriculum').json()['job_plan'] is None

def test_review_can_be_corrected_and_role_defaults_restored_without_changing_history(tmp_path):
    url=f'sqlite:///{(tmp_path/"clear.db").as_posix()}'
    with TestClient(create_app(url,job_extractor_fn=lambda d:{'skills':SKILLS})) as c:
        c.put('/api/v1/profile',json=PROFILE)
        c.put('/api/v1/curriculum/python/level',json={'level':'beginner'})
        before=c.get('/api/v1/progress').json()
        draft=c.post('/api/v1/jobs/analyze',json={'title':'A role','description':DESCRIPTION}).json()
        edited=[dict(SKILLS[2],requirement='unspecified')]
        assert c.put(f'/api/v1/jobs/{draft["id"]}/review',json={'skills':edited}).status_code==200
        plan=c.get('/api/v1/curriculum').json()['job_plan']
        assert len(plan['items'])==1 and plan['items'][0]['level']=='beginner'
        assert c.post('/api/v1/jobs/clear').status_code==200
        assert c.get('/api/v1/curriculum').json()['job_plan'] is None
        assert c.get('/api/v1/profile').json()['experience']=='intermediate'
        assert c.get('/api/v1/progress').json()==before

def test_matching_weak_areas_raise_priority_within_requirement_group(tmp_path):
    url=f'sqlite:///{(tmp_path/"priority.db").as_posix()}'
    with TestClient(create_app(url,job_extractor_fn=lambda d:{'skills':SKILLS},evaluator_fn=lambda q,a:result(q,a,'partial'))) as c:
        c.put('/api/v1/profile',json=PROFILE)
        a=c.post('/api/v1/practice/start',json={'skill':'Closure binding'}).json()
        c.post(f'/api/v1/practice/{a["id"]}/submit',json={'answer':'My explanation.'})
        draft=c.post('/api/v1/jobs/analyze',json={'title':'A role','description':DESCRIPTION}).json()
        c.put(f'/api/v1/jobs/{draft["id"]}/review',json={'skills':SKILLS})
        first=c.get('/api/v1/curriculum').json()['job_plan']['items'][0]
        assert first['name']=='Python functions' and first['weak_areas']==['Closure binding']

def test_required_subject_adds_explicitly_labeled_prerequisites(tmp_path):
    url=f'sqlite:///{(tmp_path/"prerequisites.db").as_posix()}'
    description='Required: Machine learning. You will develop and evaluate predictive models for our product.'
    skills=[{'name':'Machine learning','requirement':'required','evidence':'Required: Machine learning'}]
    with TestClient(create_app(url,job_extractor_fn=lambda d:{'skills':skills})) as c:
        c.put('/api/v1/profile',json=PROFILE)
        draft=c.post('/api/v1/jobs/analyze',json={'title':'ML engineer','description':description}).json()
        c.put(f'/api/v1/jobs/{draft["id"]}/review',json={'skills':skills})
        modules={m['id']:m for m in c.get('/api/v1/curriculum').json()['modules']}
        assert modules['math']['recommendation_kind']=='prerequisite'
        assert modules['ml']['recommendation_kind']=='job_skill'
        assert modules['python']['suggested_order']<modules['ml']['suggested_order']
    assert map_skill('QuantumFlux')==(None,None)
    assert map_skill('scikit-learn')==('ml','feature-engineering')

def test_live_extractor_repairs_quotes_once_and_keeps_a_strict_bound(monkeypatch):
    from app import jobs
    invalid=ExtractedSkills.model_validate({'skills':[dict(SKILLS[1],evidence='Required: NumPy')]})
    valid=ExtractedSkills.model_validate({'skills':[SKILLS[1]]})
    calls=[]
    outputs=[invalid,valid]
    class FakeModel:
        def with_structured_output(self,*args,**kwargs):return self
        def invoke(self,messages):calls.append(messages);return outputs.pop(0)
    monkeypatch.setattr(jobs,'ChatOpenAI',lambda **kwargs:FakeModel())
    assert extract_skills(DESCRIPTION).skills[0].evidence in DESCRIPTION
    assert len(calls)==2
    calls.clear();outputs.extend([invalid,invalid])
    with pytest.raises(ValueError):extract_skills(DESCRIPTION)
    assert len(calls)==2
