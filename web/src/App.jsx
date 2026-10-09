import { useState } from 'react';
import { NavLink, Route, Routes, useLocation } from 'react-router-dom';
import { Camera, ChartColumn, HardHat, ListTodo, Trophy } from 'lucide-react';
import { STROKE } from './components/ui.jsx';
import Welcome from './pages/Welcome.jsx';
import TaskInput from './pages/TaskInput.jsx';
import Checklist from './pages/Checklist.jsx';
import Todo from './pages/Todo.jsx';
import Evidence from './pages/Evidence.jsx';
import Ranking from './pages/Ranking.jsx';
import Eval from './pages/Eval.jsx';
import WorkerForm from './pages/WorkerForm.jsx';
import LoginSample from './pages/LoginSample.jsx';

const tabs = [
  ['/', '작업', HardHat],
  ['/todo', '할 일', ListTodo],
  ['/evidence', '사진', Camera],
  ['/ranking', '기록', Trophy],
  ['/eval', '평가', ChartColumn],
];

function welcomeSeen() {
  try { return localStorage.getItem('banjang-welcome-seen') === '1'; }
  catch { return true; }
}

export default function App() {
  const [seen, setSeen] = useState(welcomeSeen);
  const location = useLocation();
  const standalone = location.pathname.startsWith('/worker/') || location.pathname === '/login';

  function start() {
    try { localStorage.setItem('banjang-welcome-seen', '1'); }
    catch { /* 저장이 막혀도 이번 화면에서는 시작한다. */ }
    setSeen(true);
  }

  if (!seen && !standalone) return <Welcome onStart={start} />;

  return (
    <>
      <Routes>
        <Route path="/" element={<TaskInput />} />
        <Route path="/checklist" element={<Checklist />} />
        <Route path="/todo" element={<Todo />} />
        <Route path="/evidence" element={<Evidence />} />
        <Route path="/ranking" element={<Ranking />} />
        <Route path="/eval" element={<Eval />} />
        <Route path="/worker/:taskId" element={<WorkerForm />} />
        <Route path="/login" element={<LoginSample />} />
      </Routes>
      {!standalone && (
        <nav aria-label="주 메뉴" className="fixed inset-x-0 bottom-0 z-30 rounded-t-[28px] bg-white pb-safe shadow-[0_-4px_24px_rgba(0,0,0,0.06)]">
          <div className="grid h-[68px] grid-cols-5">
            {tabs.map(([path, label, Icon]) => (
              <NavLink key={path} to={path} end={path === '/'}
                className={({ isActive }) => `relative flex min-h-14 flex-col items-center justify-center gap-1 text-[13px] font-bold ${isActive ? 'text-brand-primary' : 'text-ink-sub'}`}>
                {({ isActive }) => (
                  <>
                    {path === '/evidence' ? (
                      <span className={`absolute -top-5 flex h-14 w-14 items-center justify-center rounded-full bg-brand-primary text-white shadow-cta ${isActive ? 'ring-4 ring-brand-soft' : ''}`}>
                        <Icon size={27} strokeWidth={STROKE} aria-hidden="true" />
                      </span>
                    ) : (
                      <span className={`flex h-8 w-14 items-center justify-center rounded-full ${isActive ? 'bg-brand-soft' : ''}`}>
                        <Icon size={24} strokeWidth={STROKE} aria-hidden="true" />
                      </span>
                    )}
                    <span className={path === '/evidence' ? 'mt-9' : ''}>{label}</span>
                  </>
                )}
              </NavLink>
            ))}
          </div>
        </nav>
      )}
    </>
  );
}
