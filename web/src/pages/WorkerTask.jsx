import { useEffect, useState } from 'react';
import { Camera, CheckCircle2, ClipboardCheck } from 'lucide-react';
import { api } from '../lib/api.js';
import { readSession } from '../lib/session.js';
import { EmptyState, Panel, Screen, StatusBadge } from '../components/ui.jsx';

export default function WorkerTask() {
  const [task, setTask] = useState(undefined);
  const [error, setError] = useState('');
  const [evidence, setEvidence] = useState({});
  const [uploading, setUploading] = useState('');
  const [message, setMessage] = useState('');
  const workerId = readSession()?.worker_id;
  useEffect(() => {
    api(`/tasks?worker_id=${workerId}`).then(async tasks => {
      const assigned = tasks[0] || null;
      setTask(assigned);
      if (assigned) {
        const photos = await api(`/evidence/task/${assigned.id}?worker_id=${workerId}`);
        setEvidence(Object.fromEntries(photos.map(photo => [photo.item_code, photo])));
      }
    }).catch(requestError => setError(requestError.message));
  }, []);

  async function attach(item, photo) {
    if (!photo || uploading) return;
    setUploading(item.code); setMessage('');
    const body = new FormData();
    body.append('task_id', task.id); body.append('item_code', item.code);
    body.append('worker_id', workerId); body.append('photo', photo);
    try {
      const saved = await api('/evidence', { method: 'POST', body });
      setEvidence(current => ({ ...current, [item.code]: saved }));
      setMessage(`${item.title} 사진을 첨부했습니다.`);
    } catch (requestError) { setMessage(requestError.message); }
    finally { setUploading(''); }
  }
  if (error) return <Screen title="오늘 작업"><Panel><p role="alert" className="text-danger">{error}</p></Panel></Screen>;
  if (task === undefined) return <Screen title="오늘 작업"><EmptyState icon={ClipboardCheck} title="작업을 불러오는 중" /></Screen>;
  if (task === null) return <Screen title="오늘 작업"><EmptyState icon={ClipboardCheck} title="배정된 작업이 없습니다" hint="관리자가 체크리스트를 만들고 작업자를 지정하면 여기에 표시됩니다." /></Screen>;
  return <Screen title="오늘 작업">
    <Panel><p className="text-sm font-bold text-brand-primary">관리자가 배정한 작업</p><h2 className="mt-2 text-xl font-bold">{task.text}</h2><p className="mt-2 text-sm text-ink-sub">작업 종류: {task.conditions.work} · 작업자: {task.worker_name}</p></Panel>
    <Panel className="mt-4"><h2 className="flex items-center gap-2 text-lg font-bold"><CheckCircle2 className="text-brand-primary" />안전 체크리스트</h2>
      {task.checklist.length === 0 && <p className="mt-3 text-sm text-ink-sub">등록된 체크리스트 항목이 없습니다.</p>}
      {task.checklist.map(item => <div key={item.code} className="border-b border-line py-4 last:border-0"><div className="flex items-start justify-between gap-2"><b>{item.title}</b><div className="flex shrink-0 flex-col items-end gap-2"><StatusBadge kind={item.level} />{item.level === 'required' && <label className={`inline-flex min-h-11 cursor-pointer items-center gap-1 rounded-xl px-3 text-sm font-bold ${evidence[item.code] ? 'bg-ok-soft text-ok' : 'bg-brand-soft text-brand-primary'}`}>{evidence[item.code] ? <CheckCircle2 size={17} /> : <Camera size={17} />}{uploading === item.code ? '첨부 중…' : evidence[item.code] ? '사진 첨부 완료' : '사진 첨부하기'}<input type="file" accept="image/*" capture="environment" disabled={Boolean(uploading)} onChange={event => attach(item, event.target.files?.[0])} className="sr-only" /></label>}</div></div>{item.note && <p className="mt-2 text-sm text-ink-sub">{item.note}</p>}</div>)}
    </Panel>
    {message && <p role="status" className="mx-[22px] mt-3 text-sm font-bold text-brand-dark">{message}</p>}
  </Screen>;
}
