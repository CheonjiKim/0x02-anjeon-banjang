export async function api(path, options = {}) {
  const request = { ...options };
  if (!(request.body instanceof FormData)) {
    request.headers = { ...request.headers, 'Content-Type': 'application/json' };
  }
  const response = await fetch('/api' + path, request);
  if (!response.ok) {
    const payload = typeof response.json === 'function' ? await response.json().catch(() => ({})) : {};
    const error = new Error(payload.detail || `${response.status} ${path}`);
    error.status = response.status;
    throw error;
  }
  return response.json();
}

export function post(path, body) {
  return api(path, { method: 'POST', body: JSON.stringify(body) });
}

export function patch(path, body) {
  return api(path, { method: 'PATCH', body: JSON.stringify(body) });
}

export async function transcribe(blob) {
  const form = new FormData();
  form.append('audio', blob, 'recording.webm');
  return api('/transcriptions', { method: 'POST', body: form });
}
