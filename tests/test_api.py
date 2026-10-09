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
    assert client.get('/api/scores').json()['total'] == 0
    evidence_id = response.json()['id']
    reviewed = client.post(f'/api/evidence/{evidence_id}/reviews', json={
        'action': 'retake_requested', 'reason': '사진에 보호구가 분명히 보이지 않습니다.'
    })
    assert reviewed.status_code == 201
    assert client.get(f'/api/evidence/{evidence_id}/reviews').json()[0]['reason'] == '사진에 보호구가 분명히 보이지 않습니다.'
    assert client.get('/api/evidence/review-queue').json()[0]['id'] == evidence_id
    assert client.get('/api/scores').json()['total'] == 0


@pytest.mark.parametrize('scenario', ['judge_fail', 'judge_timeout', 'judge_invalid', 'verify_empty'])
def test_photo_model_failures_are_uncertain_and_never_scored(client, scenario):
    task = make_task(client)
    response = client.post('/api/evidence', data={
        'task_id': str(task['id']), 'item_code': 'fire-watch', 'forced_result': 'confirmed', 'scenario': scenario,
    }, files={'photo': ('a.jpg', b'fake', 'image/jpeg')})
    assert response.status_code == 201
    assert response.json()['result'] == 'uncertain'
    assert response.json()['points'] == 0
    assert client.get('/api/scores').json()['total'] == 0


def test_task_extraction_failure_stays_pending_until_conditions_fixed(client):
    task = client.post('/api/tasks', json={'text': '현장 작업 지시 원문', 'scenario': 'extract_fail'}).json()
    assert task['review_status'] == 'pending'
    assert client.get('/api/tasks/review-queue').json()[0]['id'] == task['id']
    assert client.post(f"/api/tasks/{task['id']}/review", json={
        'action': 'conditions_corrected', 'reason': '작업 지시 원문과 비교 예정'
    }).status_code == 409
    response = client.patch(f"/api/tasks/{task['id']}/conditions", json={
        'work': '용접·용단', 'height': '2층', 'flammable': '합판', 'ventilation': '양호',
        'nearby_people': '없음', 'place': '실내',
    })
    assert response.json()['review_status'] == 'ready'
    assert next(item for item in response.json()['checklist'] if item['code'] == 'fire-watch')['level'] == 'required'
    saved = client.post(f"/api/tasks/{task['id']}/review", json={
        'action': 'conditions_corrected', 'reason': '원문에서 합판과 2층을 확인했습니다.'
    })
    assert saved.json()['review_status'] == 'reviewed'
    assert client.get(f"/api/tasks/{task['id']}").json()['review_note'] == '원문에서 합판과 2층을 확인했습니다.'


@pytest.mark.parametrize('result', ['uncertain', 'not_visible'])
def test_non_confirmed_becomes_todo(client, result):
    task = make_task(client, DEMO + ', 환기 양호')
    response = client.post('/api/evidence', data={
        'task_id': str(task['id']), 'item_code': 'extinguisher', 'forced_result': result,
    }, files={'photo': ('a.jpg', b'fake', 'image/jpeg')})
    assert response.status_code == 201
    todos = client.get('/api/todos', params={'task_id': task['id']}).json()
    assert any(todo['kind'] == result and todo['item_code'] == 'extinguisher' for todo in todos)
    assert client.get(todos[0]['photo_url']).content == b'fake'


def test_report_tbm_and_worker_form(client):
    task = make_task(client)
    assert client.post('/api/reports').json() == {'points': 5}
    assert client.post('/api/tbm', json={'task_id': task['id'], 'points': ['화재감시자 배치'], 'attendees': '김OO'}).status_code == 201
    assert client.post('/api/worker-forms', json={'task_id': task['id'], 'understood': True, 'ppe_worn': True}).status_code == 201


def test_resolve_removes_todo_without_points(client):
    task = make_task(client, FULL)
    client.post('/api/evidence', data={'task_id': str(task['id']), 'item_code': 'extinguisher', 'forced_result': 'uncertain'},
                files={'photo': ('a.jpg', b'fake', 'image/jpeg')})
    assert client.post(f"/api/tasks/{task['id']}/items/extinguisher/resolve").status_code == 200
    assert client.get('/api/todos', params={'task_id': task['id']}).json() == []
    assert client.get('/api/scores').json()['total'] == 0


def test_login_returns_role_for_seed_accounts(client):
    admin = client.post('/api/login', json={'login_id': 'admin', 'password': '1234'})
    worker = client.post('/api/login', json={'login_id': 'worker', 'password': '1234'})
    invalid = client.post('/api/login', json={'login_id': 'worker', 'password': 'wrong'})
    assert admin.status_code == worker.status_code == 200
    assert admin.json()['role'] == 'admin'
    assert worker.json()['role'] == 'worker'
    assert invalid.status_code == 401


def test_eval_latest_returns_newest_report(client, tmp_path, monkeypatch):
    from eval.run import main

    monkeypatch.setenv('BANJANG_EVAL_OUT', str(tmp_path))
    assert client.get('/api/eval/latest').status_code == 404
    report = tmp_path / 'report.json'
    assert main(['--compare', '--json', str(report)]) == 0
    response = client.get('/api/eval/latest')
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload['dataset']['is_sample'], bool)
    assert 'rows' not in payload['results']['verify']
    assert payload['comparison']['variants'] == ['verify', 'no_verify', 'single_call']
