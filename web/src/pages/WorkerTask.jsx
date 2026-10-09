import { useEffect, useState } from 'react';
import { CheckCircle2, ClipboardCheck } from 'lucide-react';
import { api } from '../lib/api.js';
import { readSession } from '../lib/session.js';
import { EmptyState, Panel, Screen, StatusBadge } from '../components/ui.jsx';

export default function WorkerTask() {
  const [task, setTask] = useState(undefined);
  const [error, setError] = useState('');
  useEffect(() => {
    const workerId = readSession()?.worker_id;
    api(`/tasks?worker_id=${workerId}`).then(tasks => setTask(tasks[0] || null)).catch(requestError => setError(requestError.message));
  }, []);
  if (error) return <Screen title="오늘 작업"><Panel><p role="alert" className="text-danger">{error}</p></Panel></Screen>;
  if (task === undefined) return <Screen title="오늘 작업"><EmptyState icon={ClipboardCheck} title="작업을 불러오는 중" /></Screen>;
  if (task === null) return <Screen title="오늘 작업"><EmptyState icon={ClipboardCheck} title="배정된 작업이 없습니다" hint="관리자가 체크리스트를 만들고 작업자를 지정하면 여기에 표시됩니다." /></Screen>;
  return <Screen title="오늘 작업">
    <Panel><p className="text-sm font-bold text-brand-primary">관리자가 배정한 작업</p><h2 className="mt-2 text-xl font-bold">{task.text}</h2><p className="mt-2 text-sm text-ink-sub">작업 종류: {task.conditions.work} · 작업자: {task.worker_name}</p></Panel>
    <Panel className="mt-4"><h2 className="flex items-center gap-2 text-lg font-bold"><CheckCircle2 className="text-brand-primary" />안전 체크리스트</h2>
      {task.checklist.length === 0 && <p className="mt-3 text-sm text-ink-sub">등록된 체크리스트 항목이 없습니다.</p>}
      {task.checklist.map(item => <div key={item.code} className="border-b border-line py-4 last:border-0"><div className="flex items-start justify-between gap-2"><b>{item.title}</b><StatusBadge kind={item.level} /></div>{item.note && <p className="mt-2 text-sm text-ink-sub">{item.note}</p>}</div>)}
    </Panel>
  </Screen>;
}
