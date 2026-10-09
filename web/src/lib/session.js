const SESSION_KEY = 'banjang.user';

const demoUsers = {
  admin: { password: '1234', role: 'admin', name: '김반장' },
  worker: { password: '1234', role: 'worker', name: '김작업' },
};

export function signIn(loginId, password) {
  const account = demoUsers[loginId];
  if (!account || account.password !== password) return null;
  return { role: account.role, name: account.name, clockedInAt: new Date().toISOString() };
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
