import { useEffect, useRef, useState } from 'react';
import { Camera, CircleCheck, Clock3, ImagePlus } from 'lucide-react';
import { api, post } from '../lib/api.js';
import { readSession } from '../lib/session.js';
import { AppButton, EmptyState, Panel, Screen } from '../components/ui.jsx';

function formatDate(value) {
  if (!value) return '';
  const date = new Date(String(value).replace(' ', 'T'));
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString('ko-KR', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

export default function WorkerReports() {
  const workerId = readSession()?.worker_id || 2;
  const inputRef = useRef(null);
  const [photo, setPhoto] = useState(null);
  const [note, setNote] = useState('');
  const [items, setItems] = useState(null);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const load = () => api(`/incidents?worker_id=${workerId}`).then(setItems).catch(error => setMessage(error.message));
  useEffect(() => { load(); }, []);

  async function submit(event) {
    event.preventDefault();
    if (!note.trim() || busy) return;
    if (!photo) { setMessage('위험 요소를 확인할 수 있는 사진을 첨부해 주세요.'); return; }
    setBusy(true); setMessage('');
    try {
      const report = await post('/incidents', { note: note.trim(), worker_id: workerId });
      const body = new FormData(); body.append('photo', photo);
      await api(`/incidents/${report.id}/photo`, { method: 'POST', body });
      setNote(''); setPhoto(null);
      if (inputRef.current) inputRef.current.value = '';
      setMessage('위험 요소를 신고했습니다. 조치 상태를 목록에서 확인할 수 있습니다.');
      await load();
    } catch (error) { setMessage(error.message); }
    finally { setBusy(false); }
  }

  return <Screen title="사진"><form onSubmit={submit}><Panel>
    <h2 className="text-lg font-bold">작업 중 위험 요소 신고</h2><p className="mt-2 text-sm text-ink-sub">위험해 보이는 곳의 사진과 필요한 조치를 설명해 주세요.</p>
    <label className="mt-4 flex min-h-14 cursor-pointer items-center justify-center gap-2 rounded-2xl border-2 border-dashed border-brand-primary bg-brand-soft font-bold text-brand-primary"><ImagePlus />{photo ? photo.name : '사진 첨부하기'}<input ref={inputRef} type="file" accept="image/*" capture="environment" onChange={event => setPhoto(event.target.files?.[0] || null)} className="sr-only" /></label>
    <label className="mt-4 block font-bold">위험 요소와 바라는 조치<textarea value={note} onChange={event => setNote(event.target.value)} placeholder="예: 통로에 자재가 쌓여 있습니다. 이동 조치가 필요합니다." className="mt-2 min-h-28 w-full rounded-2xl border border-line p-3 font-normal" /></label>
    <AppButton className="mt-4 w-full" disabled={!note.trim() || busy}>{busy ? '제출 중…' : '제출하기'}</AppButton>
  </Panel></form>
  {message && <p role="status" className="mx-[22px] mt-3 text-sm font-bold text-brand-dark">{message}</p>}
  <Panel className="mt-4"><h2 className="text-lg font-bold">제출한 신고 목록</h2>
    {items === null && <p className="mt-3 text-sm text-ink-sub">신고 목록을 불러오는 중입니다.</p>}
    {items?.length === 0 && <EmptyState icon={Camera} title="제출한 신고가 없습니다" />}
    {items?.map(item => <article key={item.id} className="border-b border-line py-4 last:border-0">{item.photo_url && <img src={item.photo_url} alt="신고한 위험 요소" className="mb-3 h-40 w-full rounded-xl object-cover" />}<div className="flex items-start justify-between gap-3"><div><p className="font-bold">{item.note}</p><p className="mt-1 text-xs text-ink-sub">{formatDate(item.created_at)}</p></div><span className={`inline-flex shrink-0 items-center gap-1 rounded-full px-3 py-1 text-sm font-bold ${item.status === 'completed' ? 'bg-ok-soft text-ok' : 'bg-warn-soft text-warn'}`}>{item.status === 'completed' ? <CircleCheck size={15} /> : <Clock3 size={15} />}{item.status === 'completed' ? '조치 완료' : '조치중'}</span></div></article>)}
  </Panel></Screen>;
}
