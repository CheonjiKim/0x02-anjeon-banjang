import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ClipboardCheck } from 'lucide-react';
import { api } from '../lib/api.js';
import { AppButton, Panel, Screen, StatusBadge } from '../components/ui.jsx';
export default function Checklist() {
 const [task, setTask] = useState(useLocation().state?.task); const navigate = useNavigate();
 useEffect(() => { const id = localStorage.getItem('banjang.taskId'); if (!task && id) api('/tasks/' + id).then(setTask).catch(() => {}); }, [task]);
 if (!task) return <Screen title="체크리스트"><Panel>작업을 먼저 입력해 주세요.</Panel></Screen>;
 return <Screen title="안전 체크리스트"><Panel><p className="text-sm text-ink-sub">{task.text}</p>{task.checklist.map((item) => <div key={item.code} className="mt-4 border-t border-line pt-4"><div className="flex items-center justify-between gap-2"><b>{item.title}</b><StatusBadge kind={item.level} /></div><small className="block text-ink-sub">{item.source || item.note}</small></div>)}</Panel><div className="mx-[22px] mt-5"><AppButton big className="w-full" onClick={() => navigate('/tbm', { state: { task } })}><ClipboardCheck className="mr-2 inline" size={20} />TBM 기록하기</AppButton></div></Screen>;
}
