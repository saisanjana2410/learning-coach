"""Open-ended learning runs and question-scoped discussions."""
import json
import os
from datetime import datetime, timezone
from threading import RLock
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import String, Text, select
from sqlalchemy.orm import Mapped, mapped_column
from .main import Base, Learner, ChatInput
from .practice import Attempt, serialize, summarize
from .curriculum import SUBMODULES, LEVELS, question_metadata
from .curriculum_api import RunPreference, module_levels

# One local worker: shared lock prevents next/finish/submit from racing.
practice_lock = RLock()

class LearningRun(Base):
    __tablename__='learning_runs'
    id: Mapped[str] = mapped_column(String(36),primary_key=True)
    scope: Mapped[str] = mapped_column(String(20))
    topic_id: Mapped[str | None] = mapped_column(String(60),nullable=True)
    role: Mapped[str] = mapped_column(String(120))
    mode: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20),default='active')
    created_at: Mapped[str] = mapped_column(String(40))
    summary_json: Mapped[str | None] = mapped_column(Text,nullable=True)

class QuestionDiscussion(Base):
    __tablename__='question_discussions'
    attempt_id: Mapped[str] = mapped_column(String(36),primary_key=True)
    messages_json: Mapped[str] = mapped_column(Text,default='[]')

class RunInput(BaseModel):
    scope: str = 'topic'
    topic_id: str | None = 'linear-regression'
    mode: str = 'concept'
    skill: str | None = None
    level: str | None = None

def run_attempts(db, run_id):
    return [a for a in db.scalars(select(Attempt).order_by(Attempt.created_at))
            if json.loads(a.question_json).get('run_id')==run_id]

def run_data(db, run):
    attempts=run_attempts(db,run.id)
    current=attempts[-1] if attempts and attempts[-1].status!='discarded' else None
    config=db.get(RunPreference,run.id)
    config=json.loads(config.config_json) if config else {}
    return {'run':{'id':run.id,'scope':run.scope,'topic_id':run.topic_id,'role':run.role,
                   'topic_title':SUBMODULES.get(run.topic_id,{}).get('title',run.topic_id),'level':config.get('level'),
                   'mode':run.mode,'status':run.status,'answered':sum(a.status=='accepted' for a in attempts)},
            'attempt':serialize(current) if current else None,
            'previous_attempts':[serialize(a) for a in attempts if a.status=='accepted' and (current is None or a.id!=current.id)],
            'summary':json.loads(run.summary_json) if run.summary_json else None}

def make_journey_router(db_session,start_question,help_fn=None):
    from .practice import Start
    router=APIRouter()

    def get_run(db,run_id):
        row=db.get(LearningRun,run_id)
        if not row: raise HTTPException(404,'Learning session not found.')
        return row

    @router.get('/runs/current')
    def current(db=Depends(db_session)):
        run=db.scalar(select(LearningRun).where(LearningRun.status=='active').order_by(LearningRun.created_at.desc()).limit(1))
        return run_data(db,run) if run else None

    @router.get('/runs/history')
    def history(db=Depends(db_session)):
        runs=db.scalars(select(LearningRun).where(LearningRun.status=='finished').order_by(LearningRun.created_at.desc()).limit(10))
        return [run_data(db,r) for r in runs]

    @router.post('/runs/start')
    def start(payload:RunInput,db=Depends(db_session)):
        with practice_lock:
            learner=db.get(Learner,1)
            if not learner: raise HTTPException(409,'Create your learning profile first.')
            if payload.scope not in ('topic','role') or payload.mode not in ('concept','applied','interview'):
                raise HTTPException(422,'Choose a supported scope and mode.')
            submodule=SUBMODULES.get(payload.topic_id)
            if payload.scope=='topic' and (not submodule or not submodule['available'] or payload.mode=='interview'):
                raise HTTPException(422,'Choose an available submodule for conceptual or applied practice.')
            if payload.scope=='role' and payload.mode!='interview':
                raise HTTPException(422,'Role practice uses interview mode.')
            active=db.scalar(select(LearningRun).where(LearningRun.status=='active').limit(1))
            if active: raise HTTPException(409,'Finish the current learning session before starting another.')
            run=LearningRun(id=str(uuid4()),scope=payload.scope,topic_id=payload.topic_id if payload.scope=='topic' else None,
                            role=learner.target_role,mode=payload.mode,status='active',created_at=datetime.now(timezone.utc).isoformat())
            db.add(run);db.flush()
            levels=module_levels(db)
            level=levels.get(submodule['module_id'],'beginner') if submodule else learner.experience
            if payload.level is not None:
                if payload.level not in LEVELS:
                    db.rollback();raise HTTPException(422,'Unknown learning level.')
                level=payload.level
                if run.scope=='role' and payload.skill:
                    from .curriculum import module_for_skill
                    match=module_for_skill(payload.skill)
                    if match:levels[match['module_id']]=level
            db.add(RunPreference(run_id=run.id,config_json=json.dumps({'level':level,'module_levels':levels})))
            db.flush()
            # Adopt an unanswered question from the earlier single-question UI.
            legacy=db.scalar(select(Attempt).where(Attempt.status.in_(['awaiting_answer','failed'])).limit(1))
            if legacy:
                q=json.loads(legacy.question_json)
                if legacy.mode!=run.mode or (run.scope=='topic' and q.get('submodule_id',q.get('topic_id','linear-regression'))!=run.topic_id):
                    db.rollback();raise HTTPException(409,'An older question is waiting. Resume it in its original mode before starting this session.')
                q['run_id']=run.id;legacy.question_json=json.dumps(q);db.commit()
            else:
                try:
                    start_question(Start(mode=run.mode,skill=payload.skill,run_id=run.id),db)
                except Exception:
                    db.rollback();raise
            return run_data(db,run)

    @router.post('/runs/{run_id}/next')
    def next_question(run_id:str,payload:RunInput,db=Depends(db_session)):
        with practice_lock:
            run=get_run(db,run_id)
            if run.status!='active':raise HTTPException(409,'This session is finished.')
            attempts=run_attempts(db,run.id)
            if attempts and attempts[-1].status in ('awaiting_answer','failed'):
                raise HTTPException(409,'Answer or skip the current question first.')
            if run.scope=='topic':
                if payload.mode not in ('concept','applied'):raise HTTPException(422,'Choose conceptual or applied practice.')
                run.mode=payload.mode
            start_question(Start(mode=run.mode,run_id=run.id),db)
            return run_data(db,run)

    @router.post('/runs/{run_id}/finish')
    def finish(run_id:str,db=Depends(db_session)):
        with practice_lock:
            run=get_run(db,run_id)
            if run.status=='finished':return run_data(db,run)
            attempts=run_attempts(db,run.id)
            for a in attempts:
                if a.status in ('awaiting_answer','failed'): a.status='discarded'
            accepted=[a for a in attempts if a.status=='accepted']
            touched=set()
            for a in accepted:
                q=question_metadata(json.loads(a.question_json))
                touched.add((q['skill'],a.mode,q.get('submodule_id'),q.get('level')))
            review=[s for s in summarize(db)['upcoming_reviews'] if (s['skill'],s['mode'],s['submodule_id'],s['level']) in touched]
            run.summary_json=json.dumps({'answered':len(accepted),'skipped':sum(a.status=='discarded' for a in attempts),
                'covered_skills':sorted({json.loads(a.question_json)['skill'] for a in accepted}),
                'strengths':[{'skill':json.loads(a.question_json)['skill'],'text':json.loads(a.feedback_json)['strengths']} for a in accepted if json.loads(a.feedback_json)['score'] is not None and json.loads(a.feedback_json)['score']>0],
                'gaps':[{'skill':json.loads(a.question_json)['skill'],'text':json.loads(a.feedback_json)['gap']} for a in accepted if json.loads(a.feedback_json)['score']!=100],
                'reviews':review,'attempts':[serialize(a) for a in accepted],
                'finished_at':datetime.now(timezone.utc).isoformat()})
            run.status='finished';db.commit();return run_data(db,run)

    @router.get('/practice/{attempt_id}/help')
    def help_history(attempt_id:str,db=Depends(db_session)):
        attempt=db.get(Attempt,attempt_id)
        if not attempt:raise HTTPException(404,'Question not found.')
        row=db.get(QuestionDiscussion,attempt_id)
        return {'messages':json.loads(row.messages_json) if row else []}

    @router.post('/practice/{attempt_id}/help')
    def question_help(attempt_id:str,payload:ChatInput,db=Depends(db_session)):
        from .tutor import explain_question
        with practice_lock:
            attempt=db.get(Attempt,attempt_id)
            if not attempt or attempt.status!='accepted':raise HTTPException(409,'Submit this answer before discussing its feedback.')
            row=db.get(QuestionDiscussion,attempt_id)
            if row is None:row=QuestionDiscussion(attempt_id=attempt_id,messages_json='[]');db.add(row)
            messages=json.loads(row.messages_json)
            existing=next((m for m in messages if m['id']==payload.client_message_id),None)
            if existing and (existing['role']!='user' or existing['content']!=payload.text):raise HTTPException(409,'Message identifier conflict.')
            if any(m.get('reply_to')==payload.client_message_id for m in messages):return {'messages':messages}
            if any(m['role']=='user' and not any(r.get('reply_to')==m['id'] for r in messages) for m in messages) and not existing:
                raise HTTPException(409,'Retry the unanswered help message first.')
            if not os.getenv('OPENAI_API_KEY') and help_fn is None:raise HTTPException(503,'Configure the backend OpenAI key.')
            if not existing:messages.append({'id':payload.client_message_id,'role':'user','content':payload.text})
            row.messages_json=json.dumps(messages);db.commit()
            try:
                reply=(help_fn or explain_question)(json.loads(attempt.question_json),attempt.answer,json.loads(attempt.feedback_json),
                    [{'role':m['role'],'content':m['content']} for m in messages[-16:]])
                if not isinstance(reply,str) or not reply.strip():raise ValueError('No reply')
            except Exception:raise HTTPException(502,'Help could not finish. Your question is saved; retry it.') from None
            messages.append({'id':str(uuid4()),'role':'assistant','content':reply,'reply_to':payload.client_message_id})
            row.messages_json=json.dumps(messages);db.commit();return {'messages':messages}
    return router
