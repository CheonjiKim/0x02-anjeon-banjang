import { LogOut } from 'lucide-react';
import { formatClockedInAt } from '../lib/session.js';

export default function SessionHeader({ user, onClockOut }) {
  return (
    <header className="app-bg flex shrink-0 items-center justify-between border-b border-line/70 px-[22px] py-3">
      <div>
        <p className="text-sm font-extrabold text-ink">{user.name} <span className="font-medium text-ink-sub">· {user.role === 'admin' ? '관리자' : '근로자'}</span></p>
        <p className="mt-0.5 text-xs text-ink-sub">{formatClockedInAt(user.clockedInAt)}</p>
      </div>
      <button type="button" onClick={onClockOut} className="inline-flex min-h-11 items-center gap-1.5 rounded-xl border border-line bg-white px-3 text-sm font-bold text-ink">
        <LogOut size={17} aria-hidden="true" />퇴근하기
      </button>
    </header>
  );
}
