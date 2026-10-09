"""웹 API 래퍼의 동작을 서버 없이 확인한다."""

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def test_api_wrapper_requests_and_errors():
    """JSON·사진 전송과 HTTP 오류를 서버 없이 확인한다."""
    result = subprocess.run(
        ["node", "--input-type=module", "-e", r'''
import assert from 'node:assert/strict';
import { api, post, patch } from './web/src/lib/api.js';
const calls = [];
globalThis.fetch = async (url, options) => {
  calls.push([url, options]);
  return { ok: true, json: async () => ({ id: 7 }) };
};
assert.deepEqual(await post('/tasks', { text: '용접' }), { id: 7 });
assert.equal(calls[0][0], '/api/tasks');
assert.equal(calls[0][1].method, 'POST');
assert.equal(calls[0][1].headers['Content-Type'], 'application/json');
assert.deepEqual(JSON.parse(calls[0][1].body), { text: '용접' });
await patch('/tasks/7/conditions', { ventilation: '양호' });
assert.equal(calls[1][1].method, 'PATCH');
assert.deepEqual(JSON.parse(calls[1][1].body), { ventilation: '양호' });
const body = new FormData();
body.append('task_id', '7');
await api('/evidence', { method: 'POST', body });
assert.equal(calls[2][1].body, body);
assert.equal(calls[2][1].headers, undefined);
globalThis.fetch = async () => ({ ok: false, status: 404 });
await assert.rejects(api('/tasks/404'), { message: '404 /tasks/404' });
'''],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
