"""Additive, versioned catalog storage; learner evidence remains in attempts."""
import json
from datetime import datetime, timezone
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from .main import Base


class CatalogRole(Base):
    __tablename__='catalog_roles'
    id: Mapped[str]=mapped_column(String,primary_key=True)
    title: Mapped[str]
    payload: Mapped[str]=mapped_column(Text)

class CatalogModule(Base):
    __tablename__='catalog_modules'
    id: Mapped[str]=mapped_column(String,primary_key=True)
    payload: Mapped[str]=mapped_column(Text)

class CatalogTopic(Base):
    __tablename__='catalog_topics'
    id: Mapped[str]=mapped_column(String,primary_key=True)
    module_id: Mapped[str]=mapped_column(ForeignKey('catalog_modules.id'))
    payload: Mapped[str]=mapped_column(Text)

class RoleTopic(Base):
    __tablename__='role_topics'
    role_id: Mapped[str]=mapped_column(ForeignKey('catalog_roles.id'),primary_key=True)
    topic_id: Mapped[str]=mapped_column(ForeignKey('catalog_topics.id'),primary_key=True)
    importance: Mapped[str]
    recommended_order: Mapped[int]
    payload: Mapped[str]=mapped_column(Text)

class CatalogProject(Base):
    __tablename__='catalog_projects'
    id: Mapped[str]=mapped_column(String,primary_key=True)
    role_id: Mapped[str]=mapped_column(ForeignKey('catalog_roles.id'))
    level: Mapped[str]
    payload: Mapped[str]=mapped_column(Text)

class ContentVersion(Base):
    __tablename__='content_versions'
    id: Mapped[str]=mapped_column(String,primary_key=True)
    kind: Mapped[str]
    topic_id: Mapped[str]
    payload: Mapped[str]=mapped_column(Text)

class CatalogSkill(Base):
    __tablename__='catalog_skills'
    id: Mapped[str]=mapped_column(String,primary_key=True)
    title: Mapped[str]

class TopicSkill(Base):
    __tablename__='topic_skills'
    topic_id: Mapped[str]=mapped_column(ForeignKey('catalog_topics.id'),primary_key=True)
    skill_id: Mapped[str]=mapped_column(ForeignKey('catalog_skills.id'),primary_key=True)

class TopicPreference(Base):
    __tablename__='topic_preferences'
    learner_id: Mapped[int]=mapped_column(ForeignKey('learners.id'),primary_key=True)
    topic_id: Mapped[str]=mapped_column(ForeignKey('catalog_topics.id'),primary_key=True)
    level: Mapped[str]

class SchemaMigration(Base):
    __tablename__='schema_migrations'
    id: Mapped[str]=mapped_column(String,primary_key=True)
    applied_at: Mapped[str]


def seed_catalog(db):
    from .curriculum import TRACK_CATALOG, MODULES, QUESTIONS
    from .content import LESSONS
    from .track_catalog import slug
    version=TRACK_CATALOG['version']
    if db.get(SchemaMigration,version):return
    for ordering,module in enumerate(MODULES,1):
        objectives=[objective for topic in TRACK_CATALOG['topics'] if topic['module_id']==module['id']
                    for objective in topic['learning_objectives']]
        db.add(CatalogModule(id=module['id'],payload=json.dumps({**module,'ordering':ordering,
                            'learning_objectives':list(dict.fromkeys(objectives))})))
    for role in TRACK_CATALOG['roles']:
        db.add(CatalogRole(id=role['id'],title=role['title'],payload=json.dumps(role)))
    db.flush()
    for topic in TRACK_CATALOG['topics']:
        db.add(CatalogTopic(id=topic['id'],module_id=topic['module_id'],payload=json.dumps(topic)))
    db.flush()
    for link in TRACK_CATALOG['role_topics']:
        db.add(RoleTopic(role_id=link['role_id'],topic_id=link['topic_id'],importance=link['importance'],
                         recommended_order=link['recommended_order'],payload=json.dumps(link)))
    for role in TRACK_CATALOG['roles']:
        for project in role['projects']:
            db.add(CatalogProject(id=project['id'],role_id=role['id'],level=project['level'],payload=json.dumps(project)))
    skills={f'{q["submodule_id"]}:{slug(q["skill"])}':q for q in QUESTIONS}
    for skill_id,q in skills.items():
        db.add(CatalogSkill(id=skill_id,title=q['skill']))
    db.flush()
    for skill_id,q in skills.items():
        if q['submodule_id'] in {t['id'] for t in TRACK_CATALOG['topics']}:
            db.add(TopicSkill(topic_id=q['submodule_id'],skill_id=skill_id))
    for kind,items in [('lesson',LESSONS),('assessment',QUESTIONS)]:
        for item in items:
            definition=({'question_set':[item],'coding_task':None,'rubric':item['criteria'],
                         'passing_threshold':None,'status':'starter'} if kind=='assessment' else
                        {'learning_objective':item['title'],
                         'prerequisite_topic_ids':next(t['prerequisite_topic_ids'] for t in TRACK_CATALOG['topics'] if t['id']==item['submodule_id']),
                         'concept_and_example':item['sections'],'runnable_code':None,
                         'guided_exercise':None,'independent_challenge':None,'mini_project':None,
                         'mastery_rubric':None,'further_reading':[],'status':'starter'})
            db.add(ContentVersion(id=f'{kind}:{item["id"]}@{item.get("version",1)}',kind=kind,
                                  topic_id=item['submodule_id'],payload=json.dumps({**item,'definition':definition})))
    db.add(SchemaMigration(id=version,applied_at=datetime.now(timezone.utc).isoformat()))
    db.commit()
