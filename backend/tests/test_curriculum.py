from fastapi.testclient import TestClient
from app.main import create_app
from app.curriculum import QUESTIONS, LESSONS, SUBMODULES
from test_profile import PROFILE
from test_practice import result

def test_module_levels_persist_independently_and_change_content(tmp_path):
    url=f'sqlite:///{(tmp_path/"catalog.db").as_posix()}'
    with TestClient(create_app(url)) as c:
        c.put('/api/v1/profile',json=PROFILE)
        catalog=c.get('/api/v1/curriculum').json()
        assert catalog['recommendation_source'].startswith('Curated role template')
        assert {'python','ml','math','ai'} <= {m['id'] for m in catalog['modules']}
        assert c.put('/api/v1/curriculum/python/level',json={'level':'beginner'}).status_code==200
        assert c.put('/api/v1/curriculum/ml/level',json={'level':'advanced'}).status_code==200
        beginner=c.get('/api/v1/lessons?submodule_id=python-functions&level=beginner').json()
        advanced=c.get('/api/v1/lessons?submodule_id=python-functions&level=advanced').json()
        assert beginner[0]['skill']=='Return values' and advanced[0]['skill']=='Closure binding'
        assert c.put('/api/v1/curriculum/python/level',json={'level':'expert'}).status_code==422
        assert c.put('/api/v1/curriculum/unknown/level',json={'level':'beginner'}).status_code==404
    with TestClient(create_app(url)) as c:
        levels={m['id']:m['level'] for m in c.get('/api/v1/curriculum').json()['modules']}
        assert levels['python']=='beginner' and levels['ml']=='advanced'

def test_practice_uses_level_snapshot_and_stays_in_submodule(tmp_path):
    url=f'sqlite:///{(tmp_path/"difficulty.db").as_posix()}'
    with TestClient(create_app(url,evaluator_fn=lambda q,a:result(q,a))) as c:
        c.put('/api/v1/profile',json=PROFILE)
        c.put('/api/v1/curriculum/python/level',json={'level':'beginner'})
        run=c.post('/api/v1/runs/start',json={'topic_id':'python-functions'}).json()
        assert run['attempt']['question']['level']=='beginner'
        c.put('/api/v1/curriculum/python/level',json={'level':'advanced'})
        aid=run['attempt']['id'];rid=run['run']['id']
        c.post(f'/api/v1/practice/{aid}/submit',json={'answer':'The result is returned to the caller.'})
        follow=c.post(f'/api/v1/runs/{rid}/next',json={'mode':'applied'}).json()
        assert follow['attempt']['question']['level']=='beginner'
        assert follow['attempt']['question']['submodule_id']=='python-functions'
        assert follow['attempt']['question']['id']!=run['attempt']['question']['id']
        c.post(f'/api/v1/runs/{rid}/finish')
        fresh=c.post('/api/v1/runs/start',json={'topic_id':'python-functions'}).json()
        assert fresh['attempt']['question']['level']=='advanced'

def test_curriculum_references_and_practice_coverage():
    ids={l['id'] for l in LESSONS}
    assert len(ids)==len(LESSONS)
    assert len({q['id'] for q in QUESTIONS})==len(QUESTIONS)
    for sid,submodule in SUBMODULES.items():
        if not submodule['available']:continue
        for level in ('beginner','intermediate','advanced'):
            questions=[q for q in QUESTIONS if q['submodule_id']==sid and q['level']==level]
            assert len(questions)>=2,(sid,level)
            assert any(l['submodule_id']==sid and l['level']==level for l in LESSONS)
            assert all(q['lesson_id'] in ids for q in questions)

def test_role_questions_honor_each_module_level_and_planned_content_is_blocked(tmp_path):
    url=f'sqlite:///{(tmp_path/"scope.db").as_posix()}'
    with TestClient(create_app(url)) as c:
        c.put('/api/v1/profile',json=PROFILE)
        c.put('/api/v1/curriculum/python/level',json={'level':'beginner'})
        c.put('/api/v1/curriculum/ml/level',json={'level':'advanced'})
        assert c.post('/api/v1/runs/start',json={'topic_id':'numpy'}).status_code==422
        role=c.post('/api/v1/runs/start',json={'scope':'role','mode':'interview','skill':'Return values'}).json()
        assert role['attempt']['question']['module_id']=='python'
        assert role['attempt']['question']['level']=='beginner'

def test_similar_skill_labels_do_not_merge_different_submodule_evidence(tmp_path):
    url=f'sqlite:///{(tmp_path/"evidence.db").as_posix()}'
    def evaluate(q,a):return result(q,a,'partial' if q['id']=='python-mutable' else 'met')
    with TestClient(create_app(url,evaluator_fn=evaluate)) as c:
        c.put('/api/v1/profile',json=PROFILE)
        for _ in range(2):
            a=c.post('/api/v1/practice/start',json={'skill':'Python data handling'}).json()
            assert c.post(f'/api/v1/practice/{a["id"]}/submit',json={'answer':'My explanation.'}).status_code==200
        progress=c.get('/api/v1/progress').json()
        assert len(progress['skills'])==2
        assert progress['weak_areas'][0]['submodule_id']=='python-functions'
        assert any(s['submodule_id']=='python-collections' and s['score']==100 for s in progress['skills'])
