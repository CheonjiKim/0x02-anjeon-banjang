import { useEffect, useState } from 'react';
import { api } from '../lib/api.js';
import { readSession } from '../lib/session.js';
import { Panel, Screen } from '../components/ui.jsx';
import Modal from '../components/Modal.jsx';

export default function Calendar({ worker = false }) {
  const [tasks, setTasks] = useState(null);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState(null);
  useEffect(() => { api('/tasks' + (worker ? '?worker_id=' + readSession().worker_id : '')).then(setTasks).catch(error => setError(error.message)); }, [worker]);
  const dayTasks = day => (tasks || []).filter(task => task.created_at.slice(0, 10) === `2026-10-${String(day).padStart(2, '0')}`);
  return <Screen title="캘린더"><Panel className="!mx-3 !px-2">
    <h2 className="mb-5 px-2 text-xl font-bold">2026년 10월</h2>
    {error && <p role="alert">{error}</p>}
    {!tasks && !error && <p>작업을 불러오는 중입니다.</p>}
    <div className="grid grid-cols-7 text-center text-xs">{['일', '월', '화', '수', '목', '금', '토'].map(day => <b key={day} className="py-2">{day}</b>)}</div>
    <div className="grid grid-cols-7">{Array.from({ length: 35 }, (_, index) => {
      const day = index - 3;
      if (day < 1 || day > 31) return <div key={index} />;
      const entries = dayTasks(day);
      return <div key={index} className="min-h-32 min-w-0 border-t border-line px-0.5 py-2"><b className="text-sm">{day}</b>
        {entries.slice(0, 3).map(task => <p key={task.id} title={task.text} className="mt-1 truncate rounded bg-brand-soft px-1 py-1 text-[10px] text-brand-dark">{task.text}</p>)}
        {entries.length > 0 && <button type="button" aria-label={`10월 ${day}일 작업 ${entries.length}개 더보기`} onClick={() => setSelected(day)} className="min-h-11 w-full text-[10px] font-bold text-brand-primary">더보기{entries.length > 3 ? ` +${entries.length - 3}` : ''}</button>}
      </div>;
    })}</div>
  </Panel>{selected && <Modal title={`10월 ${selected}일 작업`} onClose={() => setSelected(null)}><div className="px-5">{dayTasks(selected).map(task => <div key={task.id} className="border-b border-line py-4"><b>{task.worker_name}</b><p className="mt-1 break-words">{task.text}</p></div>)}</div></Modal>}</Screen>;
}
