import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { AlertTriangle, Camera, ClipboardCheck, TriangleAlert } from 'lucide-react';
import { api } from '../lib/api.js';
import { AppButton, Panel, Screen, StatusBadge } from '../components/ui.jsx';

const CONDITION_LABELS = {
  work: '작업 종류', height: '실제 작업 높이', floor: '작업 층', flammable: '주변 가연물',
  ventilation: '환기 상태', nearby_people: '주변 인원', place: '장소 유형',
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
              <p className="font-bold">{CONDITION_LABELS[key]}</p><p>{value === '알 수 없음' ? '정보 없음' : value}</p>
            </div>
          ))}
        </div>
        <p className="mt-3 text-sm text-ink-sub">조건 추출: {task.extraction_method === 'mock' ? '시연용 키워드 추출' : task.extraction_method} · 규칙 버전: {task.rule_version} · 관리자 수정: {task.condition_changes?.length ? '있음' : '없음'}</p>
        {unknown.length > 0 && <div className="mt-4 text-sm text-warn"><p className="flex gap-2"><TriangleAlert size={18} />정보 없음은 현장에서 확인해야 합니다. 실제 ‘없음’으로 확정하지 않았습니다.</p><p className="mt-2">확인할 조건: {unknown.map(([key]) => CONDITION_LABELS[key]).join(', ')}</p><AppButton outline className="mt-3 w-full" onClick={() => navigate('/reviews')}>현장 조건 확인·수정</AppButton></div>}
      </Panel>

      <Panel className="mt-4">
        <h2 className="font-bold">현장에서 확인할 안전 수칙</h2>
        <p className="mt-2 text-sm text-ink-sub">‘필수’는 이 체크리스트에서 우선 확인할 항목입니다. 정보 부족으로 보수적으로 표시될 수 있으며 법적 의무 확정이나 작업 승인이 아닙니다.</p>
        {task.checklist.map((item) => (
          <div key={item.code} className="mt-4 border-t border-line pt-4 first:mt-3">
            <div className="flex items-start justify-between gap-2"><b className="min-w-0">{item.title}</b><span className="shrink-0"><StatusBadge kind={item.level} label={item.level === 'required' ? '우선 확인' : undefined} /></span></div>
            {item.note && <small className="mt-1 block text-ink-sub">{item.note}</small>}
            {item.source && <small className="mt-1 block text-ink-sub">근거: {item.source}{item.source.includes('산안규칙 제241조') && <> · <a className="underline" href={item.source.includes('241조의2') ? 'https://law.go.kr/lsLinkCommonInfo.do?chrClsCd=010202&lsJoLnkSeq=1016870875' : 'https://www.law.go.kr/LSW/lsInfoR.do?efYd=20260302&lsiSeq=273603'} target="_blank" rel="noreferrer">국가법령정보센터 원문</a></>}{item.source.includes('KOSHA 화재감시자 참고자료') && <> · <a className="underline" href="https://kosha.or.kr/kosha/data/screening_e.do?articleNo=410955&attachNo=232257&mode=download" target="_blank" rel="noreferrer">KOSHA 자료</a></>}</small>}
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
