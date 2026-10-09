"""작업·사진·점수 API의 핵심 계약을 확인한다."""

from fastapi.testclient import TestClient
import pytest

from app.main import create_app


DEMO = '2층 각파이프 용접, 옆에 합판'
FULL = '외부 지상에서 용접, 환기 양호, 가연물 없음, 혼자 작업'


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(str(tmp_path / 't.db'), str(tmp_path / 'up'))) as test_client:
        yield test_client


def make_task(client, text=DEMO):
    response = client.post('/api/tasks', json={'text': text})
    assert response.status_code == 201
    return response.json()


def test_demo_task_flammable_makes_fire_watch_required(client):
    task = make_task(client)
    assert task['conditions']['flammable'] == '합판'
    assert next(item for item in task['checklist'] if item['code'] == 'fire-watch')['level'] == 'required'


def test_removing_flammable_downgrades_fire_watch(client):
    task = make_task(client)
    response = client.patch(f"/api/tasks/{task['id']}/conditions", json={'flammable': '없음'})
    assert response.status_code == 200
    assert next(item for item in response.json()['checklist'] if item['code'] == 'fire-watch')['level'] == 'recommended'


def test_questions_and_404(client):
    assert client.get('/api/tasks/999').status_code == 404
    task = make_task(client)
    questions = client.get(f"/api/tasks/{task['id']}/questions").json()
    assert {question['key'] for question in questions} == {'ventilation', 'nearby_people', 'place'}


def test_confirmed_evidence_scores_once_per_item(client):
    task = make_task(client)
    data = {'task_id': str(task['id']), 'item_code': 'fire-watch', 'forced_result': 'confirmed'}
    first = client.post('/api/evidence', data=data, files={'photo': ('a.jpg', b'fake', 'image/jpeg')})
    second = client.post('/api/evidence', data=data, files={'photo': ('a.jpg', b'fake', 'image/jpeg')})
    assert first.status_code == second.status_code == 201
    assert (first.json()['points'], second.json()['points']) == (10, 0)
    assert client.get('/api/scores').json()['total'] == 10


def test_verify_rejection_becomes_uncertain_without_points(client):
    task = make_task(client)
    response = client.post('/api/evidence', data={
        'task_id': str(task['id']), 'item_code': 'fire-watch', 'forced_result': 'confirmed', 'scenario': 'verify_reject',
    }, files={'photo': ('a.jpg', b'fake', 'image/jpeg')})
    assert response.status_code == 201
    assert response.json()['result'] == 'uncertain'
    assert response.json()['points'] == 0
    assert response.json()['first_result'] == 'confirmed'
    assert response.json()['verified'] is False
