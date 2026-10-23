import contextlib
import importlib.util
import io
import json
import sqlite3
import zipfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.focused_ml import PACKS, TOPICS, VERSION
from app.curriculum import LESSONS, QUESTIONS, SUBMODULES
from test_profile import PROFILE
from test_practice import result


@pytest.mark.parametrize('pack',PACKS,ids=lambda p:p['topic']+'-'+p['level'])
def test_authored_focus_examples(pack):
    stream=io.StringIO()
    with contextlib.redirect_stdout(stream):exec(compile(pack['code'],'authored-focus-example','exec'),{})
    assert stream.getvalue()==pack['output']


def test_active_path_and_future_modules_remain_visible(tmp_path):
    with TestClient(create_app(f'sqlite:///{tmp_path.as_posix()}/scope.db')) as c:
        c.put('/api/v1/profile',json=PROFILE)
        catalog=c.get('/api/v1/curriculum').json()
        assert [m['id'] for m in catalog['modules'][:3]]==['python','mlops','projects']
        assert {m['id'] for m in catalog['modules'] if m['release_status']=='active'}=={'python','mlops','projects'}
        assert all(m['release_status']=='coming_soon' for m in catalog['modules'] if m['id'] not in {'python','mlops','projects'})
        assert {'ml','math','react','ai','deep-learning'} <= {m['id'] for m in catalog['modules']}
        assert c.get('/api/v1/lessons?submodule_id=linear-regression&level=beginner').json()
        archive=c.get(catalog['focus']['project_download'])
        assert archive.status_code==200
        with zipfile.ZipFile(io.BytesIO(archive.content)) as z:
            assert {Path(n).name for n in z.namelist()}=={'README.md','requirements.txt','train.py','serve.py'}


@pytest.mark.parametrize('sid',[sid for sid,_,_ in TOPICS])
@pytest.mark.parametrize('level',['beginner','foundational','intermediate','advanced'])
def test_complete_focus_lessons_and_practice(tmp_path,sid,level):
    with TestClient(create_app(f'sqlite:///{tmp_path.as_posix()}/practice.db',evaluator_fn=lambda q,a:result(q,a))) as c:
        c.put('/api/v1/profile',json=PROFILE)
        c.put(f'/api/v1/curriculum/topics/{sid}/level',json={'level':level})
        lesson=c.get('/api/v1/lessons',params={'submodule_id':sid,'level':level}).json()[0]
        assert lesson['status']=='complete' and lesson['runnable_code'] and lesson['further_reading']
        assert len(lesson['mini_project']['rubric'])>=2
        for mode in ['concept','applied']:
            run=c.post('/api/v1/runs/start',json={'topic_id':sid,'mode':mode}).json()
            q=run['attempt']['question']
            assert q['submodule_id']==sid and q['level']==level
            assert q['id'].endswith('-check' if mode=='concept' else '-project')
            assert 'reference' not in q
            assert c.post(f'/api/v1/practice/{run["attempt"]["id"]}/submit',json={'answer':'My project code and reasoning.'}).status_code==200
            following=c.post(f'/api/v1/runs/{run["run"]["id"]}/next',json={'mode':mode}).json()
            assert following['attempt']['question']['id']!=q['id']
            c.post(f'/api/v1/runs/{run["run"]["id"]}/finish')
        progress=c.get('/api/v1/progress').json()
        assert any(s['submodule_id']==sid and s['level']==level for s in progress['skills'])


def test_focus_release_migrates_existing_catalog_idempotently(tmp_path):
    path=tmp_path/'release.db';url=f'sqlite:///{path.as_posix()}'
    with TestClient(create_app(url)) as c:c.put('/api/v1/profile',json=PROFILE)
    ids=[sid for sid,_,_ in TOPICS]
    with sqlite3.connect(path) as db:
        original=db.execute('select * from learners').fetchall()
        db.execute('delete from schema_migrations where id=?',(VERSION,))
        for sid in ids:
            db.execute('delete from content_versions where topic_id=?',(sid,))
            db.execute('delete from topic_skills where topic_id=?',(sid,))
            db.execute('delete from role_topics where topic_id=?',(sid,))
            db.execute('delete from catalog_topics where id=?',(sid,))
    for _ in range(2):
        with TestClient(create_app(url)) as c:assert len(c.get('/api/v1/curriculum').json()['focus']['milestones'])==6
    with sqlite3.connect(path) as db:
        assert db.execute('select * from learners').fetchall()==original
        for sid in ids:
            assert db.execute('select count(*) from content_versions where topic_id=?',(sid,)).fetchone()[0]==20


def load_example(name):
    path=Path(__file__).resolve().parents[2]/'examples'/'ml_project'/f'{name}.py'
    spec=importlib.util.spec_from_file_location('demo_'+name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_runnable_project_trains_serves_and_rejects_invalid_input(tmp_path):
    import joblib
    import pandas as pd
    report=load_example('train').train(tmp_path)
    assert (report['train_rows'],report['validation_rows'],report['test_rows'])==(72,24,24)
    assert report['test_mae']<report['baseline_test_mae']
    offline=joblib.load(tmp_path/'model.joblib')
    row={'distance_km':5.0,'traffic_index':.4}
    expected=float(offline.predict(pd.DataFrame([row],columns=report['features']))[0])
    with TestClient(load_example('serve').create_app(tmp_path)) as c:
        response=c.post('/predict',json=row)
        assert response.status_code==200
        assert response.json()['predicted_minutes']==pytest.approx(expected)
        assert response.json()['model_version']==report['model_version']
        for invalid in [{**row,'distance_km':-1},{**row,'distance_km':True},{**row,'distance_km':'5'},
                        {**row,'traffic_index':2},{**row,'extra':'bad'},{'distance_km':5.0}]:
            assert c.post('/predict',json=invalid).status_code==422
    (tmp_path/'model.joblib').write_bytes(b'altered')
    with pytest.raises(ValueError,match='hash'):load_example('serve').create_app(tmp_path)
