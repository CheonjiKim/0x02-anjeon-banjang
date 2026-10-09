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
