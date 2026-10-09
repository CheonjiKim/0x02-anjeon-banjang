import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Camera, ListTodo, MessageCircleQuestion } from 'lucide-react';
import { api } from '../lib/api.js';
import { AppButton, EmptyState, Panel, Screen, StatusBadge } from '../components/ui.jsx';

export default function Todo() {
  const [todos, setTodos] = useState([]);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const taskId = localStorage.getItem('banjang.taskId');

  useEffect(() => {
    if (!taskId) return;
    api('/todos?task_id=' + taskId).then(setTodos).catch((requestError) => setError(requestError.message));
  }, [taskId]);

  if (!taskId) return <Screen title="반장 할 일"><EmptyState icon={ListTodo} title="오늘 등록한 작업이 없어요" hint="작업 탭에서 작업을 먼저 등록해 주세요." /></Screen>;
  return (
    <Screen title="반장 할 일">
      {error && <Panel><p className="text-danger">{error}</p></Panel>}
      {!error && todos.length === 0 && <EmptyState icon={ListTodo} title="확인이 필요한 항목이 없어요" hint="사진 판정과 작업 조건을 계속 확인해 주세요." />}
      {todos.map((todo) => <Panel key={todo.id} className="mt-4">
        <div className="flex items-start justify-between gap-3">
          <div><div className="flex items-center gap-2"><h2 className="font-bold">{todo.title}</h2>{todo.level && <StatusBadge kind={todo.level} />}</div>
            <p className="mt-2 text-sm text-ink-sub">{todo.detail || '관리자 확인이 필요합니다.'}</p></div>
          {todo.kind === 'condition' ? <MessageCircleQuestion className="shrink-0 text-warn" /> : <Camera className="shrink-0 text-review" />}
        </div>
        {todo.observed && <p className="mt-3 rounded-xl bg-review-soft p-3 text-sm text-review">AI 관찰: {todo.observed}</p>}
        {todo.photo_url && <img src={todo.photo_url} alt={`${todo.title} 증빙 사진`} className="mt-3 w-full rounded-xl" />}
        {todo.kind !== 'condition' && <AppButton outline className="mt-4 w-full" onClick={() => navigate('/evidence')}>사진 검토로 이동</AppButton>}
      </Panel>)}
    </Screen>
  );
}
