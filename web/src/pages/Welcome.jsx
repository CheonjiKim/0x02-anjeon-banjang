import { Camera, ClipboardCheck, HardHat } from 'lucide-react';
import { AppButton, LegalNote, STROKE } from '../components/ui.jsx';

export default function Welcome({ onStart }) {
  return (
    <main className="app-bg flex min-h-dvh flex-col items-center justify-center px-[22px] py-safe-8 text-center">
      <div aria-hidden="true" className="mb-10 flex gap-3">
        {['bg-brand-primary', 'bg-ok', 'bg-warn-fill', 'bg-review', 'bg-danger'].map((color) => <span key={color} className={`h-2.5 w-2.5 rounded-full ${color}`} />)}
      </div>
      <img src="/icon.svg" alt="안전반장" className="h-40 w-40 rounded-[40px] shadow-cta" />
      <div aria-hidden="true" className="my-8 flex gap-4">
        {[HardHat, Camera, ClipboardCheck].map((Icon, index) => (
          <div key={index} className={`flex h-16 w-16 items-center justify-center rounded-[20px] bg-white shadow-card ${index === 1 ? 'rotate-6' : '-rotate-6'} ${index === 2 ? 'text-ok' : 'text-brand-primary'}`}>
            <Icon size={30} strokeWidth={STROKE} />
          </div>
        ))}
      </div>
      <h1 className="text-[26px] font-extrabold leading-snug">작업 전 안전 점검,<br />사진으로 끝내세요</h1>
      <p className="mt-4 max-w-xs text-ink-sub">작업을 입력하면 AI가 체크리스트를 만들고, 사진으로 확인해 드려요.</p>
      <AppButton big className="mt-9 w-full" onClick={onStart}>시작하기 →</AppButton>
      <LegalNote />
    </main>
  );
}
