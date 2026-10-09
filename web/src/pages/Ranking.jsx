import { useEffect, useState } from 'react';
import { CalendarDays, CircleCheck, Trophy } from 'lucide-react';
import { api } from '../lib/api.js';
import { readSession } from '../lib/session.js';
import { EmptyState, Panel, Screen } from '../components/ui.jsx';

const EVENT_LABELS = { evidence: '사진 증빙 확인', report: '위험 신고', tbm: 'TBM 기록' };

function formatDate(value) {
  if (!value) return '';
  const date = new Date(value.replace(' ', 'T'));
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('ko-KR', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

export default function Ranking() {
  const [scores, setScores] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => { const workerId = readSession()?.worker_id; api('/scores' + (workerId ? `?worker_id=${workerId}` : '')).then(setScores).catch((requestError) => setError(requestError.message)); }, []);
  if (error) return <Screen title="내 기록"><Panel><p className="text-danger">{error}</p></Panel></Screen>;
  if (!scores) return <Screen title="내 기록"><EmptyState icon={Trophy} title="기록을 불러오는 중" /></Screen>;

  if (readSession()?.role === 'admin') return <Screen title="기록"><Panel>
    {scores.worker_ranking.filter(row => row.score > 0).length === 0 && <p>아직 점수를 받은 작업자가 없습니다.</p>}
    {scores.worker_ranking.filter(row => row.score > 0).map((row, index) => <div key={index} className="flex items-center justify-between border-b border-line py-4 last:border-0"><b>{row.name}</b><strong className="text-brand-primary">{row.score}점</strong></div>)}
  </Panel></Screen>;
  const participation = scores.streaks.find((streak) => streak.kind === 'participation');
  return (
    <Screen title="내 기록">
      <Panel className="bg-brand-primary text-white">
        <p className="text-sm text-blue-100">내 안전 활동 점수</p>
        <p className="mt-1 text-5xl font-extrabold tnum">{scores.total}<span className="ml-1 text-xl">점</span></p>
        <p className="mt-3 flex items-center gap-2 text-sm text-blue-100"><CircleCheck size={17} />AI 또는 관리자 확인을 거친 활동만 반영됩니다.</p>
      </Panel>
      <Panel className="mt-4">
        <div className="flex items-center gap-3"><span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-ok-soft text-ok"><CalendarDays /></span><div><p className="font-bold">참여 연속 기록</p><p className="text-sm text-ink-sub">오늘 안전 활동을 이어 가고 있어요.</p></div></div>
        <p className="mt-4 text-3xl font-extrabold text-ok tnum">{participation?.days || 0}<span className="ml-1 text-lg">일</span></p>
      </Panel>
      <Panel className="mt-4">
        <h2 className="font-bold">최근 적립 내역</h2>
        {scores.events.length === 0 && <p className="mt-3 text-sm text-ink-sub">아직 적립된 활동이 없어요.</p>}
        {scores.events.map((event) => <div key={event.id} className="mt-3 flex items-center justify-between border-t border-line pt-3 first:mt-3">
          <div><p className="font-bold">{EVENT_LABELS[event.kind] || '안전 활동'}</p><p className="text-sm text-ink-sub">{formatDate(event.created_at)}</p></div>
          <strong className="text-ok tnum">+{event.points}점</strong>
        </div>)}
      </Panel>
    </Screen>
  );
}
