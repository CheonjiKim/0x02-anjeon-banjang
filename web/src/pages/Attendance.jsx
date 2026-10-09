import { Clock3 } from 'lucide-react';
import { readSession, formatClockedInAt } from '../lib/session.js';
import { Panel, Screen } from '../components/ui.jsx';

export default function Attendance() {
  const user = readSession();
  return <Screen title="출퇴근 기록"><Panel><div className="flex items-center gap-3"><span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-soft text-brand-primary"><Clock3 /></span><div><b>오늘 출근</b><p className="mt-1 text-sm text-ink-sub">{formatClockedInAt(user?.clockedInAt) || '기록 없음'}</p></div></div><p className="mt-5 rounded-xl bg-gray-50 p-3 text-sm text-ink-sub">퇴근 버튼을 누르면 오늘 업무를 마감하고 로그인 화면으로 돌아갑니다.</p></Panel></Screen>;
}
