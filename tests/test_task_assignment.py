from fastapi.testclient import TestClient

from app.main import create_app


def test_assignment_persists_and_filters_calendar_tasks(tmp_path):
    with TestClient(create_app(str(tmp_path / 'tasks.db'), str(tmp_path / 'uploads'))) as client:
        task = client.post('/api/tasks', json={
            'text': '2층 용접 작업', 'worker_id': None, 'close_requested': False,
        }).json()
        assert task['worker_id'] is None
        assert task['close_requested'] is False
        workers = client.get('/api/tasks/workers').json()
        worker = workers[0]
        assert all(row['id'] != 1 for row in workers)
        assert client.patch(f"/api/tasks/{task['id']}/assignment", json={'worker_id': 999}).status_code == 422
        assert client.patch(f"/api/tasks/{task['id']}/assignment", json={'worker_id': 1}).status_code == 422
        response = client.patch(f"/api/tasks/{task['id']}/assignment", json={'worker_id': worker['id']})
        assert response.status_code == 200
        saved = client.get(f"/api/tasks/{task['id']}").json()
        assert saved['worker_name'] == worker['name']
        assert saved['created_at']
        assert client.get('/api/tasks', params={'worker_id': worker['id']}).json() == [saved]
        assert client.get('/api/tasks', params={'worker_id': 999}).json() == []
        assert client.get('/api/tasks').json() == [saved]
