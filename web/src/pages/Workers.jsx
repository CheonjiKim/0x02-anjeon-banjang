import { useEffect, useState } from 'react';
import { api } from '../lib/api.js';
import { Panel, Screen } from '../components/ui.jsx';

export default function Workers() {
  const [tasks, setTasks] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => { Promise.all([api('/tasks'), api('/tasks/workers')]).then(([tasks, workers]) => setTasks(tasks.filter(task => workers.some(worker => worker.id === task.worker_id)))).catch(error => setError(error.message)); }, []);
  return <Screen title="작업자관리"><Panel>
    {error && <p role="alert">{error}</p>}
    {!tasks && !error && <p>작업자를 불러오는 중입니다.</p>}
    {tasks?.length === 0 && <p>아직 부여된 작업이 없습니다.</p>}
    {tasks?.map(task => <div key={task.id} className="border-b border-line py-4 last:border-0"><b>{task.worker_name || '작업자 미지정'}</b><p className="mt-1 break-words text-sm text-ink-sub">{task.text}</p></div>)}
  </Panel></Screen>;
}
