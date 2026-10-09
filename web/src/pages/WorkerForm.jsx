import { useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import { readSession } from '../lib/session.js';
import { api, post } from '../lib/api.js';
import { AppButton, Panel, Screen } from '../components/ui.jsx';

export default function WorkerForm() {
  const { taskId: routeTaskId } = useParams();
  const taskId = routeTaskId || (() => { try { return localStorage.getItem('banjang.taskId'); } catch { return null; } })();
  const [reportText, setReportText] = useState('');
  const [riskNote, setRiskNote] = useState('');
  const [photo, setPhoto] = useState(null);
  const [message, setMessage] = useState('');
  const [task, setTask] = useState(null);
  const [tbm, setTbm] = useState(null);
  const [loadError, setLoadError] = useState('');
  const [pending, setPending] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [savedFormId, setSavedFormId] = useState(null);
  const submitting = useRef(false);

  useEffect(() => {
    let active = true;
    setTask(null); setTbm(null); setLoadError('');
    setSavedFormId(null); setSubmitted(false); setMessage('');
    setReportText(''); setRiskNote(''); setPhoto(null);
    if (taskId) Promise.all([
      api('/tasks/' + taskId),
      api('/tbm/latest?task_id=' + taskId).catch(error => error.status === 404 ? null : Promise.reject(error)),
    ]).then(([savedTask, latestTbm]) => {
      if (active) { setTask(savedTask); setTbm(latestTbm); }
    }).catch(error => { if (active) setLoadError(error.message); });
    return () => { active = false; };
  }, [taskId]);

  async function submit(event) {
    event.preventDefault();
    if (submitting.current || submitted || !task || loadError) return;
    submitting.current = true; setPending(true); setMessage('');
    let formId = savedFormId;
    try {
      if (!formId) {
        const form = await post('/worker-forms', {
          task_id: Number(taskId), report_text: reportText, risk_note: riskNote,
          ppe_worn: null, understood: null, worker_id: readSession()?.worker_id || 2,
        });
        formId = form.id;
        setSavedFormId(formId);
      }
      if (photo) {
        const body = new FormData(); body.append('photo', photo);
        await api('/worker-forms/' + formId + '/photo', { method: 'POST', body });
      }
      setSubmitted(true);
      setMessage('마감 보고를 제출했습니다. 관리자 검토함에서 확인할 수 있습니다.');
    } catch (error) {
      setMessage(formId ? '보고 내용은 저장됐지만 사진 첨부에 실패했습니다. 사진만 다시 제출해 주세요. ' + error.message : error.message);
    } finally { submitting.current = false; setPending(false); }
  }

  if (!taskId) return <Screen title="오늘 작업"><Panel><p className="font-bold">관리자가 먼저 오늘 작업을 등록해야 합니다</p><p className="mt-2 text-sm text-ink-sub">관리자가 작업을 등록한 뒤 다시 출근해 주세요.</p></Panel></Screen>;
  return <Screen title="오늘 작업"><div className="space-y-4">
    <Panel><b>오늘 작업</b><p className="mt-2 text-ink-sub">{task?.text || '작업 내용을 불러오는 중입니다.'}</p></Panel>
    <Panel><b>관리자 TBM 내용</b>{tbm ? <><p className="mt-2 whitespace-pre-wrap text-ink">{tbm.transcript}</p>{tbm.memo && <p className="mt-3 text-sm text-ink-sub">메모: {tbm.memo}</p>}</> : <p className="mt-2 text-sm text-warn">저장된 TBM이 없습니다. 관리자에게 확인해 주세요.</p>}</Panel>
    <Panel><b>오늘 확인할 필수 안전 수칙</b>{task?.checklist?.filter(item => item.level === 'required').map(item => <p key={item.code} className="mt-2 text-sm">• {item.title}</p>)}{tbm?.missing?.length > 0 && <div className="mt-3 rounded-xl bg-warn-soft p-3 text-sm"><b>TBM에서 누락된 필수 수칙</b>{tbm.missing.map(item => <p key={item.code} className="mt-1">• {item.title}</p>)}</div>}</Panel>
    {loadError && <p role="alert" className="mx-[22px] text-danger">{loadError}</p>}
    <form onSubmit={submit}>
      <Panel><b>마감 보고</b><p className="mt-2 text-sm text-ink-sub">이 보고만으로 보호구 착용이나 수칙 이해를 확인 처리하지 않습니다.</p>
        <fieldset disabled={pending || submitted || !!savedFormId}>
          <label className="mt-4 block">오늘 작업 내용<textarea value={reportText} onChange={event => setReportText(event.target.value)} className="mt-2 min-h-24 w-full rounded-2xl border border-line p-3" /></label>
          <label className="mt-4 block">위험하거나 확인이 필요한 점<textarea value={riskNote} onChange={event => setRiskNote(event.target.value)} className="mt-2 min-h-24 w-full rounded-2xl border border-line p-3" /></label>
        </fieldset>
        <label className="mt-4 block">사진 첨부 (선택)<input disabled={pending || submitted} type="file" accept="image/*" onChange={event => setPhoto(event.target.files?.[0] || null)} className="mt-2 block w-full" /></label>
      </Panel>
      <div className="mx-[22px] mt-5"><AppButton big className="w-full" disabled={pending || submitted || !task || !!loadError}>{pending ? '제출 중…' : submitted ? '마감 보고 제출 완료' : savedFormId ? '사진 첨부 다시 시도' : '마감 보고 제출'}</AppButton></div>
      {message && <p role="status" className="mx-[22px] mt-3 text-center text-ink-sub">{message}</p>}
    </form>
  </div></Screen>;
}