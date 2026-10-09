import { useEffect, useState } from 'react';
import { api } from '../lib/api.js';
import { AppButton, Panel, Screen, StatusBadge } from '../components/ui.jsx';

const CONDITION_LABELS = {
  work: '작업 종류', height: '작업 높이', flammable: '주변 가연물',
  ventilation: '환기 상태', nearby_people: '주변 인원', place: '작업 장소',
};
const SUPPORTED_WORK = ['용접·용단', '절단·원형톱', '도장·방수', '사다리·말비계'];
const UNSUPPORTED_WORK_MESSAGE = '현재는 지원하지 않는 작업 종류입니다. 추후 지원될 예정입니다.';

export default function Review() {
  const [forms, setForms] = useState([]);
  const [items, setItems] = useState([]);
  const [task, setTask] = useState(null);
  const [message, setMessage] = useState('');
  const [dirty, setDirty] = useState(false);
  const taskId = localStorage.getItem('banjang.taskId');

  async function load() {
    if (!taskId) {
      setForms(await api('/worker-forms'));
      setItems([]);
      setTask(null);
      setDirty(false);
      return;
    }
    const [savedForms, savedTask] = await Promise.all([
      api('/worker-forms?task_id=' + taskId), api('/tasks/' + taskId),
    ]);
    setForms(savedForms);
    setItems(savedTask.checklist);
    setTask(savedTask);
    setDirty(false);
  }

  useEffect(() => { load().catch(error => setMessage(error.message)); }, []);

  function updateCondition(key, value) {
    setTask(current => ({ ...current, conditions: { ...current.conditions, [key]: value } }));
    setDirty(true);
  }

  async function correctConditions() {
    const values = { ...task.conditions };
    const work = values.work.trim();
    values.work = { '용접': '용접·용단', '용단': '용접·용단' }[work] || work || '알 수 없음';
    if (values.work !== '알 수 없음' && !SUPPORTED_WORK.includes(values.work)) {
      window.alert(UNSUPPORTED_WORK_MESSAGE);
      return;
    }
    try {
      const updated = await api('/tasks/' + taskId + '/conditions', {
        method: 'PATCH', body: JSON.stringify(values),
      });
      setTask(updated);
      setItems(updated.checklist);
      setDirty(false);
      setMessage(updated.review_status === 'ready'
        ? '체크리스트를 다시 생성했습니다. 정보가 없는 조건은 필수 조치로 유지됩니다.'
        : '조건을 저장했습니다. 작업 종류를 확인해 주세요.');
    } catch (error) {
      if (error.status === 422 && error.message === UNSUPPORTED_WORK_MESSAGE) window.alert(error.message);
      else setMessage(error.message);
    }
  }

  async function completeTaskReview() {
    try {
      const updated = await api('/tasks/' + taskId + '/review', {
        method: 'POST',
        body: JSON.stringify({
          action: 'conditions_corrected',
          reason: '관리자가 작업 지시 원문과 추출 조건을 대조했습니다. 정보가 없는 조건은 보수적으로 유지합니다.',
        }),
      });
      setTask(updated);
      setMessage('관리자 검토 기록을 저장했습니다.');
    } catch (error) { setMessage(error.message); }
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
    <Screen title="관리자 검토">
      {!taskId && <Panel><p className="font-bold">근로자 제출 관리함</p><p className="mt-2 text-sm text-ink-sub">근로자가 제출한 마감 보고를 최신순으로 확인합니다. 오늘 작업을 등록하면 작업 조건과 사진 증빙까지 연결해 검토할 수 있습니다.</p></Panel>}
      <Panel>
        <p className="text-sm text-ink-sub">작업 원문과 AI 추출 조건을 대조합니다. 정보가 없는 조건은 안전 조치를 필수로 유지한 채 체크리스트를 만듭니다.</p>
        {(task?.review_status === 'pending' || task?.review_status === 'ready') && (
          <div className="mt-3 rounded-xl bg-warn-soft p-3">
            {task.review_status === 'pending' && <><StatusBadge kind="uncertain" /><p className="mt-2">{task.review_reason}</p></>}
            <p className="mt-2"><b>작업 원문</b>: {task.text}</p>
            <div className="mt-3 grid grid-cols-2 gap-2">
              {Object.entries(task.conditions).map(([key, value]) => (
                <label key={key} className="text-sm">
                  {CONDITION_LABELS[key] || key}
                  <input
                    value={value === '알 수 없음' ? '' : value}
                    onChange={event => updateCondition(key, event.target.value)}
                    placeholder={key === 'work' ? '작업 종류 확인 필요' : '정보 없음'}
                    className="mt-1 w-full rounded-lg border p-2"
                  />
                </label>
              ))}
            </div>
            <AppButton className="mt-3 w-full" onClick={correctConditions}>조건 수정 후 체크리스트 재생성</AppButton>
            <AppButton className="mt-2 w-full" disabled={task.review_status !== 'ready' || dirty} onClick={completeTaskReview}>검토 기록 저장</AppButton>
          </div>
        )}
        {task?.review_action && <p className="mt-3 text-sm">저장된 조치: {task.review_action} · {task.review_note}</p>}
      </Panel>
      {forms.map(form => (
        <Panel key={form.id} className="mt-4">
          <div className="flex items-center justify-between gap-2"><b>{form.worker_name || '근로자'}</b><span className="text-xs text-ink-sub">{form.created_at}</span></div>
          <p className="mt-3">{form.report_text || '텍스트 보고 없음'}</p>
          {form.risk_note && <p className="mt-2 text-sm text-warn">위험 메모: {form.risk_note}</p>}
          {form.photo_url && <>
            <img className="mt-3 w-full rounded-xl" src={form.photo_url} alt="마감 보고 사진" />
            <select className="mt-3 w-full rounded-xl border border-line p-3"
              onChange={event => event.target.value && judge(form.id, event.target.value)} defaultValue="">
              <option value="">기록용으로 유지</option>
              {items.map(item => <option key={item.code} value={item.code}>{item.title} 증빙 판정 요청</option>)}
            </select>
          </>}
        </Panel>
      ))}
      {message && <p role="status" className="mx-[22px] mt-3">{message}</p>}
    </Screen>
  );
}
