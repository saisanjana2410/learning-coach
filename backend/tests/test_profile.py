from fastapi.testclient import TestClient
from app.main import create_app

PROFILE = {'target_role': 'AI/ML Engineer', 'experience': 'intermediate', 'study_minutes': 30, 'timezone': 'America/New_York'}

def test_profile_persists_across_restart(tmp_path):
    url = f'sqlite:///{(tmp_path / "test.db").as_posix()}'
    with TestClient(create_app(url)) as client:
        assert client.get('/api/v1/profile').json() is None
        saved = client.put('/api/v1/profile', json=PROFILE)
        assert saved.status_code == 200
    with TestClient(create_app(url)) as client:
        assert client.get('/api/v1/profile').json()['study_minutes'] == 30
        updated = client.put('/api/v1/profile', json={**PROFILE, 'study_minutes': 45})
        assert updated.json()['id'] == 1
        dashboard = client.get('/api/v1/dashboard').json()
        assert dashboard['profile']['study_minutes'] == 45
        assert dashboard['assessed_skills'] == 0
        assert dashboard['weak_areas'] == []

def test_invalid_profile_rejected(tmp_path):
    url = f'sqlite:///{(tmp_path / "test.db").as_posix()}'
    with TestClient(create_app(url)) as client:
        for changes in [{'study_minutes': 0}, {'timezone': 'not-a-zone'}, {'target_role': '  '}, {'experience': 'expert'}]:
            assert client.put('/api/v1/profile', json={**PROFILE, **changes}).status_code == 422
