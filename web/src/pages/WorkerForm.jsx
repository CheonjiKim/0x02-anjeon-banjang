import { useEffect, useRef, useState } from 'react';
import { Camera, LogOut } from 'lucide-react';
import { useParams } from 'react-router-dom';
import { api, post } from '../lib/api.js';
import { AppButton, Panel, Screen } from '../components/ui.jsx';

export default function WorkerForm({ onClockOut }) {
  const { taskId } = useParams();
  const photoInputRef = useRef(null);
  const [reportText, setReportText] = useState('');
  const [riskNote, setRiskNote] = useState('');
  const [photo, setPhoto] = useState(null);
  const [message, setMessage] = useState('');
  const [task, setTask] = useState(null);
  const [tbm, setTbm] = useState(null);
  const [loadError, setLoadError] = useState('');
  const clockOutButton = onClockOut && (
    <button type="button" onClick={onClockOut} className="inline-flex min-h-11 items-center gap-1.5 rounded-xl border border-line bg-white px-3 text-sm font-bold text-ink">
      <LogOut size={17} aria-hidden="true" />퇴근하기
    </button>
  );

  useEffect(() => {
    if (taskId === 'missing') return;
    Promise.all([
      api('/tasks/' + taskId),
      api('/tbm/latest?task_id=' + taskId).catch((error) => error.status === 404 ? null : Promise.reject(error)),
    ]).then(([savedTask, latestTbm]) => {
      setTask(savedTask);
      setTbm(latestTbm);
    }).catch((error) => setLoadError(error.message));
  }, [taskId]);

  async function submit(event) {
    event.preventDefault();
    try {
      const form = await post('/worker-forms', { task_id: Number(taskId), report_text: reportText, risk_note: riskNote, ppe_worn: true });
      if (photo) {
        const body = new FormData();
        body.append('photo', photo);
        await api('/worker-forms/' + form.id + '/photo', { method: 'POST', body });
      }
      setMessage('마감 보고를 제출했습니다.');
    } catch (error) {
      setMessage(error.message);
    }
  }

  if (taskId === 'missing') {
    return <Screen title="오늘 작업" right={clockOutButton}><Panel><p className="font-bold">관리자가 먼저 오늘 작업을 등록해야 합니다</p><p className="mt-2 text-sm text-ink-sub">관리자가 작업을 등록한 뒤 다시 출근해 주세요.</p></Panel></Screen>;
  }

  return (
    <Screen title="오늘 작업" right={clockOutButton}>
      <div className="space-y-4">
        <Panel><b>오늘 작업</b><p className="mt-2 text-ink-sub">{task?.text || '작업 내용을 불러오는 중입니다.'}</p></Panel>
        <Panel><b>관리자 TBM 내용</b>{tbm ? <><p className="mt-2 whitespace-pre-wrap text-ink">{tbm.transcript}</p>{tbm.memo && <p className="mt-3 text-sm text-ink-sub">메모: {tbm.memo}</p>}</> : <p className="mt-2 text-sm text-warn">저장된 TBM이 없습니다. 관리자에게 확인해 주세요.</p>}</Panel>
        <Panel><b>오늘 확인할 필수 안전 수칙</b>{task?.checklist?.filter((item) => item.level === 'required').map((item) => <p key={item.code} className="mt-2 text-sm">• {item.title}</p>)}{tbm?.missing?.length > 0 && <div className="mt-3 rounded-xl bg-warn-soft p-3 text-sm"><b>TBM에서 누락된 필수 수칙</b>{tbm.missing.map((item) => <p key={item.code} className="mt-1">• {item.title}</p>)}</div>}</Panel>
        {loadError && <p role="alert" className="mx-[22px] text-danger">{loadError}</p>}
        <form onSubmit={submit}>
          <Panel>
            <b>마감 보고</b>
            <label className="mt-4 block">오늘 작업 내용<textarea value={reportText} onChange={(event) => setReportText(event.target.value)} className="mt-2 min-h-24 w-full rounded-2xl border border-line p-3" /></label>
            <label className="mt-4 block">위험하거나 확인이 필요한 점<textarea value={riskNote} onChange={(event) => setRiskNote(event.target.value)} className="mt-2 min-h-24 w-full rounded-2xl border border-line p-3" /></label>
            <div className="mt-4">
              <p className="text-sm font-bold">사진 첨부 (선택)</p>
              <input ref={photoInputRef} type="file" accept="image/*" onChange={(event) => setPhoto(event.target.files?.[0] || null)} className="sr-only" />
              <button type="button" onClick={() => photoInputRef.current?.click()} className="mt-2 inline-flex min-h-11 items-center gap-2 rounded-xl border border-line bg-white px-4 text-sm font-bold text-ink">
                <Camera size={18} aria-hidden="true" />{photo ? photo.name : '사진 첨부하기'}
              </button>
            </div>
          </Panel>
          <div className="mx-[22px] mt-5"><AppButton big className="w-full">마감 보고 제출</AppButton></div>
          {message && <p className="mx-[22px] mt-3 text-center text-ink-sub">{message}</p>}
        </form>
      </div>
    </Screen>
  );
}
