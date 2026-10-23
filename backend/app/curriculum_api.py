"""Persist per-module starting levels without changing existing profile records."""
import json
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import String, Text, select
from sqlalchemy.orm import Mapped, mapped_column
from .main import Base, Learner
from .curriculum import MODULES, SUBMODULES, LEVELS, role_path, TRACK_CATALOG
from .content import LESSONS
from .catalog_models import TopicPreference
from .track_catalog import resolve_role, LEVEL_DESCRIPTIONS
from .focused_ml import FOCUS_MODULES

class ModulePreference(Base):
    __tablename__='module_preferences'
    module_id: Mapped[str]=mapped_column(String(60),primary_key=True)
    level: Mapped[str]=mapped_column(String(20))

class RunPreference(Base):
    __tablename__='run_preferences'
    run_id: Mapped[str]=mapped_column(String(36),primary_key=True)
    config_json: Mapped[str]=mapped_column(Text)

class LevelInput(BaseModel):
    level: Literal['beginner','foundational','intermediate','advanced']

def module_levels(db):
    learner=db.get(Learner,1)
    fallback=learner.experience if learner else 'beginner'
    return {m['id']:(row.level if (row:=db.get(ModulePreference,m['id'])) else fallback) for m in MODULES}

class TopicLevelInput(BaseModel):
    level: Literal['beginner','foundational','intermediate','advanced'] | None

class RoleInput(BaseModel):
    role_id: str

def topic_levels(db):
    levels=module_levels(db)
    overrides={p.topic_id:p.level for p in db.scalars(select(TopicPreference).where(TopicPreference.learner_id==1))}
    return {sid:overrides.get(sid,levels[t['module_id']]) for sid,t in SUBMODULES.items()}

def catalog(db):
    learner=db.get(Learner,1);role=learner.target_role if learner else 'AI/ML Engineer'
    path,label=role_path(role);levels=module_levels(db);topics=topic_levels(db)
    path=FOCUS_MODULES;label='Python → MLOps → guided ML project'
    role_id=resolve_role(role)
    track=next((r for r in TRACK_CATALOG['roles'] if r['id']==role_id),None)
    relevant={r['topic_id'] for r in TRACK_CATALOG['role_topics'] if r['role_id']==role_id}
    overrides={p.topic_id for p in db.scalars(select(TopicPreference).where(TopicPreference.learner_id==1))}
    modules=[]
    for m in MODULES:
        level=levels[m['id']]
        submodules=[]
        for sid,title,available in m['submodules']:
            selected_level=topics[sid]
            lessons=[{'id':l['id'],'title':l['title'],'skill':l['skill'],'minutes':l['minutes']} for l in LESSONS
                     if l['submodule_id']==sid and l['level']==selected_level]
            submodules.append({**SUBMODULES[sid],'level':selected_level,'level_source':'topic' if sid in overrides else 'module','relevant_to_role':sid in relevant,'available_levels':list(dict.fromkeys(l['level'] for l in LESSONS if l['submodule_id']==sid)),'id':sid,'title':title,'status':'available' if lessons else 'planned','lessons':lessons})
        modules.append({**{k:v for k,v in m.items() if k!='submodules'},'level':level,'recommended':m['id'] in path,
                        'release_status':'active' if m['id'] in FOCUS_MODULES else 'coming_soon',
                        'suggested_order':path.index(m['id'])+1 if m['id'] in path else None,'submodules':submodules})
    from .jobs import active_job,recommendations
    active=active_job(db)
    job_plan=None
    source='Curated role template; no reviewed job description is active.'
    if active:
        from .practice import summarize
        job_plan=recommendations(active,modules,summarize(db))
        path=[]
        module_index={m['id']:m for m in modules}
        def include(module_id):
            if module_id in path:return
            for prerequisite in module_index[module_id]['prerequisites']:include(prerequisite)
            path.append(module_id)
        for item in job_plan['items']:
            if item['module_id'] in module_index:include(item['module_id'])
        for module in modules:
            module['recommended']=module['id'] in path
            module['suggested_order']=path.index(module['id'])+1 if module['id'] in path else None
            matches=[i['name'] for i in job_plan['items'] if i['module_id']==module['id']]
            module['recommendation_kind']='job_skill' if matches else 'prerequisite' if module['recommended'] else 'explore'
            if matches:module['reason']+=' Matches reviewed job skills: '+', '.join(matches)+'.'
            elif module['recommended']:module['reason']+=' Suggested prerequisite; not an extracted job requirement.'
        label='Preparation for '+active.title
        source='Reviewed job description skills, mapped using curated aliases. Prerequisites are separate suggestions.'
    return {'role':role,'path_label':label,'recommendation_source':source,'job_plan':job_plan,
            'track':track,'roles':[{'id':r['id'],'title':r['title']} for r in TRACK_CATALOG['roles']],
            'focus':{'title':'ML first release','module_ids':FOCUS_MODULES,
                'description':'Start with Python for ML, learn MLOps basics, and connect them through one delivery-time prediction project. Other modules are coming soon; earlier starter lessons remain accessible.',
                'project_download':'/api/v1/projects/delivery-time/starter.zip',
                'milestones':['Prepare ordered features and targets','Establish a mean baseline and held-out MAE','Fit preprocessing and select a model on validation data','Save the fitted pipeline and experiment manifest','Serve validated predictions and verify offline/API parity','Define monitoring signals and a compatible rollback']},
            'level_descriptions':LEVEL_DESCRIPTIONS,'levels':LEVELS,'modules':sorted(modules,key=lambda m:(0,FOCUS_MODULES.index(m['id'])) if m['id'] in FOCUS_MODULES else (1,m['suggested_order'] or 99)),
            'roadmap':['Feedback quality evaluation set','Broader topic coverage']}

def make_curriculum_router(db_session):
    router=APIRouter(prefix='/api/v1')
    @router.get('/curriculum')
    def get_catalog(db=Depends(db_session)):return catalog(db)

    @router.put('/curriculum/role')
    def save_role(payload:RoleInput,db=Depends(db_session)):
        role=next((r for r in TRACK_CATALOG['roles'] if r['id']==payload.role_id),None)
        if not role:raise HTTPException(422,'Unknown role track.')
        learner=db.get(Learner,1)
        if not learner:raise HTTPException(409,'Create your learning profile first.')
        learner.target_role=role['title'];db.commit();return catalog(db)

    @router.put('/curriculum/topics/{topic_id}/level')
    def save_topic_level(topic_id:str,payload:TopicLevelInput,db=Depends(db_session)):
        if topic_id not in SUBMODULES:raise HTTPException(404,'Topic not found.')
        if not db.get(Learner,1):raise HTTPException(409,'Create your learning profile first.')
        row=db.get(TopicPreference,(1,topic_id))
        if payload.level is None:
            if row:db.delete(row)
        elif row:row.level=payload.level
        else:db.add(TopicPreference(learner_id=1,topic_id=topic_id,level=payload.level))
        db.commit();return catalog(db)

    @router.put('/curriculum/{module_id}/level')
    def save_level(module_id:str,payload:LevelInput,db=Depends(db_session)):
        if module_id not in {m['id'] for m in MODULES}:raise HTTPException(404,'Module not found.')
        if not db.get(Learner,1):raise HTTPException(409,'Create your learning profile first.')
        row=db.get(ModulePreference,module_id)
        if row:row.level=payload.level
        else:db.add(ModulePreference(module_id=module_id,level=payload.level))
        db.commit();return catalog(db)
    return router
