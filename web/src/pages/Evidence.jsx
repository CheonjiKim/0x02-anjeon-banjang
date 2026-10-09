import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Camera, Check, ChevronDown, RefreshCw, Search, ShieldCheck } from 'lucide-react';
import { api, post } from '../lib/api.js';
import { AppButton, EmptyState, Panel, Screen, StatusBadge } from '../components/ui.jsx';

const RESULT_LABELS = { confirmed: '확인됨', not_visible: '안 보임', uncertain: '판단불가' };
const MOCK_SCENARIOS = [
  ['verify_reject', '검증 불일치'], ['judge_fail', '판정 응답 오류'], ['judge_timeout', '판정 시간 초과'],
  ['judge_invalid', '잘못된 판정 응답'], ['verify_empty', '빈 검증 근거'],
];

export default function Evidence() {
  const navigate = useNavigate();
  const [task, setTask] = useState(null);
  const [queue, setQueue] = useState([]);
  const [selectedCode, setSelectedCode] = useState('');
  const [photo, setPhoto] = useState(null);
  const [useMock, setUseMock] = useState(false);
  const [scenario, setScenario] = useState('verify_reject');
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState('');
  const [reasons, setReasons] = useState({});
  const taskId = localStorage.getItem('banjang.taskId');

  async function load() {
    if (!taskId) return;
    const [loadedTask, loadedQueue] = await Promise.all([api('/tasks/' + taskId), api('/evidence/review-queue')]);
    setTask(loadedTask);
    setQueue(loadedQueue.filter((entry) => entry.task_id === Number(taskId)));
    setSelectedCode((current) => current || loadedTask.checklist[0]?.code || '');
  }
  useEffect(() => { load().catch((error) => setMessage(error.message)); }, []);

  async function submit(event) {
    event.preventDefault();
    if (!taskId || !selectedCode || !photo || pending) return;
    const body = new FormData();
    body.append('task_id', taskId);
    body.append('item_code', selectedCode);
    body.append('photo', photo);
    if (useMock) body.append('scenario', scenario);
    setPending(true); setMessage('');
    try {
      const result = await api('/evidence', { method: 'POST', body });
      setMessage(`${RESULT_LABELS[result.result]} · ${result.points ? `+${result.points}점 적립` : '점수 적립 없음'}`);
      setPhoto(null);
      await load();
    } catch (error) { setMessage(error.message); }
    finally { setPending(false); }
  }

  async function review(id, action) {
    try {
      await post(`/evidence/${id}/reviews`, { action, reason: reasons[id] || '사진과 체크리스트 항목을 대조해 확인했습니다.' });
      setMessage('관리자 조치를 저장했습니다.');
      await load();
    } catch (error) { setMessage(error.message); }
  }

  if (!taskId) return <Screen title="사진 증빙"><EmptyState icon={Camera} title="먼저 작업을 등록해 주세요" hint="작업별 체크리스트 항목에 사진을 연결합니다." action="작업 등록으로 이동" onAction={() => navigate('/')} /></Screen>;
  const selected = task?.checklist.find((item) => item.code === selectedCode);
  return (
    <Screen title="사진 증빙">
      <Panel>
        <div className="flex items-center gap-3"><span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-brand-soft text-brand-primary"><ShieldCheck /></span><div><b>안전 조치 사진 등록</b><p className="text-sm text-ink-sub">확인된 사진만 점수가 반영됩니다.</p></div></div>
        <form className="mt-5" onSubmit={submit}>
          <label className="block text-sm font-bold">확인할 항목
            <select value={selectedCode} onChange={(event) => setSelectedCode(event.target.value)} className="mt-2 w-full rounded-xl border border-line bg-white p-3">
              {task?.checklist.map((item) => <option key={item.code} value={item.code}>{item.level === 'required' ? '[필수] ' : '[권장] '}{item.title}</option>)}
            </select>
          </label>
          {selected && <p className="mt-2 text-sm text-ink-sub">사진에는 “{selected.title}” 조치가 실제로 보여야 합니다.</p>}
          <label className="mt-4 block text-sm font-bold">사진
            <input aria-label="증빙 사진" type="file" accept="image/*" required onChange={(event) => setPhoto(event.target.files?.[0] || null)} className="mt-2 block w-full text-sm" />
          </label>
          <details className="mt-4 rounded-xl bg-gray-100 p-3 text-sm">
            <summary className="flex cursor-pointer items-center gap-2 font-bold"><ChevronDown size={16} />개발용 mock 실패 재현</summary>
            <label className="mt-3 flex items-center gap-2"><input type="checkbox" checked={useMock} onChange={(event) => setUseMock(event.target.checked)} />시연용 mock 결과 사용</label>
            {useMock && <select value={scenario} onChange={(event) => setScenario(event.target.value)} className="mt-3 w-full rounded-xl border border-line bg-white p-3">{MOCK_SCENARIOS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select>}
          </details>
          <AppButton big className="mt-5 w-full" disabled={!photo || !selectedCode || pending}><Camera className="mr-2 inline" size={20} />{pending ? 'AI 판정 중…' : '사진 판정 요청'}</AppButton>
        </form>
      </Panel>

      <h2 className="mx-[22px] mt-6 text-lg font-bold">관리자 검토 대기</h2>
      {queue.length === 0 && <EmptyState icon={Search} title="대기 사진 없음" hint="판단불가·안 보임 사진은 이곳에서 확인합니다." />}
      {queue.map((row) => <Panel key={row.id} className="mt-3">
        <img src={row.photo_url} alt="검토 대상 사진" className="w-full rounded-xl" />
        <div className="mt-3 flex items-center justify-between gap-2"><h3 className="font-bold">{row.title}</h3><StatusBadge kind={row.result} label={RESULT_LABELS[row.result]} /></div>
        <p className="mt-2 text-sm text-ink-sub">{row.observed}</p><p className="mt-1 text-sm text-warn">{row.retake_hint}</p>
        <input className="mt-3 w-full rounded-xl border border-line p-3" placeholder="조치 사유" value={reasons[row.id] || ''} onChange={(event) => setReasons({ ...reasons, [row.id]: event.target.value })} />
        <div className="mt-3 grid grid-cols-2 gap-2"><AppButton outline onClick={() => review(row.id, 'retake_requested')}><RefreshCw className="mr-1 inline" size={16} />재촬영 요청</AppButton><AppButton onClick={() => review(row.id, 'confirmed_by_manager')}><Check className="mr-1 inline" size={16} />직접 확인</AppButton></div>
        {row.reviews.map((review) => <p key={review.id} className="mt-2 text-sm text-ink-sub">{review.action}: {review.reason}</p>)}
      </Panel>)}
      {message && <p role="status" className="mx-[22px] mt-4 text-sm font-bold">{message}</p>}
    </Screen>
  );
}
