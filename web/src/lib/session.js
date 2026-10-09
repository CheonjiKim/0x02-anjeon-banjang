const SESSION_KEY = 'banjang.user';

const demoUsers = {
  admin: { password: '1234', role: 'admin', name: '김반장' },
  worker: { password: '1234', role: 'worker', name: '김작업' },
};

export async function signIn(loginId, password) {
  const account = demoUsers[loginId];
  if (!account || account.password !== password) return null;
  try {
    const response = await fetch('/api/login', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ login_id: loginId, password }),
    });
    if (response.ok) {
      const user = await response.json();
      return { ...user, clockedInAt: new Date().toISOString() };
    }
  } catch { /* 개발 서버 없이 로그인 화면을 시연할 때는 고정 계정을 사용한다. */ }
  return { role: account.role, name: account.name, worker_id: account.role === 'worker' ? 2 : null, clockedInAt: new Date().toISOString() };
}

export function readSession() {
  try {
    const session = JSON.parse(localStorage.getItem(SESSION_KEY) || 'null');
    return session?.role && session?.name && session?.clockedInAt ? session : null;
  } catch {
    return null;
  }
}

export function saveSession(session) {
  try { localStorage.setItem(SESSION_KEY, JSON.stringify(session)); } catch { /* 저장소 제한 환경 */ }
}

export function clearSession() {
  try { localStorage.removeItem(SESSION_KEY); } catch { /* 저장소 제한 환경 */ }
}

export function formatClockedInAt(isoTime) {
  const date = new Date(isoTime);
  if (Number.isNaN(date.getTime())) return '';
  const pad = (value) => String(value).padStart(2, '0');
  return `출근 ${date.getFullYear()}.${pad(date.getMonth() + 1)}.${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}
