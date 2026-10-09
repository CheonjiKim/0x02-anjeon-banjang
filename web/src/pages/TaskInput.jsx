import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle, HardHat, LogOut } from 'lucide-react';
import { api, post } from '../lib/api.js';
import Review from './Review.jsx';
import Modal from '../components/Modal.jsx';
import Recorder from '../components/Recorder.jsx';
import { AppButton, Panel, Screen, SectionTitle } from '../components/ui.jsx';

export default function TaskInput({ onClockOut }) {
  const [text, setText] = useState('');
  const [closeRequested, setCloseRequested] = useState(true);
  const [reviewOpen, setReviewOpen] = useState(false);
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
      const task = await post('/tasks', { text, worker_id: null, close_requested: closeRequested, scenario: null });
      localStorage.setItem('banjang.taskId', task.id);
      setCurrentTask(task);
      setReviewOpen(true);
    } catch (requestError) { setError(requestError.message); }
    finally { setBusy(false); }
  }

  return <Screen title="TBM" right={onClockOut && <button type="button" onClick={onClockOut} className="inline-flex min-h-11 items-center gap-1.5 rounded-xl border border-line bg-white px-3 text-sm font-bold text-ink"><LogOut size={17} aria-hidden="true" />퇴근하기</button>}>
    {resumeError && <Panel><p role="alert" className="text-danger">{resumeError}</p><AppButton outline className="mt-3 w-full" onClick={() => window.location.reload()}>다시 불러오기</AppButton></Panel>}
    {currentTask && <Panel>
      <h2 className="font-bold">현재 작업 이어서 확인</h2>
      <p className="mt-2 break-words text-sm">{currentTask.text}</p>
      <p className="mt-2 text-sm text-ink-sub">{currentTask.review_status === 'reviewed' ? '조건 검토 기록 저장됨' : currentTask.review_status === 'pending' ? '작업 종류 확인 필요' : '체크리스트 초안 생성됨'} · 작업 승인은 아님</p>
      <AppButton className="mt-4 w-full" onClick={() => setReviewOpen(true)}>관리자 검토 이어가기</AppButton>
    </Panel>}
    <form onSubmit={submit}>
      <Panel className={currentTask ? 'mt-4' : ''}>
        <SectionTitle>새 작업 지시</SectionTitle>
        <p className="mb-3 text-sm text-ink-sub">말하거나 직접 입력하면 체크리스트 초안을 만듭니다. 기본 조건 추출은 시연용 키워드 방식이며, 생성 후 현장 조건을 확인해야 합니다.</p>
        <textarea value={text} onChange={(event) => setText(event.target.value)} placeholder="예: 2층에서 용접 작업, 주변에 합판이 있습니다." className="min-h-32 w-full rounded-2xl border border-line p-4" />
        <Recorder onTranscript={(value) => setText((current) => current ? current + ' ' + value : value)} />
      </Panel>
      <Panel className="mt-4">
        <label className="flex items-start gap-3"><input className="mt-1 h-5 w-5" type="checkbox" checked={closeRequested} onChange={(event) => setCloseRequested(event.target.checked)} /><span className="font-bold">근로자 마감 보고 요청</span></label>
      </Panel>
      {error && <p role="alert" className="mx-[22px] mt-3 text-sm text-danger">{error}</p>}
      <div className="mx-[22px] mt-5"><AppButton big disabled={busy} className="w-full"><HardHat className="mr-2 inline" size={20} />{busy ? '체크리스트 만드는 중…' : '새 체크리스트 만들기'}</AppButton></div>
    </form>
    <div className="mx-[22px] mt-4"><button type="button" onClick={() => navigate('/incidents')} className="flex min-h-14 w-full items-center justify-center gap-2 rounded-[20px] bg-danger px-4 font-bold text-white"><AlertTriangle size={20} />아차사고 신고하기</button></div>
    {reviewOpen && <Modal title="관리자 검토" onClose={() => setReviewOpen(false)}><Review embedded /></Modal>}
  </Screen>;
}
