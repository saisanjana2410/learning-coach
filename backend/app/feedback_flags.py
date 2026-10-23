"""Learner reports preserve original assessments instead of silently regrading."""
import json
from datetime import datetime, timezone
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import String, Text, select
from sqlalchemy.orm import Mapped, mapped_column
from .main import Base
from .practice import Attempt

class FeedbackFlag(Base):
    __tablename__='feedback_flags'
    attempt_id: Mapped[str]=mapped_column(String(36),primary_key=True)
    reason: Mapped[str]=mapped_column(String(40))
    note: Mapped[str]=mapped_column(Text)
    snapshot_json: Mapped[str]=mapped_column(Text)
    created_at: Mapped[str]=mapped_column(String(40))
    updated_at: Mapped[str]=mapped_column(String(40))

class FlagInput(BaseModel):
    reason: Literal['incorrect_score','unclear_explanation','missing_context','other']
    note: str=Field(default='',max_length=2000)

def serialize(row):
    snapshot=json.loads(row.snapshot_json)
    return {'attempt_id':row.attempt_id,'reason':row.reason,'note':row.note,
            'created_at':row.created_at,'updated_at':row.updated_at,'status':'recorded',
            'skill':snapshot['question']['skill'],'original_score':snapshot['feedback']['score']}

def make_flag_router(db_session):
    from .journeys import practice_lock
    router=APIRouter(prefix='/api/v1')

    @router.get('/feedback/flags')
    def flags(db=Depends(db_session)):
        return [serialize(r) for r in db.scalars(select(FeedbackFlag).order_by(FeedbackFlag.updated_at.desc()))]

    @router.get('/practice/{attempt_id}/flag')
    def get_flag(attempt_id:str,db=Depends(db_session)):
        if not db.get(Attempt,attempt_id):raise HTTPException(404,'Attempt not found.')
        row=db.get(FeedbackFlag,attempt_id)
        return serialize(row) if row else None

    @router.put('/practice/{attempt_id}/flag')
    def flag(attempt_id:str,payload:FlagInput,db=Depends(db_session)):
        with practice_lock:
            attempt=db.get(Attempt,attempt_id)
            if not attempt:raise HTTPException(404,'Attempt not found.')
            if attempt.status!='accepted':raise HTTPException(409,'Only assessed answers can be flagged.')
            now=datetime.now(timezone.utc).isoformat()
            row=db.get(FeedbackFlag,attempt_id)
            if row:
                row.reason=payload.reason;row.note=payload.note.strip();row.updated_at=now
            else:
                row=FeedbackFlag(attempt_id=attempt_id,reason=payload.reason,note=payload.note.strip(),created_at=now,updated_at=now,
                    snapshot_json=json.dumps({'question':json.loads(attempt.question_json),'answer':attempt.answer,
                                              'feedback':json.loads(attempt.feedback_json),'model':attempt.model}))
                db.add(row)
            db.commit();return serialize(row)
    return router
