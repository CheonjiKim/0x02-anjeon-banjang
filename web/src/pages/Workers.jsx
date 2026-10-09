import { useEffect, useState } from 'react';
import { api } from '../lib/api.js';
import { Panel, Screen } from '../components/ui.jsx';
import { Link } from 'react-router-dom';

export default function Workers() {
  const [tasks, setTasks] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => { Promise.all([api('/tasks'), api('/tasks/workers')]).then(([tasks, workers]) => setTasks(tasks.filter(task => workers.some(worker => worker.id === task.worker_id)))).catch(error => setError(error.message)); }, []);
  return <Screen title="작업자관리"><Panel>
    {error && <p role="alert">{error}</p>}
    {!tasks && !error && <p>작업자를 불러오는 중입니다.</p>}
    {tasks?.length === 0 && <p>아직 부여된 작업이 없습니다.</p>}
    {tasks?.map(task => <Link key={task.id} to={`/checklist/${task.id}`} state={{ task }} className="block min-h-16 border-b border-line py-4 last:border-0"><b>{task.worker_name || '작업자 미지정'}</b><p className="mt-1 break-words text-sm text-ink-sub">{task.text}</p><span className="mt-2 block text-sm font-bold text-brand-primary">안전 체크리스트 보기</span></Link>)}
  </Panel></Screen>;
}
