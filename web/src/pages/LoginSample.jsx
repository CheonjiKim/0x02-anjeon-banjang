import { useState } from 'react';
import { LogIn, UsersRound } from 'lucide-react';
import { AppButton, LegalNote, Panel, STROKE } from '../components/ui.jsx';
import { signIn } from '../lib/session.js';

export default function LoginSample({ onLogin }) {
  const [loginId, setLoginId] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  function submit(event) {
    event.preventDefault();
    setError('');
    const user = signIn(loginId.trim(), password);
    if (!user) {
      setError('아이디 또는 비밀번호가 일치하지 않습니다. 다시 확인해 주세요.');
      return;
    }
    onLogin(user);
  }

  return (
    <main className="app-bg flex min-h-dvh flex-col px-[22px] py-safe-8">
      <div className="pt-8 text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-[22px] bg-brand-primary text-white shadow-cta">
          <UsersRound size={30} strokeWidth={STROKE} aria-hidden="true" />
        </div>
        <p className="mt-6 text-sm font-bold text-brand-primary">안전반장 로그인</p>
        <h1 className="mt-2 text-[26px] font-extrabold">출근을 시작해 주세요</h1>
        <p className="mt-3 text-ink-sub">입력한 계정에 따라 관리자 또는 근로자 화면으로 이동합니다.</p>
      </div>

      <form className="mt-8 space-y-4" onSubmit={submit}>
        <Panel className="!mx-0 !p-5">
          <label className="block text-[15px] font-bold" htmlFor="loginId">아이디</label>
          <input id="loginId" value={loginId} onChange={(event) => setLoginId(event.target.value)} className="mt-2 h-14 w-full rounded-2xl border border-line bg-white px-4" autoComplete="username" placeholder="아이디를 입력해 주세요" />
          <label className="mt-4 block text-[15px] font-bold" htmlFor="password">비밀번호</label>
          <input id="password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} className="mt-2 h-14 w-full rounded-2xl border border-line bg-white px-4" autoComplete="current-password" placeholder="비밀번호를 입력해 주세요" />
          <p className="mt-3 text-[14px] text-ink-sub">시연 계정: 관리자 admin / 1234 · 근로자 worker / 1234</p>
        </Panel>

        {error && <p role="alert" className="rounded-2xl bg-danger-soft px-4 py-3 text-center text-[15px] font-bold text-danger">{error}</p>}
        <AppButton big className="w-full"><LogIn className="mr-2 inline" size={20} />출근하기</AppButton>
      </form>
      <LegalNote />
    </main>
  );
}
