export async function api(path, options = {}) {
  const request = { ...options };
  if (!(request.body instanceof FormData)) {
    request.headers = { ...request.headers, 'Content-Type': 'application/json' };
  }
  const response = await fetch('/api' + path, request);
  if (!response.ok) throw new Error(`${response.status} ${path}`);
  return response.json();
}

export function post(path, body) {
  return api(path, { method: 'POST', body: JSON.stringify(body) });
}

export function patch(path, body) {
  return api(path, { method: 'PATCH', body: JSON.stringify(body) });
}
