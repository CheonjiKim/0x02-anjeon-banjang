import { useState } from 'react';
import { UsersRound } from 'lucide-react';
import { AppButton, LegalNote, Panel, STROKE } from '../components/ui.jsx';
import { signIn } from '../lib/session.js';

export default function LoginSample({ onLogin }) {
  const [loginId, setLoginId] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [pending, setPending] = useState(false);
  async function submit(event) {
    event.preventDefault();
    if (!loginId.trim() || !password) return setError('아이디와 비밀번호를 입력해 주세요.');
    setPending(true); setError('');
    try {
      const user = await signIn(loginId.trim(), password);
      if (!user) setError('아이디 또는 비밀번호를 다시 확인해 주세요.');
      else onLogin(user);
    } finally { setPending(false); }
  }
  return <main className="app-bg flex min-h-dvh flex-col px-[22px] py-safe-8">
    <div className="pt-12 text-center"><div className="mx-auto flex h-16 w-16 items-center justify-center rounded-[22px] bg-brand-primary text-white shadow-cta"><UsersRound size={30} strokeWidth={STROKE} /></div><p className="mt-6 text-sm font-bold text-brand-primary">안전반장</p><h1 className="mt-2 text-[26px] font-extrabold">로그인</h1><p className="mt-3 text-ink-sub">등록된 계정으로 로그인해 주세요.</p></div>
    <form className="mt-10 space-y-4" onSubmit={submit}><Panel className="!mx-0 !p-5"><label className="block text-[15px] font-bold" htmlFor="loginId">아이디</label><input id="loginId" value={loginId} onChange={(event) => setLoginId(event.target.value)} className="mt-2 h-14 w-full rounded-2xl border border-line bg-white px-4" autoComplete="username" /><label className="mt-4 block text-[15px] font-bold" htmlFor="password">비밀번호</label><input id="password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} className="mt-2 h-14 w-full rounded-2xl border border-line bg-white px-4" autoComplete="current-password" /></Panel>{error && <p role="alert" className="rounded-2xl bg-danger-soft px-4 py-3 text-center text-[15px] font-bold text-danger">{error}</p>}<AppButton big className="w-full" disabled={pending}>{pending ? '로그인 중…' : '로그인'}</AppButton></form>
    <LegalNote />
  </main>;
}
