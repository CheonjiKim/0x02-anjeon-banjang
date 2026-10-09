from fastapi.testclient import TestClient

from app.main import create_app


def test_assigned_worker_photo_marks_checklist_item_attached(tmp_path):
    with TestClient(create_app(str(tmp_path / 'worker.db'), str(tmp_path / 'uploads'))) as client:
        task = client.post('/api/tasks', json={'text': '2m 옆 합판 용접', 'worker_id': 2}).json()
        code = next(item['code'] for item in task['checklist'] if item['level'] == 'required')
        assert client.get(f"/api/evidence/task/{task['id']}", params={'worker_id': 3}).status_code == 403
        saved = client.post('/api/evidence', data={
            'task_id': task['id'], 'item_code': code, 'worker_id': 2,
        }, files={'photo': ('check.jpg', b'photo', 'image/jpeg')})
        assert saved.status_code == 201
        updated_task = client.get(f"/api/tasks/{task['id']}").json()
        assert next(item for item in updated_task['checklist'] if item['code'] == code)['attached'] is True
        assert next(item for item in updated_task['checklist'] if item['code'] == code)['resolved'] is False
        attached = client.get(f"/api/evidence/task/{task['id']}", params={'worker_id': 2}).json()
        assert attached[0]['item_code'] == code
        assert attached[0]['photo_url'].startswith('/api/uploads/')


def test_admin_worker_ranking_excludes_foreman_and_matches_personal_score(tmp_path):
    with TestClient(create_app(str(tmp_path / 'score.db'), str(tmp_path / 'uploads'))) as client:
        client.post('/api/incidents', json={'worker_id': 1, 'note': '반장 기록'})
        client.post('/api/incidents', json={'worker_id': 2, 'note': '근로자 기록'})
        worker_scores = client.get('/api/scores', params={'worker_id': 2}).json()
        admin_scores = client.get('/api/scores').json()
        assert worker_scores['total'] == 5
        assert admin_scores['worker_ranking'] == [{'name': '김OO', 'score': 5, 'me': False}]
