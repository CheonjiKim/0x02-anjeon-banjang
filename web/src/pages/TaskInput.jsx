import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle, ClipboardList, HardHat, LogOut } from 'lucide-react';
import { api, post } from '../lib/api.js';
import Recorder from '../components/Recorder.jsx';
import { AppButton, Panel, Screen, SectionTitle } from '../components/ui.jsx';

export default function TaskInput({ onClockOut }) {
  const [text, setText] = useState('');
  const [closeRequested, setCloseRequested] = useState(true);
  const [scenario, setScenario] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [currentTask, setCurrentTask] = useState(null);
  const [resumeError, setResumeError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const id = localStorage.getItem('banjang.taskId');
    if (id) api('/tasks/' + id).then(setCurrentTask).catch((requestError) => {
      if (requestError.status === 404) localStorage.removeItem('banjang.taskId');
      else setResumeError('현재 작업을 불러오지 못했습니다. 연결을 확인하고 다시 시도해 주세요.');
    });
  }, []);

  async function submit(event) {
    event.preventDefault();
    if (!text.trim()) { setError('작업 내용을 입력해 주세요.'); return; }
    setBusy(true); setError('');
    try {
      const task = await post('/tasks', { text, close_requested: closeRequested, scenario: scenario || null });
      localStorage.setItem('banjang.taskId', task.id);
      setCurrentTask(task);
      navigate(task.review_status === 'pending' ? '/reviews' : '/checklist', { state: { task } });
    } catch (requestError) { setError(requestError.message); }
    finally { setBusy(false); }
  }

  return <Screen title="오늘 작업" right={onClockOut && <button type="button" onClick={onClockOut} className="inline-flex min-h-11 items-center gap-1.5 rounded-xl border border-line bg-white px-3 text-sm font-bold text-ink"><LogOut size={17} aria-hidden="true" />퇴근하기</button>}>
    {resumeError && <Panel><p role="alert" className="text-danger">{resumeError}</p><AppButton outline className="mt-3 w-full" onClick={() => window.location.reload()}>다시 불러오기</AppButton></Panel>}
    {currentTask && <Panel>
      <h2 className="font-bold">현재 작업 이어서 확인</h2>
      <p className="mt-2 break-words text-sm">{currentTask.text}</p>
      <p className="mt-2 text-sm text-ink-sub">{currentTask.review_status === 'reviewed' ? '조건 검토 기록 저장됨' : currentTask.review_status === 'pending' ? '작업 종류 확인 필요' : '체크리스트 초안 생성됨'} · 작업 승인은 아님</p>
      <AppButton className="mt-4 w-full" onClick={() => navigate(currentTask.review_status === 'pending' ? '/reviews' : '/checklist')}>{currentTask.review_status === 'pending' ? '관리자 검토 이어가기' : '체크리스트 보기'}</AppButton>
      <AppButton outline className="mt-2 w-full" onClick={() => navigate('/reviews')}>조건 확인·수정</AppButton>
    </Panel>}
    <form onSubmit={submit}>
      <Panel className={currentTask ? 'mt-4' : ''}>
        <SectionTitle>새 작업 지시</SectionTitle>
        <p className="mb-3 text-sm text-ink-sub">말하거나 직접 입력하면 체크리스트 초안을 만듭니다. 기본 조건 추출은 시연용 키워드 방식이며, 생성 후 현장 조건을 확인해야 합니다.</p>
        <textarea value={text} onChange={(event) => setText(event.target.value)} placeholder="예: 2층에서 용접 작업, 주변에 합판이 있습니다." className="min-h-32 w-full rounded-2xl border border-line p-4" />
        <Recorder onTranscript={(value) => setText((current) => current ? current + ' ' + value : value)} />
      </Panel>
      <Panel className="mt-4">
        <label className="flex items-start gap-3"><input className="mt-1 h-5 w-5" type="checkbox" checked={closeRequested} onChange={(event) => setCloseRequested(event.target.checked)} /><span><b>근로자 마감 보고 요청</b><small className="mt-1 block text-ink-sub">작업 후 텍스트와 사진을 선택적으로 받습니다.</small></span></label>
        <label className="mt-4 block text-sm">시연용 실패 상황<select value={scenario} onChange={(event) => setScenario(event.target.value)} className="mt-2 w-full rounded-xl border border-line p-3"><option value="">없음</option><option value="extract_fail">조건 추출 실패</option><option value="extract_empty">빈 응답</option><option value="unsupported_none">근거 없는 조건</option></select></label>
        {scenario && <p className="mt-2 text-sm text-warn">시연용 설정이 켜져 있습니다.</p>}
      </Panel>
      {error && <p role="alert" className="mx-[22px] mt-3 text-sm text-danger">{error}</p>}
      <div className="mx-[22px] mt-5"><AppButton big disabled={busy} className="w-full"><HardHat className="mr-2 inline" size={20} />{busy ? '체크리스트 만드는 중…' : '새 체크리스트 만들기'}</AppButton></div>
    </form>
    <Panel className="mt-5"><div className="flex gap-3"><ClipboardList className="shrink-0 text-brand-primary" /><p className="text-sm text-ink-sub">체크리스트 생성과 현장 확인은 별도 단계입니다. 이 앱은 법률을 해석하거나 작업을 승인하지 않습니다.</p></div></Panel>
    <button type="button" onClick={() => navigate('/incidents')} className="mx-[22px] mt-4 flex min-h-11 items-center gap-2 text-sm font-bold text-danger"><AlertTriangle size={18} />아차사고 신고·조치 확인</button>
  </Screen>;
}
