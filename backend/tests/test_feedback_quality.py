import json
from pathlib import Path
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.main import create_app
from app.feedback_flags import FeedbackFlag
from test_profile import PROFILE
from test_practice import result

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'evals'))
from run_feedback_eval import load_cases,evaluate_case,metrics
from app.assessment import Evaluation
from app.curriculum import QUESTIONS

def test_feedback_flag_is_persistent_idempotent_and_does_not_regrade(tmp_path):
    url=f'sqlite:///{(tmp_path/"flags.db").as_posix()}'
    with TestClient(create_app(url,evaluator_fn=lambda q,a:result(q,a,'partial'))) as c:
        c.put('/api/v1/profile',json=PROFILE)
        attempt=c.post('/api/v1/practice/start',json={}).json();aid=attempt['id']
        path=f'/api/v1/practice/{aid}/flag'
        assert c.put(path,json={'reason':'incorrect_score','note':'Check my answer.'}).status_code==409
        c.post(f'/api/v1/practice/{aid}/submit',json={'answer':'My explanation.'})
        before=c.get('/api/v1/progress').json()
        payload={'reason':'incorrect_score','note':'The rubric missed my explanation.'}
        assert c.put(path,json=payload).status_code==200
        assert c.put(path,json=payload).status_code==200
        assert len(c.get('/api/v1/feedback/flags').json())==1
        assert c.get('/api/v1/progress').json()==before
        assert c.put(path,json={'reason':'unknown'}).status_code==422
        assert c.put(path,json={'reason':'other','note':'x'*2001}).status_code==422
    with TestClient(create_app(url)) as c:
        flag=c.get(path).json()
        assert flag['note']==payload['note'] and flag['original_score']==50
        assert c.put(path,json={'reason':'missing_context','note':'Updated report'}).status_code==200
    with Session(create_engine(url)) as db:
        snapshot=json.loads(db.get(FeedbackFlag,aid).snapshot_json)
        assert snapshot['answer']=='My explanation.'
        assert snapshot['feedback']['score']==50

def test_quality_fixtures_cover_cases_and_validate_evidence_without_database():
    dataset=load_cases(ROOT/'evals'/'feedback_cases.json')
    assert len(dataset['cases'])==20
    assert {c['category'] for c in dataset['cases']}=={'correct','equivalent','partial','incorrect','ambiguous'}
    case=dataset['cases'][0]
    def evaluator(q,a):return result(q,a)
    output=evaluate_case(case,1,evaluator)
    assert output['valid'] and output['score']==100
    def invented(q,a):
        value=result(q,a);value['criteria'][0]['evidence']='not present in the supplied answer';return value
    invalid=evaluate_case(case,2,invented)
    assert not invalid['valid']
    report=metrics([output,invalid])
    assert report['criterion_agreement']==.5
    assert report['score_agreement']==.5
    assert report['repeat_consistency']==0

def test_equivalent_answer_metric_detects_different_judgments():
    dataset=load_cases(ROOT/'evals'/'feedback_cases.json')
    one=evaluate_case(dataset['cases'][0],1,lambda q,a:result(q,a))
    two=evaluate_case(dataset['cases'][1],1,lambda q,a:result(q,a,'partial'))
    assert metrics([one,two])['equivalent_answer_consistency']==0

def test_evaluator_has_one_bounded_validation_correction(monkeypatch):
    from app import assessment
    q=QUESTIONS[0];answer='An answer containing evidence.'
    correct=Evaluation.model_validate(result(q,answer))
    invalid=Evaluation.model_validate(result(q,'invented quotation'))
    outputs=[invalid,correct];calls=[]
    class FakeModel:
        def with_structured_output(self,*args,**kwargs):return self
        def invoke(self,messages):calls.append(messages);return outputs.pop(0)
    monkeypatch.setattr(assessment,'ChatOpenAI',lambda **kwargs:FakeModel())
    assert assessment.evaluate_answer(q,answer)==correct
    assert len(calls)==2
    calls.clear();outputs.extend([invalid,invalid])
    with pytest.raises(ValueError):assessment.evaluate_answer(q,answer)
    assert len(calls)==2

def test_attempt_preserves_the_catalog_rubric_version(tmp_path):
    url=f'sqlite:///{(tmp_path/"versions.db").as_posix()}'
    with TestClient(create_app(url,evaluator_fn=lambda q,a:result(q,a))) as c:
        c.put('/api/v1/profile',json=PROFILE)
        a=c.post('/api/v1/practice/start',json={'skill':'Understand residuals'}).json()
        feedback=c.post(f'/api/v1/practice/{a["id"]}/submit',json={'answer':'Three minutes; underpredicted.'}).json()['feedback']
        assert feedback['rubric_version']==2
