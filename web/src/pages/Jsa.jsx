import { useEffect, useState } from 'react';
import { FileText, Sparkles } from 'lucide-react';
import { api } from '../lib/api.js';
import { AppButton, EmptyState, Panel, Screen } from '../components/ui.jsx';
import Modal from '../components/Modal.jsx';

const EMPTY = { title: '', work_summary: '', worker_inputs: '', hazards: '', measures: '', photo_summary: '' };

function formatDate(value) {
  if (!value) return '';
  return new Date(value.replace(' ', 'T')).toLocaleString('ko-KR', { month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

export default function Jsa() {
  const [items, setItems] = useState(null);
  const [draft, setDraft] = useState(null);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);

  const load = () => api('/jsas').then(setItems).catch(error => setMessage(error.message));
  useEffect(() => { load(); }, []);

  async function createDraft() {
    setBusy(true); setMessage('');
    try { setDraft(await api('/jsas/draft', { method: 'POST', body: '{}' })); }
    catch (error) { setMessage(error.message); }
    finally { setBusy(false); }
  }

  async function save() {
    setBusy(true); setMessage('');
    try {
      const path = draft.id ? `/jsas/${draft.id}` : '/jsas';
      const saved = await api(path, { method: draft.id ? 'PATCH' : 'POST', body: JSON.stringify(draft) });
      setDraft(null);
      setMessage(draft.id ? 'JSA 수정 내용을 저장했습니다.' : '오늘의 JSA를 저장했습니다.');
      await load();
      return saved;
    } catch (error) { setMessage(error.message); }
    finally { setBusy(false); }
  }

  function field(key, label, rows = 3) {
    return <label className="block text-sm font-bold">{label}<textarea rows={rows} value={draft[key] ?? EMPTY[key]} onChange={event => setDraft({ ...draft, [key]: event.target.value })} className="mt-1 w-full rounded-xl border border-line p-3 font-normal" /></label>;
  }

  return <Screen title="JSA">
    <Panel className="bg-brand-soft">
      <div className="flex items-start gap-3"><Sparkles className="mt-1 shrink-0 text-brand-primary" /><div><h2 className="text-lg font-bold">오늘의 JSA</h2><p className="mt-1 text-sm text-ink-sub">작업자 보고, 위험 메모, 안전 조치와 사진 판정 내용을 바탕으로 수정 가능한 초안을 만듭니다.</p></div></div>
      <AppButton className="mt-4 w-full" disabled={busy} onClick={createDraft}>{busy ? '초안 만드는 중…' : '오늘의 JSA 작성하기'}</AppButton>
    </Panel>
    {message && <p role="status" className="mx-[22px] mt-3 text-sm font-bold text-brand-dark">{message}</p>}
    <Panel className="mt-4"><h2 className="text-lg font-bold">지난 JSA</h2>
      {items === null && <p className="mt-3 text-sm text-ink-sub">JSA 기록을 불러오는 중입니다.</p>}
      {items?.length === 0 && <EmptyState icon={FileText} title="저장된 JSA가 없습니다" hint="오늘의 JSA 초안을 만들고 저장하면 여기에 표시됩니다." />}
      {items?.map(item => <button key={item.id} type="button" onClick={() => setDraft(item)} className="flex min-h-16 w-full items-center justify-between gap-3 border-b border-line py-4 text-left last:border-0"><span><b className="block">{item.title}</b><small className="mt-1 block text-ink-sub">{formatDate(item.updated_at)}</small></span><span className="shrink-0 text-sm font-bold text-brand-primary">보기·수정</span></button>)}
    </Panel>
    {draft && <Modal title={draft.id ? 'JSA 보기·수정' : 'AI JSA 초안'} onClose={() => setDraft(null)}><div className="space-y-4 px-5">
      <p className="rounded-xl bg-warn-soft p-3 text-sm">자동 생성된 초안입니다. 현장 상황과 안전 조치를 관리자가 확인하고 수정해 주세요.</p>
      <label className="block text-sm font-bold">JSA 제목<input value={draft.title} onChange={event => setDraft({ ...draft, title: event.target.value })} className="mt-1 min-h-11 w-full rounded-xl border border-line p-3 font-normal" /></label>
      {field('work_summary', '작업 내용')}
      {field('worker_inputs', '작업자 보고 내용', 4)}
      {field('hazards', '위험 요인', 5)}
      {field('measures', '안전 조치', 6)}
      {field('photo_summary', '사진·판정 요약')}
      <AppButton className="w-full" disabled={busy || !draft.title.trim() || !draft.work_summary.trim() || !draft.hazards.trim() || !draft.measures.trim()} onClick={save}>{busy ? '저장 중…' : draft.id ? '수정 내용 저장' : 'JSA 저장'}</AppButton>
    </div></Modal>}
  </Screen>;
}
