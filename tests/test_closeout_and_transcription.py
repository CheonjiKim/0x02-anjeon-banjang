import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(str(tmp_path / 't.db'), str(tmp_path / 'up'))) as test_client:
        yield test_client


def test_transcription_uses_audio_client(client, monkeypatch):
    seen = {}

    def fake(name, content, content_type):
        seen.update(name=name, content=content, content_type=content_type)
        return '용접 작업을 시작합니다.'

    monkeypatch.setattr('app.routers.transcription.transcribe_audio', fake)
    response = client.post('/api/transcriptions', files={'audio': ('voice.webm', b'audio', 'audio/webm')})
    assert response.status_code == 200
    assert response.json() == {'text': '용접 작업을 시작합니다.'}
    assert seen['name'] == 'voice.webm'


def test_transcription_rejects_invalid_suffix(client):
    response = client.post('/api/transcriptions', files={'audio': ('voice.txt', b'audio', 'text/plain')})
    assert response.status_code == 422


def test_closeout_photo_and_manager_review(client, tmp_path):
    task = client.post('/api/tasks', json={'text': '용접 작업', 'close_requested': True}).json()
    form = client.post('/api/worker-forms', json={'task_id': task['id'], 'report_text': '작업 완료', 'risk_note': '통로 정리 필요', 'ppe_worn': True}).json()
    upload = client.post(f"/api/worker-forms/{form['id']}/photo", files={'photo': ('close.jpg', b'fake', 'image/jpeg')})
    assert upload.status_code == 200 and upload.json()['photo_url']
    forms = client.get('/api/worker-forms', params={'task_id': task['id']}).json()
    assert forms[0]['report_text'] == '작업 완료'
    assert client.get('/api/tbm-suggestions', params={'task_id': task['id']}).json()['suggestions'] == ['통로 정리 필요']


def test_latest_tbm_returns_final_text_and_missing_rules(client):
    task = client.post('/api/tasks', json={'text': '용접 작업, 옆에 합판'}).json()
    saved = client.post('/api/tbm', json={
        'task_id': task['id'], 'transcript': '보안경을 착용합니다.', 'memo': '통로를 정리합니다.', 'attendees': '김작업',
    })
    assert saved.status_code == 201
    latest = client.get('/api/tbm/latest', params={'task_id': task['id']})
    assert latest.status_code == 200
    assert latest.json()['transcript'] == '보안경을 착용합니다.'
    assert latest.json()['memo'] == '통로를 정리합니다.'
    assert latest.json()['attendees'] == '김작업'
    assert latest.json()['missing']
    assert client.get('/api/tbm/latest', params={'task_id': 999}).status_code == 404


def test_closeout_must_be_requested_and_incident_awards_points(client):
    task = client.post('/api/tasks', json={'text': '용접 작업', 'close_requested': False}).json()
    assert client.post('/api/worker-forms', json={'task_id': task['id'], 'ppe_worn': True}).status_code == 409
    incident = client.post('/api/incidents', json={'note': '발이 미끄러질 뻔함'})
    assert incident.status_code == 201 and incident.json()['points'] == 5
    incident_id = incident.json()['id']
    assert client.post(f'/api/incidents/{incident_id}/follow-up').status_code == 200
