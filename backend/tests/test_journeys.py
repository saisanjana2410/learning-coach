from fastapi.testclient import TestClient
from app.main import create_app
from test_profile import PROFILE
from test_practice import result

def test_continuous_topic_run_survives_refresh_and_finishes_with_summary(tmp_path):
    url=f'sqlite:///{(tmp_path/"runs.db").as_posix()}'
    def evaluate(q,a):return result(q,a)
    with TestClient(create_app(url,evaluator_fn=evaluate)) as c:
        c.put('/api/v1/profile',json=PROFILE)
        first=c.post('/api/v1/runs/start',json={}).json()
        run_id=first['run']['id']; a=first['attempt']
        assert c.post(f'/api/v1/runs/{run_id}/next',json={}).status_code==409
        c.post(f'/api/v1/practice/{a["id"]}/submit',json={'answer':'Evidence of understanding.'})
    with TestClient(create_app(url,evaluator_fn=evaluate)) as c:
        restored=c.get('/api/v1/runs/current').json()
        assert restored['attempt']['feedback']['score']==100
        second=c.post(f'/api/v1/runs/{run_id}/next',json={'mode':'applied'}).json()
        assert second['attempt']['mode']=='applied'
        assert second['attempt']['id']!=a['id']
        assert second['attempt']['question']['skill'] in ['Interpret coefficients','Make predictions','Understand residuals','Measure prediction error','Evaluate on unseen data']
        summary=c.post(f'/api/v1/runs/{run_id}/finish').json()['summary']
        assert summary['answered']==1 and summary['skipped']==1
        assert len(summary['reviews'])==1
        assert c.post(f'/api/v1/runs/{run_id}/finish').json()['summary']==summary
        assert c.get('/api/v1/runs/current').json() is None
        assert len(c.get('/api/v1/runs/history').json())==1

def test_question_help_is_scoped_persistent_and_does_not_change_score(tmp_path):
    contexts=[]
    def help_reply(q,a,f,m):contexts.append((q,a,f,m));return 'Use the slope units to interpret your answer.'
    url=f'sqlite:///{(tmp_path/"help.db").as_posix()}'
    with TestClient(create_app(url,evaluator_fn=lambda q,a:result(q,a,'partial'),help_fn=help_reply)) as c:
        c.put('/api/v1/profile',json=PROFILE)
        run=c.post('/api/v1/runs/start',json={}).json();a=run['attempt']; aid=a['id']
        assert c.post(f'/api/v1/practice/{aid}/help',json={'client_message_id':'h','text':'Help'}).status_code==409
        c.post(f'/api/v1/practice/{aid}/submit',json={'answer':'My specific answer.'})
        before=c.get('/api/v1/progress').json()
        msg={'client_message_id':'help-one','text':'Why are the units important?'}
        response=c.post(f'/api/v1/practice/{aid}/help',json=msg)
        assert response.status_code==200
        assert len(c.post(f'/api/v1/practice/{aid}/help',json=msg).json()['messages'])==2
        assert len(contexts)==1 and contexts[0][1]=='My specific answer.'
        assert c.get('/api/v1/progress').json()==before
        next_a=c.post(f'/api/v1/runs/{run["run"]["id"]}/next',json={}).json()['attempt']
        assert c.get(f'/api/v1/practice/{next_a["id"]}/help').json()['messages']==[]
    with TestClient(create_app(url,help_fn=help_reply)) as c:
        assert len(c.get(f'/api/v1/practice/{aid}/help').json()['messages'])==2

def test_role_run_can_cover_other_domains_and_topic_scope_rejects_them(tmp_path):
    url=f'sqlite:///{(tmp_path/"role.db").as_posix()}'
    with TestClient(create_app(url,evaluator_fn=lambda q,a:result(q,a))) as c:
        c.put('/api/v1/profile',json=PROFILE)
        response=c.post('/api/v1/runs/start',json={'scope':'topic','skill':'SQL aggregation'})
        assert response.status_code==422
        assert c.get('/api/v1/runs/current').json() is None
        run=c.post('/api/v1/runs/start',json={'scope':'role','mode':'interview','skill':'SQL aggregation'}).json()
        assert run['attempt']['question']['skill']=='SQL aggregation'
        assert run['run']['role']=='AI/ML Engineer'
        assert c.post('/api/v1/runs/start',json={}).status_code==409
        assert 'reference' not in str(run['attempt']['question'])

def test_failed_help_retry_keeps_the_same_question_context(tmp_path):
    count=0
    def helper(q,a,f,m):
        nonlocal count
        count+=1
        if count==1:raise ValueError('provider detail')
        return 'Here is another explanation.'
    url=f'sqlite:///{(tmp_path/"retry.db").as_posix()}'
    with TestClient(create_app(url,evaluator_fn=lambda q,a:result(q,a),help_fn=helper)) as c:
        c.put('/api/v1/profile',json=PROFILE)
        run=c.post('/api/v1/runs/start',json={}).json();aid=run['attempt']['id']
        c.post(f'/api/v1/practice/{aid}/submit',json={'answer':'My answer.'})
        msg={'client_message_id':'help','text':'Explain this again.'};path=f'/api/v1/practice/{aid}/help'
        failed=c.post(path,json=msg)
        assert failed.status_code==502 and 'provider detail' not in failed.text
        assert len(c.get(path).json()['messages'])==1
        assert len(c.post(path,json=msg).json()['messages'])==2
