import { useEffect, useState } from 'react';
import { BookOpenCheck } from 'lucide-react';
import { api, post } from '../lib/api.js';
import { readSession } from '../lib/session.js';
import { AppButton, EmptyState, Panel, Screen } from '../components/ui.jsx';

export default function Training() {
  const workerId = readSession()?.worker_id || 2;
  const [course, setCourse] = useState('오늘 작업 전 안전교육');
  const [understood, setUnderstood] = useState(false);
  const [items, setItems] = useState([]);
  const [message, setMessage] = useState('');
  const load = () => api(`/training-reports?worker_id=${workerId}`).then(setItems).catch((error) => setMessage(error.message));
  useEffect(() => { load(); }, []);
  async function submit(event) {
    event.preventDefault();
    try { await post('/training-reports', { worker_id: workerId, course, understood }); setMessage('교육 수강 여부를 제출했습니다.'); load(); }
    catch (error) { setMessage(error.message); }
  }
  return <Screen title="안전 교육"><form onSubmit={submit}><Panel><label className="block font-bold">교육 과정<input value={course} onChange={(e) => setCourse(e.target.value)} className="mt-2 h-14 w-full rounded-xl border border-line px-3" /></label><label className="mt-4 flex items-start gap-3"><input type="checkbox" checked={understood} onChange={(e) => setUnderstood(e.target.checked)} className="mt-1 h-5 w-5" /><span><b>교육 내용을 이해했습니다</b><small className="mt-1 block text-ink-sub">이해가 안 된 내용은 관리자에게 바로 질문해 주세요.</small></span></label><AppButton className="mt-4 w-full">수강 여부 제출</AppButton></Panel></form>{message && <p role="status" className="mx-[22px] mt-3 text-sm">{message}</p>}{items.length === 0 ? <EmptyState icon={BookOpenCheck} title="제출한 교육 기록이 없어요" /> : <Panel className="mt-4"><b>내 제출 기록</b>{items.map((item) => <p className="mt-3 border-t border-line pt-3 text-sm" key={item.id}>{item.course} · {item.understood ? '이해함' : '추가 설명 필요'}</p>)}</Panel>}</Screen>;
}
