from datetime import datetime, timedelta, timezone
import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.main import create_app
from app.practice import Attempt, summarize
from app.assessment import Evaluation, validate_evaluation, score
from app.questions import QUESTIONS
from test_profile import PROFILE
import pytest

def result(question, answer, grade='met'):
    return {'criteria':[{'id':c,'result':grade,'evidence':answer,'explanation':'Checks the stated concept.'} for c in question['criteria']],
            'strengths':'Identifies the concept.' if grade=='met' else 'Attempted the question.',
            'gap':'' if grade=='met' else 'Revisit units and interpretation.', 'next_step':'Try a fresh example.'}

def test_feedback_retry_persistence_and_hidden_rubric(tmp_path):
    calls=[]
    def evaluate(q,a): calls.append(a); return result(q,a,'partial')
    url=f'sqlite:///{(tmp_path/"practice.db").as_posix()}'
    with TestClient(create_app(url,evaluator_fn=evaluate)) as c:
        c.put('/api/v1/profile',json=PROFILE)
        attempt=c.post('/api/v1/practice/start',json={'skill':'Interpret coefficients'}).json()
        assert 'reference' not in json.dumps(attempt) and 'criteria' not in json.dumps(attempt)
        path=f'/api/v1/practice/{attempt["id"]}/submit'
        feedback=c.post(path,json={'answer':'The prediction increases.'})
        assert feedback.status_code==200
        assert feedback.json()['feedback']['score']==50
        assert c.post(path,json={'answer':'The prediction increases.'}).status_code==200
        assert len(calls)==1
        assert c.post(path,json={'answer':'Changed answer'}).status_code==409
    with TestClient(create_app(url,evaluator_fn=evaluate)) as c:
        progress=c.get('/api/v1/progress').json()
        assert progress['assessed_skills']==1
        assert progress['weak_areas'][0]['dimension']=='Conceptual understanding'
        due=datetime.fromisoformat(progress['upcoming_reviews'][0]['due_at'])
        assert timedelta(days=1,hours=23)<due-datetime.now(timezone.utc)<timedelta(days=2,seconds=5)
        assert len(progress['recent_attempts'])==1
        interview=c.post('/api/v1/practice/start',json={'mode':'interview'}).json()
        assert interview['question']['skill']=='Interpret coefficients'

def test_invalid_assessment_does_not_change_progress_and_can_retry(tmp_path):
    calls=0
    def evaluate(q,a):
        nonlocal calls
        calls+=1
        if calls==1:
            value=result(q,a); value['criteria'][0]['evidence']='invented quotation'; return value
        return result(q,a)
    url=f'sqlite:///{(tmp_path/"failure.db").as_posix()}'
    with TestClient(create_app(url,evaluator_fn=evaluate)) as c:
        c.put('/api/v1/profile',json=PROFILE)
        a=c.post('/api/v1/practice/start',json={}).json(); path=f'/api/v1/practice/{a["id"]}/submit'
        assert c.post(path,json={'answer':'Two minutes per kilometer.'}).status_code==502
        assert c.get('/api/v1/progress').json()['assessed_skills']==0
        assert c.get('/api/v1/practice/current').json()['answer']=='Two minutes per kilometer.'
        assert c.post(path,json={'answer':'Two minutes per kilometer.'}).status_code==200

def test_delayed_fresh_evidence_required_and_gap_resets_status(tmp_path):
    url=f'sqlite:///{(tmp_path/"rules.db").as_posix()}'
    with TestClient(create_app(url)): pass
    engine=create_engine(url); now=datetime.now(timezone.utc)
    with Session(engine) as db:
        def add(q,days,grade='met'):
            feedback=result(q,'evidence',grade)
            feedback['score']=100 if grade=='met' else 0
            db.add(Attempt(id=str(days)+q['id'],created_at=(now-timedelta(days=days)).isoformat(),assessed_at=(now-timedelta(days=days)).isoformat(),mode='concept',question_json=json.dumps(q),answer='evidence',feedback_json=json.dumps(feedback),status='accepted'))
            db.commit()
        add(QUESTIONS[0],5)
        assert summarize(db,now)['skills'][0]['status']=='learning'
        add(QUESTIONS[1],0)
        assert summarize(db,now)['skills'][0]['status']=='demonstrated_proficiency'
        add(QUESTIONS[0],-1,'not_met')
        assert summarize(db,now+timedelta(days=2))['skills'][0]['status']=='needs_review'
        add(QUESTIONS[1],-2)
        assert summarize(db,now+timedelta(days=2))['skills'][0]['status']=='learning'

def test_uncertain_and_missing_criteria_not_treated_as_mastery():
    q=QUESTIONS[0]
    uncertain=Evaluation.model_validate(result(q,'unclear','insufficient_evidence'))
    assert score(uncertain) is None
    value=result(q,'answer'); value['criteria']=value['criteria'][:1]
    with pytest.raises(ValueError):validate_evaluation(value,q,'answer')
