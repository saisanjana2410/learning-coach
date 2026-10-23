import contextlib
import io
import json
import sqlite3
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.curriculum import LESSONS, QUESTIONS
from app.python_basics import PACKS, VERSION
from test_profile import PROFILE
from test_practice import result


@pytest.mark.parametrize('pack',PACKS,ids=lambda p:p['level'])
def test_authored_examples_produce_documented_outputs(pack):
    # Only checked-in authored examples are executed; never learner submissions.
    output=io.StringIO()
    with contextlib.redirect_stdout(output):exec(compile(pack['code'],'authored-example','exec'),{})
    assert output.getvalue()==pack['output']


@pytest.mark.parametrize('level',['beginner','foundational','intermediate','advanced'])
def test_complete_lessons_and_assessed_projects(level,tmp_path):
    with TestClient(create_app(f'sqlite:///{tmp_path.as_posix()}/lesson.db',evaluator_fn=lambda q,a:result(q,a))) as c:
        c.put('/api/v1/profile',json=PROFILE)
        c.put('/api/v1/curriculum/topics/python-basics/level',json={'level':level})
        lessons=c.get('/api/v1/lessons',params={'submodule_id':'python-basics','level':level}).json()
        assert len(lessons)==1
        lesson=lessons[0]
        assert lesson['status']=='complete'
        assert lesson['runnable_code'] and lesson['mini_project']['rubric'] and lesson['further_reading']
        assert lesson['next_topic_ids']
        for mode,suffix in [('concept','check'),('applied','project')]:
            run=c.post('/api/v1/runs/start',json={'topic_id':'python-basics','mode':mode}).json()
            question=run['attempt']['question']
            assert question['level']==level and question['id'].endswith('-'+suffix)
            assert 'reference' not in question and 'criteria' not in question
            assessed=c.post(f'/api/v1/practice/{run["attempt"]["id"]}/submit',json={'answer':'My code and explanation.'})
            assert assessed.status_code==200
            c.post(f'/api/v1/runs/{run["run"]["id"]}/finish')
        progress=c.get('/api/v1/progress').json()
        assert any(s['submodule_id']=='python-basics' and s['level']==level for s in progress['skills'])
        for mode,suffix in [('concept','transfer'),('applied','challenge')]:
            run=c.post('/api/v1/runs/start',json={'topic_id':'python-basics','mode':mode}).json()
            assert run['attempt']['question']['id'].endswith('-'+suffix)
            c.post(f'/api/v1/runs/{run["run"]["id"]}/finish')


def test_new_content_release_is_idempotent_on_existing_catalog(tmp_path):
    path=tmp_path/'release.db';url=f'sqlite:///{path.as_posix()}'
    with TestClient(create_app(url)) as c:c.put('/api/v1/profile',json=PROFILE)
    # Model a database that already has the preceding catalog migration.
    with sqlite3.connect(path) as db:
        db.execute('delete from schema_migrations where id=?',(VERSION,))
        db.execute("delete from content_versions where topic_id='python-basics'")
        db.execute("delete from topic_skills where topic_id='python-basics'")
        db.execute("delete from catalog_skills where id like 'python-basics:%'")
        old=db.execute('select * from learners').fetchall()
    for _ in range(2):
        with TestClient(create_app(url)) as c:
            assert len(c.get('/api/v1/lessons?submodule_id=python-basics&level=foundational').json())==1
    with sqlite3.connect(path) as db:
        assert db.execute('select * from learners').fetchall()==old
        assert db.execute("select count(*) from content_versions where topic_id='python-basics'").fetchone()[0]==20
        assert db.execute("select count(*) from catalog_skills where id like 'python-basics:%'").fetchone()[0]==4
