"""Local single-learner API with persistent tutor conversations."""
import os
import json
from threading import Lock
from uuid import uuid4
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

BASE = Path(__file__).resolve().parents[1]
load_dotenv(BASE / '.env')
from .content import LESSONS, find_lesson
from .curriculum import QUESTIONS, module_for_skill

class Base(DeclarativeBase):
    pass

class Learner(Base):
    __tablename__ = 'learners'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    target_role: Mapped[str] = mapped_column(String(120))
    experience: Mapped[str] = mapped_column(String(30))
    study_minutes: Mapped[int]
    timezone: Mapped[str] = mapped_column(String(80))

class ProfileInput(BaseModel):
    target_role: str = Field(min_length=2, max_length=120)
    experience: Literal['beginner', 'intermediate', 'advanced']
    study_minutes: int = Field(ge=5, le=240)
    timezone: str = Field(max_length=80)

    @field_validator('target_role', mode='before')
    @classmethod
    def trim_role(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator('timezone')
    @classmethod
    def valid_timezone(cls, value):
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError('Choose a valid IANA timezone, such as America/New_York')
        return value

class Profile(ProfileInput):
    model_config = ConfigDict(from_attributes=True)
    id: int

class LearningSession(Base):
    __tablename__ = 'learning_sessions'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    lesson_id: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[str] = mapped_column(String(40))
    messages_json: Mapped[str] = mapped_column(Text, default='[]')

class SessionInput(BaseModel):
    lesson_id: str = Field(max_length=40)

class ChatInput(BaseModel):
    client_message_id: str = Field(min_length=1, max_length=80)
    text: str = Field(min_length=1, max_length=4000)

    @field_validator('text')
    @classmethod
    def nonempty(cls, value):
        if not value.strip():
            raise ValueError('Message cannot be blank')
        return value.strip()

SKILLS = ['Interpret coefficients', 'Make predictions', 'Understand residuals', 'Measure prediction error', 'Evaluate on unseen data', 'Python data handling', 'SQL aggregation', 'Classification metrics']
SKILLS = list(dict.fromkeys(SKILLS+[q['skill'] for q in QUESTIONS]))
TOPIC = {'id': 'linear-regression', 'title': 'Linear regression', 'description': 'Understand predictions, coefficients, and how to measure model error.', 'status': 'available', 'skills': SKILLS[:5]}

def create_app(database_url=None, tutor_fn=None, evaluator_fn=None, help_fn=None, job_extractor_fn=None):
    url = database_url or os.getenv('DATABASE_URL', f'sqlite:///{(BASE / "learning.db").as_posix()}')
    engine = create_engine(url, connect_args={'check_same_thread': False} if url.startswith('sqlite') else {})

    @asynccontextmanager
    async def lifespan(app):
        Base.metadata.create_all(engine)
        yield
        engine.dispose()

    api = FastAPI(title='Learning Coach API', version='0.1.0', lifespan=lifespan)
    chat_lock = Lock()

    def session_data(row):
        return {'id': row.id, 'lesson_id': row.lesson_id, 'created_at': row.created_at,
                'messages': json.loads(row.messages_json), 'lesson': find_lesson(row.lesson_id)}

    def db_session():
        with Session(engine) as session:
            yield session

    from .practice import make_router, summarize
    from .curriculum_api import make_curriculum_router
    api.include_router(make_curriculum_router(db_session))
    api.include_router(make_router(db_session, evaluator_fn, help_fn))
    from .jobs import make_job_router
    api.include_router(make_job_router(db_session,job_extractor_fn))

    @api.get('/api/v1/health')
    def health():
        return {'status': 'ok'}

    @api.get('/api/v1/profile', response_model=Profile | None)
    def profile(db: Session = Depends(db_session)):
        return db.get(Learner, 1)

    @api.put('/api/v1/profile', response_model=Profile)
    def save_profile(payload: ProfileInput, db: Session = Depends(db_session)):
        learner = db.get(Learner, 1)
        if learner is None:
            learner = Learner(id=1, **payload.model_dump())
            db.add(learner)
        else:
            for key, value in payload.model_dump().items():
                setattr(learner, key, value)
        db.commit()
        db.refresh(learner)
        return learner

    @api.get('/api/v1/topics')
    def topics():
        return [TOPIC]

    @api.get('/api/v1/lessons')
    def lessons(submodule_id:str|None=None,level:str|None=None):
        if level is not None and level not in ('beginner','intermediate','advanced'):
            raise HTTPException(422,'Unknown learning level.')
        if submodule_id is None:return LESSONS[:3]
        return [l for l in LESSONS if l['submodule_id']==submodule_id and (level is None or l['level']==level)]

    @api.get('/api/v1/tutor/status')
    def tutor_status():
        from .tutor import configured
        return {'configured': configured() or tutor_fn is not None, 'model': os.getenv('OPENAI_MODEL', 'gpt-4.1-mini')}

    @api.post('/api/v1/sessions', status_code=201)
    def start_session(payload: SessionInput, db: Session = Depends(db_session)):
        if not db.get(Learner, 1):
            raise HTTPException(409, 'Create your learning profile first.')
        if not find_lesson(payload.lesson_id):
            raise HTTPException(404, 'Lesson not found.')
        row = LearningSession(id=str(uuid4()), lesson_id=payload.lesson_id,
                              created_at=datetime.now(timezone.utc).isoformat(), messages_json='[]')
        db.add(row); db.commit(); db.refresh(row)
        return session_data(row)

    @api.get('/api/v1/sessions/{session_id}')
    def get_session(session_id: str, db: Session = Depends(db_session)):
        row = db.get(LearningSession, session_id)
        if row is None:
            raise HTTPException(404, 'Session not found.')
        return session_data(row)

    @api.post('/api/v1/sessions/{session_id}/messages')
    def send_message(session_id: str, payload: ChatInput, db: Session = Depends(db_session)):
        from .tutor import configured, tutor_reply
        if not chat_lock.acquire(blocking=False):
            raise HTTPException(409, 'A tutor reply is in progress. Try again shortly.')
        try:
            row = db.get(LearningSession, session_id)
            if row is None:
                raise HTTPException(404, 'Session not found.')
            history = json.loads(row.messages_json)
            existing = next((m for m in history if m.get('id') == payload.client_message_id), None)
            if existing and (existing['role'] != 'user' or existing['content'] != payload.text):
                raise HTTPException(409, 'Message identifier already used for different content.')
            if any(m.get('reply_to') == payload.client_message_id for m in history):
                return session_data(row)
            if not configured() and tutor_fn is None:
                raise HTTPException(503, 'Add OPENAI_API_KEY to backend/.env and restart the backend. Lessons remain available.')
            pending = [m for m in history if m['role'] == 'user' and not any(r.get('reply_to') == m['id'] for r in history)]
            if pending and not existing:
                raise HTTPException(409, 'Retry the previous unanswered message first.')
            if not existing:
                history.append({'id': payload.client_message_id, 'role': 'user', 'content': payload.text})
                row.messages_json = json.dumps(history); db.commit()
            learner = db.get(Learner, 1)
            try:
                answer = (tutor_fn or tutor_reply)(
                    [{'role': m['role'], 'content': m['content']} for m in history],
                    {**Profile.model_validate(learner).model_dump(exclude={'id', 'timezone'}),
                     'weak_areas': summarize(db)['weak_areas']}, find_lesson(row.lesson_id))
            except Exception:
                raise HTTPException(502, 'The tutor could not respond. Check the backend key, model access, billing, and connection, then retry this message.') from None
            history.append({'id': str(uuid4()), 'role': 'assistant', 'content': answer, 'reply_to': payload.client_message_id})
            row.messages_json = json.dumps(history); db.commit()
            return session_data(row)
        finally:
            chat_lock.release()

    @api.get('/api/v1/dashboard')
    def dashboard(db: Session = Depends(db_session)):
        from .curriculum_api import catalog
        learner = db.get(Learner, 1)
        active = db.scalar(select(LearningSession).order_by(LearningSession.created_at.desc()).limit(1))
        progress=summarize(db)
        return {'profile': Profile.model_validate(learner) if learner else None,
                'topics': [TOPIC], 'due_reviews': progress['due_reviews'], 'weak_areas': progress['weak_areas'],
                'curriculum':catalog(db),
                'skill_scopes':{s:module_for_skill(s)['submodule_id'] for s in SKILLS if module_for_skill(s)},
                'assessed_skills': progress['assessed_skills'], 'total_skills':len(SKILLS), 'active_session': {'id': active.id, 'lesson_id': active.lesson_id} if active else None,
                'generated_at': datetime.now(timezone.utc).isoformat()}

    return api

app = create_app()
