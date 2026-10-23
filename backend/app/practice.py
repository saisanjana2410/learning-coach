"""Persistent assessments and revision summaries for the local learner."""
import json
import os
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Literal
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import String, Text, select
from sqlalchemy.orm import Mapped, mapped_column
from .main import Base, Learner, SKILLS
from .questions import QUESTIONS, public_question
from .assessment import evaluate_answer, validate_evaluation, score, EVALUATOR_PROMPT_VERSION

class Attempt(Base):
    __tablename__='practice_attempts'
    id: Mapped[str] = mapped_column(String(36),primary_key=True)
    created_at: Mapped[str] = mapped_column(String(40))
    assessed_at: Mapped[str | None] = mapped_column(String(40),nullable=True)
    mode: Mapped[str] = mapped_column(String(20))
    question_json: Mapped[str] = mapped_column(Text)
    answer: Mapped[str | None] = mapped_column(Text,nullable=True)
    feedback_json: Mapped[str | None] = mapped_column(Text,nullable=True)
    status: Mapped[str] = mapped_column(String(20),default='awaiting_answer')
    model: Mapped[str | None] = mapped_column(String(100),nullable=True)

class Start(BaseModel):
    mode: Literal['concept','applied','interview'] = 'concept'
    skill: str | None = None
    run_id: str | None = None

class Submission(BaseModel):
    answer: str = Field(min_length=1,max_length=6000)
    @field_validator('answer')
    @classmethod
    def not_blank(cls,value):
        if not value.strip(): raise ValueError('Write an answer first')
        return value.strip()

def serialize(row):
    question=json.loads(row.question_json)
    return {'id':row.id,'mode':row.mode,'status':row.status,'question':public_question(question),
            'answer':row.answer,'feedback':json.loads(row.feedback_json) if row.feedback_json else None,
            'created_at':row.created_at,'assessed_at':row.assessed_at}

def summarize(db, now=None):
    now=now or datetime.now(timezone.utc)
    rows=list(db.scalars(select(Attempt).where(Attempt.status=='accepted').order_by(Attempt.assessed_at)))
    dimensions={'concept':'Conceptual understanding','applied':'Practical application','interview':'Interview explanation'}
    progress=[]
    question_index={q['id']:q for q in QUESTIONS}
    groups={}
    for row in rows:
        q=json.loads(row.question_json)
        if json.loads(row.feedback_json)['score'] is None:continue
        metadata={**question_index.get(q['id'],{}),**q}
        identity=(q['skill'],row.mode,metadata.get('module_id'),metadata.get('submodule_id'),metadata.get('level'))
        groups.setdefault(identity,[]).append(row)
    for (skill,mode,module_id,submodule_id,level),evidence in groups.items():
        dimension=dimensions[mode]
        latest=evidence[-1]; feedback=json.loads(latest.feedback_json); points=feedback['score']
        # A different question after a delay provides stronger retention evidence.
        last_gap=max((i for i,r in enumerate(evidence[:-1]) if json.loads(r.feedback_json)['score']<100),default=-1)
        independent=[r for r in evidence[last_gap+1:-1] if json.loads(r.feedback_json)['score']==100
                     and json.loads(r.question_json)['id']!=json.loads(latest.question_json)['id']
                     and datetime.fromisoformat(latest.assessed_at)-datetime.fromisoformat(r.assessed_at)>=timedelta(days=4)]
        proficient=points==100 and bool(independent)
        interval=1 if points<50 else 2 if points<100 else 8 if proficient else 4
        due=datetime.fromisoformat(latest.assessed_at)+timedelta(days=interval)
        stored_question=json.loads(latest.question_json)
        metadata={**question_index.get(stored_question['id'],{}),**stored_question}
        progress.append({'skill':skill,'mode':mode,'dimension':dimension,'status':'demonstrated_proficiency' if proficient else 'needs_review' if points<100 else 'learning',
            'score':points,'evidence_count':len(evidence),'gap':feedback['gap'] if points<100 else '',
            'next_step':feedback['next_step'],'due_at':due.isoformat(),'due':due<=now,
            'reason':f'{points}% on the latest {mode} answer; review after {interval} days.',
            'module_id':metadata.get('module_id'),'submodule_id':metadata.get('submodule_id'),'level':metadata.get('level'),
            'lesson_id':json.loads(latest.question_json)['lesson_id']})
    return {'skills':progress,'assessed_skills':len({p['skill'] for p in progress}),
            'weak_areas':[p for p in progress if p['status']=='needs_review'],
            'due_reviews':sorted([p for p in progress if p['due']],key=lambda p:p['due_at']),
            'upcoming_reviews':sorted(progress,key=lambda p:p['due_at']),
            'recent_attempts':[serialize(r) for r in rows[-10:][::-1]]}

def make_router(db_session, evaluator_fn=None, help_fn=None):
    from .journeys import LearningRun, make_journey_router, practice_lock
    router=APIRouter(prefix='/api/v1'); lock=practice_lock

    @router.get('/progress')
    def progress(db=Depends(db_session)):
        return summarize(db)

    @router.get('/practice/current')
    def current(db=Depends(db_session)):
        row=db.scalar(select(Attempt).where(Attempt.status.in_(['awaiting_answer','failed'])).order_by(Attempt.created_at.desc()).limit(1))
        return serialize(row) if row else None

    @router.post('/practice/start')
    def start(payload:Start,db=Depends(db_session)):
        if not db.get(Learner,1): raise HTTPException(409,'Create your profile first.')
        pending=db.scalar(select(Attempt).where(Attempt.status.in_(['awaiting_answer','failed'])).limit(1))
        if pending: raise HTTPException(409,'Finish or discard the current question first.')
        summary=summarize(db)
        run=db.get(LearningRun,payload.run_id) if payload.run_id else None
        if payload.run_id and (not run or run.status!='active'):
            raise HTTPException(409,'Start or resume an active learning session.')
        from .curriculum import scoped_questions
        from .curriculum_api import RunPreference
        preference=db.get(RunPreference,run.id) if run else None
        config=json.loads(preference.config_json) if preference else None
        allowed=scoped_questions(run.topic_id if run.scope=='topic' else None,config['level'],config['module_levels'] if run.scope=='role' else None) if config else [q for q in QUESTIONS if not run or run.scope=='role' or q.get('topic_id','linear-regression')==run.topic_id]
        if not allowed:raise HTTPException(422,'No reviewed questions are available at this level yet.')
        allowed_skills=list(dict.fromkeys(q['skill'] for q in allowed))
        chosen_skill=payload.skill
        if chosen_skill is None:
            priorities=[p for p in (summary['due_reviews'] or summary['weak_areas']) if p['skill'] in allowed_skills]
            chosen_skill=priorities[0]['skill'] if priorities else next((s for s in allowed_skills if not any(p['skill']==s and p['mode']==payload.mode for p in summary['skills'])),allowed_skills[0])
        candidates=[q for q in allowed if q['skill']==chosen_skill]
        if not candidates: raise HTTPException(422,'Unknown skill.')
        history=list(db.scalars(select(Attempt).where(Attempt.status=='accepted')))
        question=min(candidates,key=lambda q:sum(json.loads(a.question_json)['id']==q['id'] for a in history))
        question={**question,'version':question.get('version',1),'run_id':payload.run_id}
        if payload.mode=='interview':
            question['prompt']='Interview question: '+question['prompt']+' Give a clear, concise explanation as you would to an interviewer.'
            question['criteria']=[*question['criteria'],'clarity']
            question['reference']+=' Clarity criterion: communicate a coherent, direct explanation using the correct quantities and units.'
        row=Attempt(id=str(uuid4()),created_at=datetime.now(timezone.utc).isoformat(),mode=payload.mode,question_json=json.dumps(question),status='awaiting_answer')
        db.add(row); db.commit(); return serialize(row)

    @router.post('/practice/{attempt_id}/discard')
    def discard(attempt_id:str,db=Depends(db_session)):
        if not lock.acquire(blocking=False): raise HTTPException(409,'An assessment is in progress.')
        try:
            row=db.get(Attempt,attempt_id)
            if not row: raise HTTPException(404,'Attempt not found.')
            if row.status=='accepted': raise HTTPException(409,'Accepted attempts cannot be discarded.')
            row.status='discarded'; db.commit(); return {'status':'discarded'}
        finally: lock.release()

    @router.post('/practice/{attempt_id}/submit')
    def submit(attempt_id:str,payload:Submission,db=Depends(db_session)):
        if not lock.acquire(blocking=False): raise HTTPException(409,'An assessment is in progress.')
        try:
            row=db.get(Attempt,attempt_id)
            if not row: raise HTTPException(404,'Attempt not found.')
            if row.status=='discarded': raise HTTPException(409,'This attempt was discarded.')
            if row.answer is not None and row.answer!=payload.answer: raise HTTPException(409,'Retry the saved answer or start a new question.')
            if row.status=='accepted': return serialize(row)
            if not os.getenv('OPENAI_API_KEY') and evaluator_fn is None: raise HTTPException(503,'Configure the backend OpenAI key to evaluate answers.')
            row.answer=payload.answer; row.status='failed'; db.commit()
            question=json.loads(row.question_json)
            try:
                value=(evaluator_fn or evaluate_answer)(question,payload.answer)
                evaluation=validate_evaluation(value,question,payload.answer)
            except Exception:
                raise HTTPException(502,'Assessment could not finish. Your answer is saved; retry without changing it.') from None
            result=evaluation.model_dump(); result['score']=score(evaluation)
            result['reference']=question['reference']; result['rule_version']='revision-v1'
            result['evaluator_prompt_version']=EVALUATOR_PROMPT_VERSION if evaluator_fn is None else 'test-evaluator'
            result['rubric_version']=question.get('version',1)
            row.feedback_json=json.dumps(result); row.assessed_at=datetime.now(timezone.utc).isoformat()
            row.model=os.getenv('OPENAI_MODEL','gpt-4.1-mini') if evaluator_fn is None else 'test-evaluator'
            row.status='accepted'; db.commit()
            return serialize(row)
        finally: lock.release()
    router.include_router(make_journey_router(db_session,start,help_fn))
    return router
