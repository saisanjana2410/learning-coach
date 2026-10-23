"""Saved project drafts and immutable milestone evidence using the existing evaluator."""
import json
import os
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import ForeignKey, String, Text, UniqueConstraint, select
from sqlalchemy.orm import Mapped, mapped_column
from .main import Base, Learner
from .practice import Attempt, assess_attempt, serialize
from .curriculum import LESSONS, LEVELS

PROJECT_ID='delivery-time'

class ProjectWorkspace(Base):
    __tablename__='project_workspaces'
    __table_args__=(UniqueConstraint('learner_id','project_id','level'),)
    id: Mapped[str]=mapped_column(String(36),primary_key=True)
    learner_id: Mapped[int]=mapped_column(ForeignKey('learners.id'))
    project_id: Mapped[str]
    level: Mapped[str]
    last_milestone_id: Mapped[str | None]
    created_at: Mapped[str]
    updated_at: Mapped[str]

class MilestoneDraft(Base):
    __tablename__='project_milestone_drafts'
    workspace_id: Mapped[str]=mapped_column(ForeignKey('project_workspaces.id'),primary_key=True)
    milestone_id: Mapped[str]=mapped_column(String(40),primary_key=True)
    text: Mapped[str]=mapped_column(Text,default='')
    version: Mapped[int]=mapped_column(default=0)
    updated_at: Mapped[str]

class ProjectSubmission(Base):
    __tablename__='project_milestone_submissions'
    id: Mapped[str]=mapped_column(String(80),primary_key=True)
    workspace_id: Mapped[str]=mapped_column(ForeignKey('project_workspaces.id'))
    milestone_id: Mapped[str]
    attempt_id: Mapped[str]=mapped_column(ForeignKey('practice_attempts.id'),unique=True)
    created_at: Mapped[str]

MILESTONES=[
 {'id':'data','title':'Prepare features and targets','topic':'python-for-ml',
  'task':'For a before-trip delivery-time predictor, prepare ordered features distance_km and traffic_index and target minutes. Explain feature availability, units, row alignment and missing-data handling. Include code/pseudocode or a small worked table with a missing value and a valid zero.',
  'rubric':{'features':'Names before-trip distance in kilometers and traffic index as inputs, with actual minutes as the separate target.',
            'rows':'Preserves row alignment and valid zeros; handles missing features explicitly using training-only fitted statistics.'},
  'advanced':('contract','Specify finite-value/type/range checks, a feature schema version and an offline/serving feature-parity test.'),
  'reference':'Use ordered [distance_km, traffic_index] in kilometers and a documented 0..1 traffic scale; y is actual minutes. Keep X/y rows aligned, preserve zero, and learn missing-feature fills only on training data. Add explicit finite/type/range and schema/parity checks for a stronger boundary.'},
 {'id':'baseline','title':'Establish a mean baseline','topic':'ml-project',
  'task':'Training delivery minutes are [12,14,16]; held-out actual minutes are [18,20]. Calculate the training-mean baseline and held-out MAE, state the units, and explain the training/evaluation boundary. Include calculation or code and what a baseline comparison establishes.',
  'rubric':{'calculation':'Computes training mean 14 and held-out MAE 5 minutes from absolute errors 4 and 6.',
            'boundary':'Fits the baseline only to training targets and evaluates fixed predictors on the same held-out records; does not claim real-world quality from the toy example.'},
  'advanced':('evaluation_policy','Specify a cohort/window policy and uncertainty or sample-size limitation for comparing this baseline with a production candidate.'),
  'reference':'The training mean is 14; held-out absolute errors are 4 and 6, giving MAE 5 minutes. Use the same evaluation records/metric for baseline and model. This tiny synthetic example checks arithmetic, not production generalization; stronger comparisons need representative cohorts and sample/uncertainty analysis.'},
 {'id':'training','title':'Build the fitted pipeline','topic':'python-for-ml',
  'task':'Design the delivery pipeline with missing-value imputation, scaling and Ridge regression. Explain their order, which rows fit every step, and how validation/serving rows are processed. Provide code or precise pseudocode and checks for a missing feature and fixed feature order.',
  'rubric':{'pipeline':'Orders imputation before scaling before regression in one pipeline or an equivalent explicit fitted procedure.',
            'fitting':'Fits transformations/model only on training rows and reuses fitted transforms for validation/serving without refitting.'},
  'advanced':('parity_tests','Specify tests for offline/serving parity, feature-order/schema mismatch and missing-value behavior in the saved full pipeline.'),
  'reference':'Use Pipeline([SimpleImputer, StandardScaler, Ridge]) in that order. Fit all learned steps only on training rows, then call predict on validation/serving inputs without refitting. Preserve feature order and save the whole fitted pipeline; test missing-input and offline/serving parity behavior.'},
 {'id':'evaluation','title':'Select and evaluate the model','topic':'ml-project',
  'task':'Use the project split of 72 training, 24 validation and 24 test rows. Explain how to choose Ridge alpha from [0.1,1,10], when to report final test MAE and how to compare the baseline. Include the experiment record fields and the limits of synthetic-data results.',
  'rubric':{'selection':'Fits on training data and selects alpha by validation MAE, keeping test observations out of tuning.',
            'reporting':'Evaluates the fixed winner and baseline on the same test records; records data/split identity, settings and metrics, and recognizes synthetic-data limits.'},
  'advanced':('validity','Specify deployment-relevant temporal/group boundaries when applicable, plus a predeclared selection/refit policy and uncertainty/sample-size limitation.'),
  'reference':'Fit candidates on 72 training rows, choose alpha by the 24-row validation MAE, then evaluate the fixed selected model and baseline on 24 untouched test rows. Record data/seed/splits, versions, feature schema, alpha and metrics. Do not retune on the test. Document any refit policy and assess representative cohort/time boundaries and uncertainty; synthetic results are demonstration evidence.'},
 {'id':'deployment','title':'Save and serve predictions','topic':'mlops-basics',
  'task':'Describe or implement saving the trusted full fitted pipeline and a manifest, then serving POST /predict for finite distance_km in [0,100] and traffic_index in [0,1]. Explain feature order, model loading, a versioned response, and a valid plus invalid-input test.',
  'rubric':{'artifact':'Saves/reloads the controlled full fitted pipeline and a manifest with feature order/units and model/environment identity.',
            'serving':'Validates finite bounded inputs and forbidden types/fields, reuses the loaded pipeline in saved feature order and returns minutes plus model version.'},
  'advanced':('release_checks','Specify artifact-integrity verification, offline/API prediction parity and a compatible previous pipeline/schema as a release/rollback check.'),
  'reference':'Save the full trusted pipeline and manifest; verify identity and load during setup rather than training per request. Validate finite bounded inputs and reject booleans/unexpected fields, construct [distance_km, traffic_index], call predict and return minutes/model_version. Test valid/invalid requests and offline/API parity; retain a compatible prior artifact/schema. A checksum is not authentication.'},
 {'id':'monitoring','title':'Define monitoring and rollback','topic':'mlops-basics',
  'task':'Write the project monitoring plan: distinguish service error/latency metrics, input-quality or drift signals and delayed labeled MAE. Specify model-version/cohort tracking, an observation window/minimum sample policy, and a compatible rollback target. Explain why drift alone is not proof of accuracy loss.',
  'rubric':{'signals':'Separates operational/data signals from labeled error and does not equate drift alone with measured accuracy loss.',
            'recovery':'Tracks version/cohort, specifies a window/sample policy and retains a compatible previous full pipeline/schema for rollback.'},
  'advanced':('operational_gate','Specify actionable alert thresholds, who investigates, label-delay handling and verification after rollback without claiming unsupported statistical certainty.'),
  'reference':'Monitor errors/p95 and input missingness/distributions separately from delayed labeled MAE. Track version and cohort, predeclare observation/sample requirements and investigate drift while awaiting labels. Keep a tested prior full pipeline with a compatible feature contract; verify health and parity after rollback. Advanced plans include actionable thresholds and investigation ownership.'},
]

def now():return datetime.now(timezone.utc).isoformat()

def milestone_question(workspace,milestone):
    lesson=next(l for l in LESSONS if l['submodule_id']==milestone['topic'] and l['level']==workspace.level)
    rubric=dict(milestone['rubric'])
    framing={'beginner':'Use a small worked example or clear pseudocode; explain terms as you go.',
             'foundational':'Show a small usable implementation or precise step-by-step pseudocode with expected results.',
             'intermediate':'Show integration details, checks and reproducibility/failure considerations.',
             'advanced':'Explain implementation choices and production tradeoffs with explicit verification evidence.'}[workspace.level]
    task=milestone['task']+' '+framing
    if workspace.level=='advanced':
        key,description=milestone['advanced'];rubric[key]=description;task+=' '+description
    return {'id':f'delivery-{milestone["id"]}-{workspace.level}','version':1,
        'skill':lesson['skill'],'lesson_id':lesson['id'],'module_id':lesson['module_id'],
        'submodule_id':milestone['topic'],'topic_id':milestone['topic'],'level':workspace.level,
        'prompt':task,'hint':lesson['takeaway'],'criteria':list(rubric),'criterion_descriptions':rubric,
        'reference':milestone['reference'],'project_workspace_id':workspace.id,
        'project_milestone_id':milestone['id'],'assessment_origin':'project_milestone'}

def workspace_data(db,workspace):
    submissions=list(db.scalars(select(ProjectSubmission).where(ProjectSubmission.workspace_id==workspace.id).order_by(ProjectSubmission.created_at)))
    attempts={s.id:db.get(Attempt,s.attempt_id) for s in submissions}
    milestones=[]
    for definition in MILESTONES:
        draft=db.get(MilestoneDraft,(workspace.id,definition['id']))
        history=[(s,attempts[s.id]) for s in submissions if s.milestone_id==definition['id']]
        accepted=[a for _,a in history if a.status=='accepted']
        latest=accepted[-1] if accepted else None
        feedback=json.loads(latest.feedback_json) if latest else None
        pending=next(((s,a) for s,a in reversed(history) if a.status in ('failed','awaiting_answer')),None)
        state='requirements_met' if feedback and feedback['score']==100 else 'needs_revision' if feedback else 'in_progress' if draft and draft.text else 'not_started'
        if pending:state='retry_required'
        question=milestone_question(workspace,definition)
        milestones.append({'id':definition['id'],'title':definition['title'],'task':question['prompt'],
            'rubric':[{'id':key,'description':value} for key,value in question['criterion_descriptions'].items()],
            'draft':draft.text if draft else '', 'draft_version':draft.version if draft else 0,
            'saved_at':draft.updated_at if draft else None,'status':state,
            'related_lesson':{'id':question['lesson_id'],'submodule_id':question['submodule_id'],'module_id':question['module_id'],'level':workspace.level},
            'latest_feedback':serialize(latest) if latest else None,
            'pending_submission':{'id':pending[0].id,'attempt':serialize(pending[1])} if pending else None,
            'history':[{'submission_id':s.id,'attempt':serialize(a)} for s,a in reversed(history)]})
    completed=sum(m['status']=='requirements_met' for m in milestones)
    resume=workspace.last_milestone_id or next((m['id'] for m in milestones if m['status']!='requirements_met'),milestones[-1]['id'])
    return {'workspace':{'id':workspace.id,'project_id':PROJECT_ID,'level':workspace.level,
            'created_at':workspace.created_at,'updated_at':workspace.updated_at,'completed':completed,'total':len(milestones),
            'status':'requirements_met' if completed==len(milestones) else 'in_progress','resume_milestone_id':resume},
            'milestones':milestones,'levels':LEVELS,
            'completion_policy':'A milestone meets requirements when its latest accepted feedback meets every rubric criterion. This is AI feedback on submitted text, not execution of your code or a mastery certification.'}

class StartProject(BaseModel):
    level: Literal['beginner','foundational','intermediate','advanced']
class DraftInput(BaseModel):
    text: str=Field(max_length=6000)
    version: int=Field(ge=0)
class SubmitInput(BaseModel):
    submission_id: str=Field(min_length=1,max_length=80)
    answer: str=Field(min_length=1,max_length=6000)

def make_project_router(db_session,evaluator_fn=None):
    from .journeys import practice_lock
    router=APIRouter(prefix='/api/v1/projects/delivery-time')
    def get_workspace(db,workspace_id):
        row=db.get(ProjectWorkspace,workspace_id)
        if not row or row.learner_id!=1 or row.project_id!=PROJECT_ID:raise HTTPException(404,'Project workspace not found.')
        return row
    def get_milestone(milestone_id):
        item=next((m for m in MILESTONES if m['id']==milestone_id),None)
        if not item:raise HTTPException(404,'Milestone not found.')
        return item

    @router.get('')
    def current(db=Depends(db_session)):
        row=db.scalar(select(ProjectWorkspace).where(ProjectWorkspace.learner_id==1,ProjectWorkspace.project_id==PROJECT_ID).order_by(ProjectWorkspace.updated_at.desc()).limit(1))
        from .curriculum_api import topic_levels
        return workspace_data(db,row) if row else {'workspace':None,'levels':LEVELS,'selected_level':topic_levels(db)['ml-project']}

    @router.post('/start')
    def start(payload:StartProject,db=Depends(db_session)):
        with practice_lock:
            if not db.get(Learner,1):raise HTTPException(409,'Create your learning profile first.')
            row=db.scalar(select(ProjectWorkspace).where(ProjectWorkspace.learner_id==1,ProjectWorkspace.project_id==PROJECT_ID,ProjectWorkspace.level==payload.level))
            if not row:
                row=ProjectWorkspace(id=str(uuid4()),learner_id=1,project_id=PROJECT_ID,level=payload.level,last_milestone_id=None,created_at=now(),updated_at=now())
                db.add(row)
            row.updated_at=now();db.commit();return workspace_data(db,row)

    @router.get('/workspaces/{workspace_id}')
    def workspace_by_id(workspace_id:str,db=Depends(db_session)):
        return workspace_data(db,get_workspace(db,workspace_id))

    @router.put('/{workspace_id}/milestones/{milestone_id}/draft')
    def save_draft(workspace_id:str,milestone_id:str,payload:DraftInput,db=Depends(db_session)):
        with practice_lock:
            workspace=get_workspace(db,workspace_id);get_milestone(milestone_id)
            row=db.get(MilestoneDraft,(workspace_id,milestone_id))
            if payload.version!=(row.version if row else 0):raise HTTPException(409,'This draft changed in another tab. Reload before replacing it.')
            if not row:row=MilestoneDraft(workspace_id=workspace_id,milestone_id=milestone_id,text='',version=0,updated_at=now());db.add(row)
            row.text=payload.text;row.version+=1;row.updated_at=now()
            workspace.last_milestone_id=milestone_id;workspace.updated_at=now();db.commit()
            return workspace_data(db,workspace)

    @router.post('/{workspace_id}/milestones/{milestone_id}/submit')
    def submit(workspace_id:str,milestone_id:str,payload:SubmitInput,db=Depends(db_session)):
        if not practice_lock.acquire(blocking=False):raise HTTPException(409,'An assessment is in progress. Try again shortly.')
        try:
            workspace=get_workspace(db,workspace_id);definition=get_milestone(milestone_id)
            if not payload.answer.strip():raise HTTPException(422,'Write your work and explanation first.')
            existing=db.get(ProjectSubmission,payload.submission_id)
            if existing:
                attempt=db.get(Attempt,existing.attempt_id)
                if existing.workspace_id!=workspace_id or existing.milestone_id!=milestone_id or attempt.answer!=payload.answer:
                    raise HTTPException(409,'Submission identifier is already used for different work.')
            else:
                if evaluator_fn is None and not os.getenv('OPENAI_API_KEY','').strip():raise HTTPException(503,'Configure the backend OpenAI key for milestone feedback. Drafts can still be saved.')
                earlier=list(db.scalars(select(ProjectSubmission).where(ProjectSubmission.workspace_id==workspace_id,ProjectSubmission.milestone_id==milestone_id)))
                prior=[db.get(Attempt,s.attempt_id) for s in earlier]
                if any(a.status in ('awaiting_answer','failed') for a in prior):raise HTTPException(409,'Retry or cancel the saved pending submission before submitting revised work.')
                if any(a.status=='accepted' and a.answer==payload.answer for a in prior):raise HTTPException(409,'This work already has feedback. Revise it before requesting a new evaluation.')
                attempt=Attempt(id=str(uuid4()),created_at=now(),mode='applied',question_json=json.dumps(milestone_question(workspace,definition)),answer=payload.answer,status='failed')
                db.add(attempt);db.flush()
                db.add(ProjectSubmission(id=payload.submission_id,workspace_id=workspace_id,milestone_id=milestone_id,attempt_id=attempt.id,created_at=now()))
                workspace.last_milestone_id=milestone_id;workspace.updated_at=now();db.commit()
            assess_attempt(db,attempt,payload.answer,evaluator_fn)
            workspace.updated_at=now();db.commit()
            return workspace_data(db,workspace)
        finally:practice_lock.release()
    return router
