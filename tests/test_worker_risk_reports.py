from fastapi.testclient import TestClient

from app.main import create_app


def test_worker_risk_report_photo_and_status(tmp_path):
    uploads = tmp_path / 'uploads'
    with TestClient(create_app(str(tmp_path / 'reports.db'), str(uploads))) as client:
        created = client.post('/api/incidents', json={
            'worker_id': 2, 'note': '통로에 자재가 쌓여 있습니다.',
        })
        assert created.status_code == 201
        report_id = created.json()['id']
        uploaded = client.post(
            f'/api/incidents/{report_id}/photo',
            files={'photo': ('risk.jpg', b'photo-bytes', 'image/jpeg')},
        )
        assert uploaded.status_code == 200
        assert uploaded.json()['photo_url'].endswith(f'incident-{report_id}.jpg')

        report = client.get('/api/incidents', params={'worker_id': 2}).json()[0]
        assert report['note'] == '통로에 자재가 쌓여 있습니다.'
        assert report['status'] == 'in_progress'
        assert report['photo_url'] == uploaded.json()['photo_url']
        assert report['worker_name'] == '김OO'

        assert client.post(f'/api/incidents/{report_id}/follow-up').status_code == 200
        completed = client.get('/api/incidents', params={'worker_id': 2}).json()[0]
        assert completed['status'] == 'completed'
