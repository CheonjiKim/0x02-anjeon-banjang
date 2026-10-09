import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { AlertTriangle, Camera, ClipboardCheck, TriangleAlert } from 'lucide-react';
import { api } from '../lib/api.js';
import { AppButton, Panel, Screen, StatusBadge } from '../components/ui.jsx';

const CONDITION_LABELS = {
  work: '작업 종류', height: '작업 높이', flammable: '주변 가연물',
  ventilation: '환기 상태', nearby_people: '주변 인원', place: '작업 장소',
};

export default function Checklist() {
  const [task, setTask] = useState(useLocation().state?.task || null);
  const [risks, setRisks] = useState([]);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const id = localStorage.getItem('banjang.taskId');
    if (!id) return;
    Promise.all([task ? Promise.resolve(task) : api('/tasks/' + id), api('/tasks/' + id + '/risk')])
      .then(([loadedTask, loadedRisks]) => {
        setTask(loadedTask);
        setRisks(loadedRisks);
      })
      .catch((requestError) => setError(requestError.message));
  }, []);

  if (!task) {
    return <Screen title="체크리스트"><Panel>{error || '작업을 먼저 입력해 주세요.'}</Panel></Screen>;
  }

  const unknown = Object.entries(task.conditions).filter(([, value]) => value === '알 수 없음');
  return (
    <Screen title="안전 체크리스트">
      <Panel>
        <p className="text-sm text-ink-sub">오늘 작업</p>
        <p className="mt-1 font-bold">{task.text}</p>
        <div className="mt-4 grid grid-cols-2 gap-2">
          {Object.entries(task.conditions).map(([key, value]) => (
            <div key={key} className={`rounded-xl p-3 text-sm ${value === '알 수 없음' ? 'bg-warn-soft text-warn' : 'bg-brand-soft text-brand-dark'}`}>
              <p className="font-bold">{CONDITION_LABELS[key]}</p><p>{value}</p>
            </div>
          ))}
        </div>
        {unknown.length > 0 && <p className="mt-4 flex gap-2 text-sm text-warn"><TriangleAlert size={18} />확인하지 못한 조건은 필수 조치로 안내합니다.</p>}
      </Panel>

      <Panel className="mt-4">
        <h2 className="font-bold">확인할 안전 수칙</h2>
        {task.checklist.map((item) => (
          <div key={item.code} className="mt-4 border-t border-line pt-4 first:mt-3">
            <div className="flex items-center justify-between gap-2"><b>{item.title}</b><StatusBadge kind={item.level} /></div>
            {(item.note || item.source) && <small className="mt-1 block text-ink-sub">{item.note || item.source}</small>}
          </div>
        ))}
      </Panel>

      <Panel className="mt-4">
        <h2 className="flex items-center gap-2 font-bold"><AlertTriangle size={19} className="text-danger" />위험성평가 초안</h2>
        {risks.map((risk) => <div key={risk.code} className="mt-4 border-t border-line pt-4 first:mt-3">
          <div className="flex items-center justify-between gap-2"><b>{risk.hazard}</b><span className="rounded-full bg-danger-soft px-3 py-1 text-sm font-bold text-danger">발생 {risk.likelihood} · 중대성 {risk.severity}</span></div>
          <p className="mt-2 text-sm text-ink-sub">{risk.measure}</p>
        </div>)}
      </Panel>

      <div className="mx-[22px] mt-5 grid gap-3">
        <AppButton big className="w-full" onClick={() => navigate('/tbm', { state: { task } })}><ClipboardCheck className="mr-2 inline" size={20} />TBM 기록하기</AppButton>
        <AppButton outline className="w-full" onClick={() => navigate('/evidence')}><Camera className="mr-2 inline" size={20} />사진 증빙 등록</AppButton>
      </div>
    </Screen>
  );
}
