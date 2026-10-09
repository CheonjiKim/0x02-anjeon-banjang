from fastapi.testclient import TestClient

from app.main import create_app


def test_jsa_draft_uses_worker_report_and_can_be_edited(tmp_path):
    with TestClient(create_app(str(tmp_path / 'jsa.db'), str(tmp_path / 'uploads'))) as client:
        assert client.post('/api/jsas/draft').status_code == 409
        task = client.post('/api/tasks', json={
            'text': '2층에서 용접 작업, 주변에 합판', 'worker_id': 2,
        }).json()
        report = client.post('/api/worker-forms', json={
            'task_id': task['id'], 'worker_id': 2,
            'report_text': '용접 작업과 정리를 마쳤습니다.',
            'risk_note': '통로에 자재가 남아 있습니다.',
        })
        assert report.status_code == 201

        draft_response = client.post('/api/jsas/draft')
        assert draft_response.status_code == 200
        draft = draft_response.json()
        assert draft['id'] is None
        assert draft['task_id'] == task['id']
        assert '용접 작업과 정리를 마쳤습니다.' in draft['worker_inputs']
        assert '통로에 자재가 남아 있습니다.' in draft['hazards']
        assert '작업자 첨부 사진 0장' in draft['photo_summary']

        draft['title'] = '관리자 수정 JSA'
        created = client.post('/api/jsas', json=draft)
        assert created.status_code == 201
        saved = created.json()
        assert saved['title'] == '관리자 수정 JSA'
        saved['measures'] = '통로 자재를 제거하고 용접 감시자를 배치한다.'
        updated = client.patch(f"/api/jsas/{saved['id']}", json=saved)
        assert updated.status_code == 200
        assert updated.json()['measures'].startswith('통로 자재')
        assert client.get('/api/jsas').json()[0]['id'] == saved['id']
