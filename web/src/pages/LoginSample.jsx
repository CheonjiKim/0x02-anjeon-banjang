import { useState } from 'react';
import { HardHat, ShieldCheck, UsersRound } from 'lucide-react';
import { AppButton, LegalNote, Panel, STROKE } from '../components/ui.jsx';

const roles = {
  foreman: {
    label: '관리자 · 반장',
    description: '오늘 작업을 등록하고, 사진 증빙·할 일·점수 기록을 관리해요.',
    Icon: ShieldCheck,
    className: 'border-brand-primary bg-brand-soft text-brand-dark',
  },
  worker: {
    label: '근로자',
    description: '작업 내용을 확인하고, 보호구 착용과 위험 의견을 제출해요.',
    Icon: HardHat,
    className: 'border-ok bg-ok-soft text-ok',
  },
};

export default function LoginSample() {
  const [role, setRole] = useState('foreman');
  const [notice, setNotice] = useState('');
  const selected = roles[role];

  function submit(event) {
    event.preventDefault();
    setNotice(`${selected.label} 로그인은 데모 화면입니다.`);
  }

  return (
    <main className="app-bg flex min-h-dvh flex-col px-[22px] py-safe-8">
      <div className="pt-8 text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-[22px] bg-brand-primary text-white shadow-cta">
          <UsersRound size={30} strokeWidth={STROKE} aria-hidden="true" />
        </div>
        <p className="mt-6 text-sm font-bold text-brand-primary">안전반장 로그인</p>
        <h1 className="mt-2 text-[26px] font-extrabold">어떤 역할로 사용하나요?</h1>
        <p className="mt-3 text-ink-sub">역할에 따라 필요한 화면만 간단하게 보여 드려요.</p>
      </div>

      <form className="mt-8 space-y-4" onSubmit={submit}>
        <div className="grid gap-3" role="radiogroup" aria-label="사용자 역할">
          {Object.entries(roles).map(([key, item]) => {
            const Icon = item.Icon;
            const active = role === key;
            return (
              <button key={key} type="button" role="radio" aria-checked={active} onClick={() => setRole(key)}
                className={`flex min-h-28 items-center gap-4 rounded-[20px] border-2 p-5 text-left transition ${active ? item.className : 'border-line bg-white text-ink'}`}>
                <span className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl ${active ? 'bg-white/80' : 'bg-gray-100 text-ink-sub'}`}>
                  <Icon size={25} strokeWidth={STROKE} aria-hidden="true" />
                </span>
                <span><strong className="block text-[18px]">{item.label}</strong><span className="mt-1 block text-[15px] leading-snug text-ink-sub">{item.description}</span></span>
              </button>
            );
          })}
        </div>

        <Panel className="!mx-0 !p-5">
          <label className="block text-[15px] font-bold" htmlFor="name">이름</label>
          <input id="name" className="mt-2 h-14 w-full rounded-2xl border border-line bg-white px-4" placeholder="예) 김안전" />
          <label className="mt-4 block text-[15px] font-bold" htmlFor="site">현장</label>
          <select id="site" className="mt-2 h-14 w-full rounded-2xl border border-line bg-white px-4" defaultValue="basic">
            <option value="basic">기본 현장</option>
            <option value="sample">시연 현장</option>
          </select>
        </Panel>

        {notice && <p role="status" className="rounded-2xl bg-review-soft px-4 py-3 text-center text-[15px] font-bold text-review">{notice}</p>}
        <AppButton big className="w-full">{selected.label}으로 로그인</AppButton>
      </form>
      <LegalNote />
    </main>
  );
}
