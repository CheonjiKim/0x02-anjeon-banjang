import { useEffect, useState } from 'react';
import { api } from '../lib/api.js';
import { AppButton, Panel, Screen, StatusBadge } from '../components/ui.jsx';

const CONDITION_LABELS = {
  work: '작업 종류', height: '작업 높이', flammable: '주변 가연물',
  ventilation: '환기 상태', nearby_people: '주변 인원', place: '작업 장소',
};
const SUPPORTED_WORK = ['용접·용단', '절단·원형톱', '도장·방수', '사다리·말비계'];
const UNSUPPORTED_WORK_MESSAGE = '현재는 지원하지 않는 작업 종류입니다. 추후 지원될 예정입니다.';
const DEFAULT_REVIEW_VALUES = { flammable: '없음', nearby_people: '없음' };

function withReviewDefaults(conditions) {
  return Object.fromEntries(Object.entries(conditions).map(([key, value]) => [
    key, value === '알 수 없음' && DEFAULT_REVIEW_VALUES[key] ? DEFAULT_REVIEW_VALUES[key] : value,
  ]));
}

export default function Review() {
  const [forms, setForms] = useState([]);
  const [items, setItems] = useState([]);
  const [task, setTask] = useState(null);
  const [message, setMessage] = useState('');
  const [dirty, setDirty] = useState(false);
  const [conditionsConfirmed, setConditionsConfirmed] = useState(false);
  const taskId = localStorage.getItem('banjang.taskId');

  async function load() {
    if (!taskId) return;
    const [savedForms, savedTask] = await Promise.all([
      api('/worker-forms?task_id=' + taskId), api('/tasks/' + taskId),
    ]);
    setForms(savedForms);
    setItems(savedTask.checklist);
    setTask({ ...savedTask, conditions: withReviewDefaults(savedTask.conditions) });
    setDirty(false);
    setConditionsConfirmed(false);
  }

  useEffect(() => { load().catch(error => setMessage(error.message)); }, []);

  function updateCondition(key, value) {
    setTask(current => ({ ...current, conditions: { ...current.conditions, [key]: value } }));
    setDirty(true);
    setConditionsConfirmed(false);
  }

  async function correctConditions() {
    if (!conditionsConfirmed) return;
    const values = { ...task.conditions };
    const work = values.work.trim();
    values.work = { '용접': '용접·용단', '용단': '용접·용단' }[work] || work;
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
      setConditionsConfirmed(false);
      setMessage(updated.review_status === 'ready'
        ? '조건을 반영하고 체크리스트를 다시 생성했습니다. 검토 기록을 저장해 주세요.'
        : '조건을 저장했습니다. 미확인 필수 조건을 확인해 주세요.');
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
          reason: '관리자가 작업 지시 원문과 추출 조건을 대조하고 누락 조건을 보정했습니다.',
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
      <Panel>
        <p className="text-sm text-ink-sub">작업 원문과 AI 추출 조건을 대조합니다. 불확실한 조건은 관리자 확인 전까지 작업 준비를 완료하지 않습니다.</p>
        {(task?.review_status === 'pending' || task?.review_status === 'ready') && (
          <div className="mt-3 rounded-xl bg-warn-soft p-3">
            {task.review_status === 'pending' && <><StatusBadge kind="uncertain" /><p className="mt-2">{task.review_reason}</p></>}
            <p className="mt-2"><b>작업 원문</b>: {task.text}</p>
            <div className="mt-3 grid grid-cols-2 gap-2">
              {Object.entries(task.conditions).map(([key, value]) => (
                <label key={key} className="text-sm">
                  {CONDITION_LABELS[key] || key}
                  <input
                    value={value}
                    onChange={event => updateCondition(key, event.target.value)}
                    className="mt-1 w-full rounded-lg border p-2"
                  />
                </label>
              ))}
            </div>
            <label className="mt-4 flex items-start gap-2 text-sm font-bold text-ink">
              <input type="checkbox" checked={conditionsConfirmed} onChange={event => setConditionsConfirmed(event.target.checked)} className="mt-0.5 h-5 w-5" />
              입력한 작업 조건을 전부 확인했습니다.
            </label>
            <AppButton className="mt-3 w-full" disabled={!conditionsConfirmed} onClick={correctConditions}>조건 수정 후 체크리스트 재생성</AppButton>
            <AppButton className="mt-2 w-full" disabled={task.review_status !== 'ready' || dirty} onClick={completeTaskReview}>검토 기록 저장</AppButton>
          </div>
        )}
        {task?.review_action && <p className="mt-3 text-sm">저장된 조치: {task.review_action} · {task.review_note}</p>}
      </Panel>
      {forms.map(form => (
        <Panel key={form.id} className="mt-4">
          <p>{form.report_text || '텍스트 보고 없음'}</p>
          <p className="mt-2 text-sm text-warn">{form.risk_note}</p>
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
