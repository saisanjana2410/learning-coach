"""Persist per-module starting levels without changing existing profile records."""
import json
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from .main import Base, Learner
from .curriculum import MODULES, SUBMODULES, LEVELS, role_path
from .content import LESSONS

class ModulePreference(Base):
    __tablename__='module_preferences'
    module_id: Mapped[str]=mapped_column(String(60),primary_key=True)
    level: Mapped[str]=mapped_column(String(20))

class RunPreference(Base):
    __tablename__='run_preferences'
    run_id: Mapped[str]=mapped_column(String(36),primary_key=True)
    config_json: Mapped[str]=mapped_column(Text)

class LevelInput(BaseModel):
    level: Literal['beginner','intermediate','advanced']

def module_levels(db):
    learner=db.get(Learner,1)
    fallback=learner.experience if learner else 'beginner'
    return {m['id']:(row.level if (row:=db.get(ModulePreference,m['id'])) else fallback) for m in MODULES}

def catalog(db):
    learner=db.get(Learner,1);role=learner.target_role if learner else 'AI/ML Engineer'
    path,label=role_path(role);levels=module_levels(db)
    modules=[]
    for m in MODULES:
        level=levels[m['id']]
        submodules=[]
        for sid,title,available in m['submodules']:
            lessons=[{'id':l['id'],'title':l['title'],'skill':l['skill'],'minutes':l['minutes']} for l in LESSONS
                     if l['submodule_id']==sid and l['level']==level]
            submodules.append({'id':sid,'title':title,'status':'available' if lessons else 'planned','lessons':lessons})
        modules.append({**{k:v for k,v in m.items() if k!='submodules'},'level':level,'recommended':m['id'] in path,
                        'suggested_order':path.index(m['id'])+1 if m['id'] in path else None,'submodules':submodules})
    return {'role':role,'path_label':label,'recommendation_source':'Curated role template; no job description has been analyzed.',
            'levels':LEVELS,'modules':sorted(modules,key=lambda m:m['suggested_order'] or 99),
            'roadmap':['Job description skill mapping','Feedback quality evaluation set','Dated technology updates']}

def make_curriculum_router(db_session):
    router=APIRouter(prefix='/api/v1')
    @router.get('/curriculum')
    def get_catalog(db=Depends(db_session)):return catalog(db)

    @router.put('/curriculum/{module_id}/level')
    def save_level(module_id:str,payload:LevelInput,db=Depends(db_session)):
        if module_id not in {m['id'] for m in MODULES}:raise HTTPException(404,'Module not found.')
        if not db.get(Learner,1):raise HTTPException(409,'Create your learning profile first.')
        row=db.get(ModulePreference,module_id)
        if row:row.level=payload.level
        else:db.add(ModulePreference(module_id=module_id,level=payload.level))
        db.commit();return catalog(db)
    return router
