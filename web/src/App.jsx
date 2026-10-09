import { useState } from 'react';
import { NavLink, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import { Camera, ChartColumn, HardHat, ListTodo, Trophy } from 'lucide-react';
import { STROKE } from './components/ui.jsx';
import TaskInput from './pages/TaskInput.jsx';
import Checklist from './pages/Checklist.jsx';
import Todo from './pages/Todo.jsx';
import Evidence from './pages/Evidence.jsx';
import Ranking from './pages/Ranking.jsx';
import Eval from './pages/Eval.jsx';
import WorkerForm from './pages/WorkerForm.jsx';
import LoginSample from './pages/LoginSample.jsx';
import Tbm from './pages/Tbm.jsx';
import Incidents from './pages/Incidents.jsx';
import Review from './pages/Review.jsx';
import SessionHeader from './components/SessionHeader.jsx';
import { clearSession, readSession, saveSession } from './lib/session.js';

const tabs = [
  ['/', '작업', HardHat],
  ['/todo', '할 일', ListTodo],
  ['/evidence', '사진', Camera],
  ['/ranking', '기록', Trophy],
  ['/eval', '평가', ChartColumn],
];

function taskId() {
  try { return localStorage.getItem('banjang.taskId'); }
  catch { return null; }
}

function RequireSession({ user, role, children }) {
  if (!user) return <Navigate to="/login" replace />;
  if (role && user.role !== role) return <Navigate to={user.role === 'worker' ? `/worker/${taskId() || 'missing'}` : '/'} replace />;
  return children;
}

export default function App() {
  const [user, setUser] = useState(readSession);
  const location = useLocation();
  const navigate = useNavigate();
  const standalone = location.pathname.startsWith('/worker/') || location.pathname === '/login';

  function login(nextUser) {
    saveSession(nextUser);
    setUser(nextUser);
    navigate(nextUser.role === 'worker' ? `/worker/${taskId() || 'missing'}` : '/');
  }

  function clockOut() {
    clearSession();
    setUser(null);
    navigate('/login', { replace: true });
  }

  return (
    <>
      {user && location.pathname !== '/login' && <SessionHeader user={user} onClockOut={clockOut} />}
      <Routes>
        <Route path="/" element={<RequireSession user={user} role="admin"><TaskInput /></RequireSession>} />
        <Route path="/checklist" element={<RequireSession user={user} role="admin"><Checklist /></RequireSession>} />
        <Route path="/todo" element={<RequireSession user={user} role="admin"><Todo /></RequireSession>} />
        <Route path="/evidence" element={<RequireSession user={user} role="admin"><Evidence /></RequireSession>} />
        <Route path="/ranking" element={<RequireSession user={user} role="admin"><Ranking /></RequireSession>} />
        <Route path="/eval" element={<RequireSession user={user} role="admin"><Eval /></RequireSession>} />
        <Route path="/worker/:taskId" element={<RequireSession user={user} role="worker"><WorkerForm /></RequireSession>} />
        <Route path="/tbm" element={<RequireSession user={user} role="admin"><Tbm /></RequireSession>} />
        <Route path="/incidents" element={<RequireSession user={user} role="admin"><Incidents /></RequireSession>} />
        <Route path="/reviews" element={<RequireSession user={user} role="admin"><Review /></RequireSession>} />
        <Route path="/login" element={<LoginSample onLogin={login} />} />
        <Route path="*" element={<Navigate to={user ? (user.role === 'worker' ? `/worker/${taskId() || 'missing'}` : '/') : '/login'} replace />} />
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
