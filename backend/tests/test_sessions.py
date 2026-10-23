from fastapi.testclient import TestClient
from app.main import create_app
from test_profile import PROFILE

def test_chat_is_saved_and_duplicate_retry_is_idempotent(tmp_path):
    calls = []
    def tutor(messages, learner, lesson):
        calls.append(messages)
        return 'The slope is 2 minutes per kilometer.'
    url = f'sqlite:///{(tmp_path / "sessions.db").as_posix()}'
    with TestClient(create_app(url, tutor_fn=tutor)) as c:
        assert c.post('/api/v1/sessions', json={'lesson_id':'predictions'}).status_code == 409
        c.put('/api/v1/profile', json=PROFILE)
        assert c.post('/api/v1/sessions', json={'lesson_id':'bad'}).status_code == 404
        session = c.post('/api/v1/sessions', json={'lesson_id':'predictions'}).json()
        path = f'/api/v1/sessions/{session["id"]}/messages'
        message = {'client_message_id':'one','text':'Explain slope'}
        assert len(c.post(path, json=message).json()['messages']) == 2
        assert len(c.post(path, json=message).json()['messages']) == 2
        assert len(calls) == 1
        assert c.post(path, json={**message,'text':'Different'}).status_code == 409
    with TestClient(create_app(url, tutor_fn=tutor)) as c:
        assert len(c.get(f'/api/v1/sessions/{session["id"]}').json()['messages']) == 2
        assert c.get('/api/v1/dashboard').json()['active_session']['id'] == session['id']

def test_failure_preserves_answer_and_allows_retry(tmp_path):
    count = 0
    def tutor(*args):
        nonlocal count
        count += 1
        if count == 1:
            raise RuntimeError('sensitive provider detail')
        return 'Try interpreting the units.'
    url = f'sqlite:///{(tmp_path / "retry.db").as_posix()}'
    with TestClient(create_app(url, tutor_fn=tutor)) as c:
        c.put('/api/v1/profile', json=PROFILE)
        session = c.post('/api/v1/sessions', json={'lesson_id':'predictions'}).json()
        path = f'/api/v1/sessions/{session["id"]}/messages'
        msg = {'client_message_id':'retry','text':'Help'}
        response = c.post(path, json=msg)
        assert response.status_code == 502
        assert 'sensitive' not in response.text
        assert len(c.get(f'/api/v1/sessions/{session["id"]}').json()['messages']) == 1
        assert len(c.post(path, json=msg).json()['messages']) == 2

def test_unconfigured_tutor_keeps_lessons_available(tmp_path, monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    url = f'sqlite:///{(tmp_path / "offline.db").as_posix()}'
    with TestClient(create_app(url)) as c:
        c.put('/api/v1/profile', json=PROFILE)
        assert len(c.get('/api/v1/lessons').json()) == 3
        assert c.get('/api/v1/tutor/status').json()['configured'] is False
        session = c.post('/api/v1/sessions', json={'lesson_id':'predictions'}).json()
        assert c.post(f'/api/v1/sessions/{session["id"]}/messages',json={'client_message_id':'x','text':'Help'}).status_code == 503
