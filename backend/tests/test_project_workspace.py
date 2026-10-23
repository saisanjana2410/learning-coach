import json
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from app.main import create_app
from test_profile import PROFILE
from test_practice import result


def begin(c,level='beginner'):
    c.put('/api/v1/profile',json=PROFILE)
    response=c.post('/api/v1/projects/delivery-time/start',json={'level':level})
    assert response.status_code==200
    return response.json()

def endpoint(data,milestone='data',action='submit'):
    return f'/api/v1/projects/delivery-time/{data["workspace"]["id"]}/milestones/{milestone}/{action}'

def test_draft_resume_version_conflict_and_level_isolation(tmp_path):
    url=f'sqlite:///{tmp_path.as_posix()}/draft.db'
    with TestClient(create_app(url)) as c:
        assert c.get('/api/v1/projects/delivery-time').json()['workspace'] is None
        data=begin(c)
        saved=c.put(endpoint(data,'training','draft'),json={'text':'My pipeline draft','version':0}).json()
        assert saved['workspace']['resume_milestone_id']=='training'
        assert saved['milestones'][2]['draft_version']==1
        assert c.put(endpoint(data,'training','draft'),json={'text':'Stale replacement','version':0}).status_code==409
        second=begin(c,'advanced')
        assert second['workspace']['id']!=data['workspace']['id']
        assert second['milestones'][2]['draft']==''
        original=c.get(f'/api/v1/projects/delivery-time/workspaces/{data["workspace"]["id"]}').json()
        assert original['workspace']['level']=='beginner'
        assert original['milestones'][2]['draft']=='My pipeline draft'
        restored=begin(c)
        assert restored['milestones'][2]['draft']=='My pipeline draft'
        assert c.get('/api/v1/progress').json()['assessed_skills']==0
    with TestClient(create_app(url)) as c:
        restored=c.get('/api/v1/projects/delivery-time').json()
        assert restored['workspace']['resume_milestone_id']=='training'
        assert restored['milestones'][2]['draft']=='My pipeline draft'


def test_accepted_evidence_is_idempotent_and_weak_areas_link_to_real_lessons(tmp_path):
    calls=[]
    def evaluate(q,a):calls.append(a);return result(q,a,'partial' if a=='Initial work' else 'met')
    with TestClient(create_app(f'sqlite:///{tmp_path.as_posix()}/feedback.db',evaluator_fn=evaluate)) as c:
        data=begin(c,'intermediate')
        path=endpoint(data)
        body={'submission_id':'first','answer':'Initial work'}
        assessed=c.post(path,json=body).json()
        milestone=assessed['milestones'][0]
        assert milestone['status']=='needs_revision'
        assert milestone['latest_feedback']['feedback']['score']==50
        assert c.post(path,json=body).status_code==200 and len(calls)==1
        assert c.post(path,json={'submission_id':'duplicate','answer':body['answer']}).status_code==409
        assert len(calls)==1
        assert c.post(path,json={**body,'answer':'Changed work'}).status_code==409
        weak=c.get('/api/v1/progress').json()['weak_areas'][0]
        assert weak['submodule_id']=='python-for-ml' and weak['level']=='intermediate'
        assert c.get(f'/api/v1/lessons?submodule_id={weak["submodule_id"]}&level={weak["level"]}').json()
        revised=c.post(path,json={'submission_id':'second','answer':'Revised implementation'}).json()
        assert revised['milestones'][0]['status']=='requirements_met'
        assert revised['workspace']['completed']==1
        history=revised['milestones'][0]['history']
        assert len(history)==2
        assert history[-1]['attempt']['answer']=='Initial work'
        assert history[-1]['attempt']['feedback']['score']==50
        assert c.get('/api/v1/progress').json()['weak_areas']==[]
        assert c.get('/api/v1/practice/current').json() is None


def test_failed_feedback_preserves_answer_retries_and_does_not_block_practice(tmp_path):
    calls=[]
    def evaluate(q,a):
        calls.append(a)
        if len(calls)==1:raise RuntimeError('temporary provider failure')
        return result(q,a)
    with TestClient(create_app(f'sqlite:///{tmp_path.as_posix()}/retry.db',evaluator_fn=evaluate)) as c:
        data=begin(c)
        path=endpoint(data)
        body={'submission_id':'retry','answer':'Saved project work'}
        assert c.post(path,json=body).status_code==502
        restored=c.get('/api/v1/projects/delivery-time').json()
        assert restored['milestones'][0]['pending_submission']['attempt']['answer']=='Saved project work'
        assert restored['milestones'][0]['status']=='retry_required'
        assert c.get('/api/v1/progress').json()['assessed_skills']==0
        assert c.post(path,json={'submission_id':'another','answer':'Different work'}).status_code==409
        assert c.post('/api/v1/runs/start',json={'topic_id':'python-for-ml'}).status_code==200
        retried=c.post(path,json=body).json()
        assert retried['milestones'][0]['pending_submission'] is None
        assert retried['milestones'][0]['status']=='requirements_met'
        assert calls==['Saved project work','Saved project work']


def test_cancel_pending_keeps_history_and_allows_new_submission(tmp_path):
    def failing(q,a):raise RuntimeError('temporary')
    with TestClient(create_app(f'sqlite:///{tmp_path.as_posix()}/cancel.db',evaluator_fn=failing)) as c:
        data=begin(c)
        c.post(endpoint(data),json={'submission_id':'old','answer':'Keep this historical answer'})
        saved=c.get('/api/v1/projects/delivery-time').json()
        attempt=saved['milestones'][0]['pending_submission']['attempt']
        assert c.post(f'/api/v1/practice/{attempt["id"]}/discard').status_code==200
        saved=c.get('/api/v1/projects/delivery-time').json()
        assert saved['milestones'][0]['pending_submission'] is None
        assert saved['milestones'][0]['history'][0]['attempt']['answer']=='Keep this historical answer'
        assert c.post(endpoint(data),json={'submission_id':'new','answer':'Revised saved work'}).status_code==502


def test_insufficient_evidence_does_not_complete_a_milestone(tmp_path):
    with TestClient(create_app(f'sqlite:///{tmp_path.as_posix()}/uncertain.db',evaluator_fn=lambda q,a:result(q,a,'insufficient_evidence'))) as c:
        data=begin(c)
        assessed=c.post(endpoint(data),json={'submission_id':'uncertain','answer':'I am not sure'}).json()
        assert assessed['workspace']['completed']==0
        assert assessed['milestones'][0]['latest_feedback']['feedback']['score'] is None
        assert c.get('/api/v1/progress').json()['assessed_skills']==0


def test_all_milestones_complete_only_after_accepted_feedback(tmp_path):
    with TestClient(create_app(f'sqlite:///{tmp_path.as_posix()}/all.db',evaluator_fn=lambda q,a:result(q,a))) as c:
        data=begin(c,'advanced')
        assert data['workspace']['completed']==0
        for m in data['milestones']:
            assert len(m['rubric'])==3
            response=c.post(endpoint(data,m['id']),json={'submission_id':'step-'+m['id'],'answer':'My implementation and release evidence'})
            assert response.status_code==200
        complete=c.get('/api/v1/projects/delivery-time').json()
        assert complete['workspace']['completed']==6
        assert complete['workspace']['status']=='requirements_met'
        assert all(m['status']=='requirements_met' for m in complete['milestones'])
        assert c.post(endpoint(data,'unknown'),json={'submission_id':'bad','answer':'No milestone'}).status_code==404
