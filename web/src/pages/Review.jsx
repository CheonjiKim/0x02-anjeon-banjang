import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api.js';
import { AppButton, Panel, Screen, StatusBadge } from '../components/ui.jsx';

const CONDITION_LABELS = {
  work: '작업 종류', height: '실제 작업 높이', floor: '작업 층', flammable: '주변 가연물',
  ventilation: '환기 상태', nearby_people: '주변 인원', place: '장소 유형',
};
const INPUT_HINTS = {
  height: '예: 2m (층수 아님)', floor: '예: 10층', flammable: '예: 합판 또는 없음',
  ventilation: '양호 또는 불량', nearby_people: '예: 10명, 있음, 없음', place: '예: 실내, 외부, 지하',
};

export default function Review({ embedded = false }) {
  const [forms, setForms] = useState([]);
  const [items, setItems] = useState([]);
  const [task, setTask] = useState(null);
  const [savedConditions, setSavedConditions] = useState(null);
  const [message, setMessage] = useState('');
  const [dirty, setDirty] = useState(false);
  const [reviewEvidence, setReviewEvidence] = useState('');
  const [workers, setWorkers] = useState([]);
  const [workerId, setWorkerId] = useState('');
  const [busy, setBusy] = useState(false);
  const Wrapper = embedded ? 'div' : Screen;
  const navigate = useNavigate();
  const taskId = localStorage.getItem('banjang.taskId');

  async function load() {
    if (!taskId) {
      setForms(await api('/worker-forms'));
      setItems([]);
      setTask(null);
      setDirty(false);
      return;
    }
    const savedTask = await api('/tasks/' + taskId);
    setItems(savedTask.checklist);
    let draft = null;
    try { draft = JSON.parse(localStorage.getItem('banjang.review.' + taskId) || 'null'); } catch { /* 저장된 초안이 없으면 서버 작업을 사용합니다. */ }
    setTask(draft ? { ...savedTask, conditions: draft.conditions } : savedTask);
    setWorkerId(String(draft?.workerId || savedTask.worker_id || ''));
    setReviewEvidence(draft?.reviewEvidence || '');
    setWorkers(await api('/tasks/workers'));
    setSavedConditions(savedTask.conditions);
    setDirty(Boolean(draft));
    try { setForms(await api('/worker-forms?task_id=' + taskId)); }
    catch { setForms([]); }
  }

  useEffect(() => { load().catch(error => setMessage(error.message)); }, []);

  function updateCondition(key, value) {
    const conditions = { ...task.conditions, [key]: value || '알 수 없음' };
    setTask({ ...task, conditions });
    setDirty(Object.entries(conditions).some(([field, next]) => next !== savedConditions?.[field]));
    setMessage('');
  }

  function saveDraft() {
    try {
      localStorage.setItem('banjang.review.' + taskId, JSON.stringify({ conditions: task.conditions, workerId, reviewEvidence }));
      setMessage('임시저장했습니다.');
    } catch { setMessage('임시저장하지 못했습니다. 브라우저 저장 공간을 확인해 주세요.'); }
  }

  async function completeTaskReview() {
    if (busy) return;
    if (!workers.some(worker => String(worker.id) === workerId)) { setMessage('작업자 이름을 선택해 주세요.'); return; }
    setBusy(true);
    try {
      let updated = task;
      if (dirty) updated = await api('/tasks/' + taskId + '/conditions', {
        method: 'PATCH', body: JSON.stringify({ ...task.conditions, review_evidence: reviewEvidence }),
      });
      updated = await api('/tasks/' + taskId + '/assignment', { method: 'PATCH', body: JSON.stringify({ worker_id: Number(workerId) }) });
      if (updated.review_status !== 'reviewed') updated = await api('/tasks/' + taskId + '/review', {
        method: 'POST', body: JSON.stringify({ action: 'conditions_corrected', reason: '관리자가 작업 지시 원문과 현장 조건을 대조했습니다.' }),
      });
      localStorage.removeItem('banjang.review.' + taskId);
      navigate('/checklist', { state: { task: updated, reviewCompleted: true } });
    } catch (error) { setMessage(error.message); }
    finally { setBusy(false); }
  }

  async function judge(formId, code) {
    const body = new FormData();
    body.append('item_code', code);
    try {
      const result = await api('/worker-forms/' + formId + '/evidence', { method: 'POST', body });
      setMessage(result.result === 'confirmed'
        ? `확인되어 ${result.points}점이 반영되었습니다.` : '사진 판정: ' + result.result);
      await load();
    } catch (error) { setMessage(error.message); }
  }

  return (
    <Wrapper {...(embedded ? {} : { title: "관리자 검토" })}>
      {!taskId && <Panel><p className="font-bold">근로자 제출 관리함</p><p className="mt-2 text-sm text-ink-sub">제출된 마감 보고를 최신순으로 확인합니다. 작업을 등록하면 해당 작업의 조건과 증빙을 연결해 검토할 수 있습니다.</p><AppButton className="mt-4 w-full" onClick={() => navigate('/')}>작업 등록으로 이동</AppButton></Panel>}
      {taskId && !task && <Panel><p>{message || '작업을 불러오는 중입니다.'}</p><AppButton outline className="mt-4 w-full" onClick={() => navigate('/')}>작업 화면으로 이동</AppButton></Panel>}
      {task && <Panel>
        <p className="text-sm text-ink-sub">작업 원문과 추출 조건을 대조합니다. 정보가 없는 조건은 현장 확인 전까지 필수 조치로 안내합니다. 이 검토는 작업 승인이 아닙니다.</p>
        {task && <p className="mt-2 text-sm text-ink-sub">조건 추출: {task.extraction_method === 'mock' ? '시연용 키워드 추출' : task.extraction_method} · 규칙 버전: {task.rule_version} · 관리자 수정: {task.condition_changes?.length ? '있음' : '없음'}</p>}
        {task.review_status === 'cancelled' && <div className="mt-4 rounded-xl bg-warn-soft p-4"><p className="font-bold">이 작업의 검토가 중단되었습니다.</p><AppButton className="mt-3 w-full" onClick={() => navigate('/')}>작업 화면으로 이동</AppButton></div>}
        {(task.review_status !== 'cancelled') && (
          <div className="mt-3 rounded-xl bg-warn-soft p-3">
            {task.review_status === 'pending' && <><StatusBadge kind="uncertain" /><p className="mt-2">{task.review_reason}</p></>}
            <p className="mt-2"><b>작업 원문</b>: {task.text}</p>
            <div className="mt-3 grid grid-cols-1 gap-3">
              <label className="text-sm">작업자 이름
                <select value={workerId} onChange={event => setWorkerId(event.target.value)} className="mt-1 min-h-11 w-full rounded-lg border p-2">
                  <option value="">작업자를 선택해 주세요</option>
                  {workers.map(worker => <option key={worker.id} value={worker.id}>{worker.name}{worker.team ? ` · ${worker.team}` : ''}</option>)}
                </select>
              </label>
              {Object.entries(task.conditions).map(([key, value]) => (
                <label key={key} className="text-sm">
                  {CONDITION_LABELS[key] || key}
                  <input
                    value={value === '알 수 없음' ? '' : value}
                    onChange={event => updateCondition(key, event.target.value)}
                    placeholder={key === 'work' ? '작업 종류 확인 필요' : INPUT_HINTS[key] || '정보 없음'}
                    className="mt-1 min-h-11 w-full rounded-lg border p-2"
                  />
                </label>
              ))}
            </div>
            <label className="mt-3 block text-sm font-bold">현장 확인 근거 (가연물 없음·환기 양호 등 위험을 낮추는 수정 시 필수)
              <textarea value={reviewEvidence} onChange={event => setReviewEvidence(event.target.value)} className="mt-1 w-full rounded-lg border p-3" placeholder="예: 현장 확인 위치·방법·확인자" />
            </label>
            <AppButton outline className="mt-3 w-full" disabled={busy} onClick={saveDraft}>임시저장</AppButton>
            <AppButton className="mt-2 w-full" disabled={busy} onClick={completeTaskReview}>{busy ? '저장 중…' : '검토기록 저장 후 체크리스트 보기'}</AppButton>
            {message && <p role="alert" className="mt-3 text-sm font-bold text-danger">{message}</p>}
          </div>
        )}
        {task?.review_action && <p className="mt-3 text-sm">저장된 검토: {task.review_action === 'conditions_corrected' ? '조건 검토 기록' : '검토 중단'} · {task.review_note}</p>}
        {task?.condition_changes?.length > 0 && <div className="mt-3 text-sm"><b>관리자 수정 기록</b>{task.condition_changes.map((change, index) => <p key={index} className="mt-2 break-words">{CONDITION_LABELS[change.field] || change.field}: {change.before_value} → {change.after_value} · 근거: {change.evidence} · {change.created_at}</p>)}</div>}
      </Panel>}
      {!embedded && forms.map(form => (
        <Panel key={form.id} className="mt-4">
          <div className="flex items-center justify-between gap-2"><b>{form.worker_name || '근로자'}</b><span className="text-xs text-ink-sub">{form.created_at}</span></div>
          <p className="mt-3">{form.report_text || '텍스트 보고 없음'}</p>
          <p className="mt-2 text-sm text-ink-sub">보호구 착용: {form.ppe_worn == null ? '미확인' : form.ppe_worn ? '착용 응답' : '미착용 응답'} · 수칙 이해: {form.understood == null ? '미확인' : form.understood ? '이해함 응답' : '추가 설명 필요'}</p>
          {form.risk_note && <p className="mt-2 text-sm text-warn">위험 메모: {form.risk_note}</p>}
          {form.photo_url && <>
            <img className="mt-3 w-full rounded-xl" src={form.photo_url} alt="마감 보고 사진" />
            {task && <select className="mt-3 w-full rounded-xl border border-line p-3"
              onChange={event => event.target.value && judge(form.id, event.target.value)} defaultValue="">
              <option value="">기록용으로 유지</option>
              {items.map(item => <option key={item.code} value={item.code}>{item.title} 증빙 판정 요청</option>)}
            </select>}
          </>}
        </Panel>
      ))}
      {message && <p role="status" className="mx-[22px] mt-3">{message}</p>}
    </Wrapper>
  );
}
