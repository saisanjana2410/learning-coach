import json
import sqlite3
from fastapi.testclient import TestClient
from app.main import create_app
from app.curriculum import TRACK_CATALOG, SUBMODULES
from test_profile import PROFILE
from test_practice import result


def test_supplied_catalog_references_and_reuse():
    roles=TRACK_CATALOG['roles']
    assert len(roles)==5
    assert len(TRACK_CATALOG['source_topics'])==300
    assert all(len(r['sections'])==12 and len(r['projects'])==4 for r in roles)
    assert all(len(s['source_topics'])==5 for r in roles for s in r['sections'])
    links={(l['role_id'],l['topic_id']) for l in TRACK_CATALOG['role_topics']}
    for role in roles:
        for topic in ['git-basics','security-basics','testing-basics','deployment']:
            assert (role['id'],topic) in links
    for role in ['ai-engineer','python-developer','genai-engineer']:
        assert (role,'python-functions') in links and (role,'apis') in links
    assert ('mern-full-stack','python-functions') not in links
    for role in ['react-frontend','mern-full-stack']:
        assert (role,'react-components') in links
    def visit(topic,trail):
        assert topic not in trail
        for parent in SUBMODULES[topic]['prerequisite_topic_ids']:
            visit(parent,trail|{topic})
    for topic in SUBMODULES:visit(topic,set())


def topic(c,sid):
    return next(s for m in c.get('/api/v1/curriculum').json()['modules'] for s in m['submodules'] if s['id']==sid)


def test_topic_preferences_inherit_override_reset_and_foundational(tmp_path):
    with TestClient(create_app(f'sqlite:///{tmp_path.as_posix()}/prefs.db')) as c:
        c.put('/api/v1/profile',json=PROFILE)
        c.put('/api/v1/curriculum/python/level',json={'level':'advanced'})
        assert topic(c,'python-functions')['level']=='advanced'
        endpoint='/api/v1/curriculum/topics/python-functions/level'
        assert c.put(endpoint,json={'level':'beginner'}).status_code==200
        assert topic(c,'python-functions')['level']=='beginner'
        assert topic(c,'python-collections')['level']=='advanced'
        c.put(endpoint,json={'level':None})
        assert topic(c,'python-functions')['level_source']=='module'
        c.put(endpoint,json={'level':'foundational'})
        assert topic(c,'python-functions')['status']=='planned'
        assert c.post('/api/v1/runs/start',json={'topic_id':'python-functions'}).status_code==422
        assert c.get('/api/v1/runs/current').json() is None
        assert c.get('/api/v1/lessons?submodule_id=python-functions&level=foundational').json()==[]


def test_catalog_seed_is_idempotent_and_preserves_accepted_evidence(tmp_path):
    path=tmp_path/'migration.db';url=f'sqlite:///{path.as_posix()}'
    with TestClient(create_app(url,evaluator_fn=lambda q,a:result(q,a))) as c:
        c.put('/api/v1/profile',json=PROFILE)
        c.put('/api/v1/curriculum/topics/python-functions/level',json={'level':'beginner'})
        run=c.post('/api/v1/runs/start',json={'topic_id':'python-functions'}).json()
        aid=run['attempt']['id']
        c.post(f'/api/v1/practice/{aid}/submit',json={'answer':'It returns the value to its caller.'})
        c.post(f'/api/v1/runs/{run["run"]["id"]}/finish')
        before=c.get('/api/v1/progress').json()
    with sqlite3.connect(path) as db:
        evidence=db.execute('select question_json,answer,feedback_json from practice_attempts where id=?',(aid,)).fetchone()
        assert evidence[2]
    with TestClient(create_app(url)) as c:
        assert c.get('/api/v1/progress').json()==before
        assert topic(c,'python-functions')['level']=='beginner'
        updated=c.put('/api/v1/curriculum/role',json={'role_id':'python-developer'}).json()
        assert updated['track']['title']=='Python Developer'
    with sqlite3.connect(path) as db:
        assert db.execute('select count(*) from catalog_roles').fetchone()[0]==5
        assert db.execute('select count(*) from schema_migrations').fetchone()[0]==1
        assert db.execute('select count(*) from catalog_projects').fetchone()[0]==20
        assert db.execute('select question_json,answer,feedback_json from practice_attempts where id=?',(aid,)).fetchone()==evidence


def test_role_run_freezes_topic_preferences(tmp_path):
    with TestClient(create_app(f'sqlite:///{tmp_path.as_posix()}/run.db',evaluator_fn=lambda q,a:result(q,a))) as c:
        c.put('/api/v1/profile',json={**PROFILE,'experience':'foundational'})
        endpoint='/api/v1/curriculum/topics/python-functions/level'
        c.put(endpoint,json={'level':'beginner'})
        run=c.post('/api/v1/runs/start',json={'scope':'role','mode':'interview','skill':'Return values'}).json()
        c.put(endpoint,json={'level':'advanced'})
        c.post(f'/api/v1/practice/{run["attempt"]["id"]}/submit',json={'answer':'Returns a value.'})
        following=c.post(f'/api/v1/runs/{run["run"]["id"]}/next',json={'skill':'Return values','mode':'interview'}).json()
        assert following['attempt']['question']['level']=='beginner'


def test_planned_frontend_track_does_not_ask_unrelated_ml_questions(tmp_path):
    with TestClient(create_app(f'sqlite:///{tmp_path.as_posix()}/frontend.db')) as c:
        c.put('/api/v1/profile',json=PROFILE)
        c.put('/api/v1/curriculum/role',json={'role_id':'react-frontend'})
        response=c.post('/api/v1/runs/start',json={'scope':'role','mode':'interview'})
        assert response.status_code==422
        assert c.get('/api/v1/runs/current').json() is None
