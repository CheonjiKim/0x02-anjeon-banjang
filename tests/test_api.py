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
    response = client.patch(f"/api/tasks/{task['id']}/conditions", json={'flammable': '없음', 'review_evidence': '현장에서 가연물 주변을 직접 확인'})
    assert response.status_code == 200
    assert next(item for item in response.json()['checklist'] if item['code'] == 'fire-watch')['level'] == 'recommended'


def test_unsupported_work_is_rejected_without_changing_task(client):
    task = make_task(client)
    response = client.patch(f"/api/tasks/{task['id']}/conditions", json={'work': '시멘트 나르기'})
    assert response.status_code == 422
    assert response.json()['detail'] == '현재는 지원하지 않는 작업 종류입니다. 추후 지원될 예정입니다.'
    saved = client.get(f"/api/tasks/{task['id']}").json()
    assert saved['conditions'] == task['conditions']


def test_common_welding_name_is_accepted_as_supported_work(client):
    task = make_task(client, '각 파이프 용접해야 합니다.')
    response = client.patch(f"/api/tasks/{task['id']}/conditions", json={'work': '용접'})
    assert response.status_code == 200
    assert response.json()['conditions']['work'] == '용접·용단'


def test_missing_details_do_not_block_conservative_welding_checklist(client):
    task = make_task(client, '5층 용접')
    assert task['review_status'] == 'ready'
    assert task['conditions']['flammable'] == '알 수 없음'
    assert task['conditions']['ventilation'] == '알 수 없음'
    assert client.get('/api/tasks/review-queue').json() == []
    assert next(item for item in task['checklist'] if item['code'] == 'fire-watch')['level'] == 'required'
    assert next(item for item in task['checklist'] if item['code'] == 'ventilation')['level'] == 'required'
    reviewed = client.post(f"/api/tasks/{task['id']}/review", json={
        'action': 'conditions_corrected', 'reason': '정보가 없는 조건은 보수적으로 유지합니다.'
    })
    assert reviewed.status_code == 200


def test_blank_details_stay_unknown_and_no_ventilation_means_poor(client):
    task = make_task(client, '5층 용접')
    response = client.patch(f"/api/tasks/{task['id']}/conditions", json={
        'flammable': '', 'ventilation': '없음', 'nearby_people': '10인', 'place': '',
    })
    assert response.status_code == 200
    conditions = response.json()['conditions']
    assert conditions['flammable'] == conditions['place'] == '알 수 없음'
    assert conditions['ventilation'] == '불량'
    assert conditions['nearby_people'] == '10명'
    assert response.json()['review_status'] == 'ready'


def test_questions_and_404(client):
    assert client.get('/api/tasks/999').status_code == 404
    task = make_task(client)
    questions = client.get(f"/api/tasks/{task['id']}/questions").json()
    assert {question['key'] for question in questions} == {'height', 'ventilation', 'nearby_people', 'place'}


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
    assert response.json()['mode'] == 'mock'
    assert client.get('/api/scores').json()['total'] == 0
    task_status = client.get(f"/api/tasks/{task['id']}").json()['review_status']
    evidence_id = response.json()['id']
    reviewed = client.post(f'/api/evidence/{evidence_id}/reviews', json={
        'action': 'retake_requested', 'reason': '사진에 보호구가 분명히 보이지 않습니다.'
    })
    assert reviewed.status_code == 201
    assert client.get(f'/api/evidence/{evidence_id}/reviews').json()[0]['reason'] == '사진에 보호구가 분명히 보이지 않습니다.'
    assert client.get('/api/evidence/review-queue').json()[0]['id'] == evidence_id
    assert client.get('/api/scores').json()['total'] == 0
    assert client.get(f"/api/tasks/{task['id']}").json()['review_status'] == task_status


def test_runtime_mode_honors_vision_override_without_calling_model(client, monkeypatch):
    monkeypatch.setenv('BANJANG_LLM', 'openai')
    assert client.get('/api/runtime').json() == {'vision_mode': 'mock'}
    monkeypatch.setenv('BANJANG_VISION', 'openai')
    assert client.get('/api/runtime').json() == {'vision_mode': 'openai'}
    # A forced mock scenario must be labelled mock even with real mode configured.
    monkeypatch.setenv('BANJANG_LLM', 'mock')
    task = make_task(client)
    response = client.post('/api/evidence', data={
        'task_id': str(task['id']), 'item_code': 'extinguisher', 'scenario': 'judge_fail',
    }, files={'photo': ('a.jpg', b'fake', 'image/jpeg')})
    assert response.json()['mode'] == 'mock'
    monkeypatch.setenv('BANJANG_VISION', 'bad-setting')
    assert client.get('/api/runtime').json() == {'vision_mode': 'unavailable'}


def test_photo_review_does_not_clear_pending_task_condition_review(client):
    task = client.post('/api/tasks', json={'text': '현장 작업 지시 원문', 'scenario': 'extract_fail'}).json()
    response = client.post('/api/evidence', data={
        'task_id': str(task['id']), 'item_code': 'fire-watch', 'scenario': 'judge_fail',
    }, files={'photo': ('a.jpg', b'fake', 'image/jpeg')})
    assert response.status_code == 201 and response.json()['result'] == 'uncertain'
    assert client.get(f"/api/tasks/{task['id']}").json()['review_status'] == 'pending'
    reviewed = client.post(f"/api/evidence/{response.json()['id']}/reviews", json={
        'action': 'confirmed_by_manager', 'reason': '사진과 실제 조치를 대조했습니다.'
    })
    assert reviewed.status_code == 201
    saved = client.get(f"/api/tasks/{task['id']}").json()
    assert saved['review_status'] == 'pending'
    assert saved['conditions']['work'] == '알 수 없음'


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
        'work': '용접·용단', 'height': '2m', 'floor': '2층', 'flammable': '합판', 'ventilation': '양호',
        'nearby_people': '없음', 'place': '실내', 'review_evidence': '관리자가 현장 주변과 환기 상태를 확인',
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


def test_personal_scores_history_and_streak_do_not_include_other_workers(client):
    client.post('/api/reports', params={'worker_id': 1})
    empty = client.get('/api/scores', params={'worker_id': 2}).json()
    assert empty['total'] == 0 and empty['events'] == []
    assert next(s for s in empty['streaks'] if s['kind'] == 'participation')['days'] == 0
    assert not any(day['recorded'] for day in empty['history'])
    client.post('/api/reports', params={'worker_id': 2})
    client.post('/api/reports', params={'worker_id': 2})
    own = client.get('/api/scores', params={'worker_id': 2}).json()
    assert own['total'] == 10
    assert len(own['events']) == 2
    assert all(event['worker_id'] == 2 for event in own['events'])
    assert next(s for s in own['streaks'] if s['kind'] == 'participation')['days'] == 1
    assert own['history'][-1]['recorded']
    assert client.get('/api/scores').json()['total'] == 5


@pytest.mark.parametrize('answer', [None, False, True])
def test_closeout_preserves_unknown_no_and_yes_separately(client, answer):
    task = make_task(client)
    payload = {'task_id': task['id']}
    if answer is not None:
        payload.update(ppe_worn=answer, understood=answer)
    response = client.post('/api/worker-forms', json=payload)
    assert response.status_code == 201
    saved = client.get('/api/worker-forms', params={'task_id': task['id']}).json()[0]
    assert saved['ppe_worn'] is answer
    assert saved['understood'] is answer


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


def test_worker_submission_is_attributed_for_manager_and_training_is_saved(client):
    task = make_task(client)
    form = client.post('/api/worker-forms', json={
        'task_id': task['id'], 'understood': True, 'ppe_worn': True,
        'report_text': '보호구를 착용하고 작업을 마쳤습니다.', 'worker_id': 2,
    })
    assert form.status_code == 201
    submitted = client.get('/api/worker-forms').json()[0]
    assert submitted['worker_id'] == 2
    assert submitted['worker_name'] == '김OO'
    training = client.post('/api/training-reports', json={
        'worker_id': 2, 'course': '오늘 작업 전 안전교육', 'understood': True,
    })
    assert training.status_code == 201
    assert client.get('/api/training-reports', params={'worker_id': 2}).json()[0]['worker_name'] == '김OO'


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
