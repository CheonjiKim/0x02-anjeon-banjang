import { useState } from 'react';
import { NavLink, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import { CalendarDays, Camera, ClipboardCheck, Clock3, FileText, HardHat, ListTodo, ShieldAlert, Trophy, UsersRound } from 'lucide-react';
import { STROKE } from './components/ui.jsx';
import Calendar from './pages/Calendar.jsx';
import Workers from './pages/Workers.jsx';
import Jsa from './pages/Jsa.jsx';
import WorkerTask from './pages/WorkerTask.jsx';
import WorkerReports from './pages/WorkerReports.jsx';
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
import Attendance from './pages/Attendance.jsx';
import Training from './pages/Training.jsx';
import SessionHeader from './components/SessionHeader.jsx';
import { clearSession, readSession, saveSession } from './lib/session.js';

const tabs = [
  ['/', 'TBM', ClipboardCheck],
  ['/workers', '작업자관리', UsersRound],
  ['/calendar', '캘린더', CalendarDays],
  ['/jsa', 'JSA', FileText],
  ['/ranking', '기록', Trophy],
];
const workerTabs = [
  ['/worker/task', '오늘작업', HardHat],
  ['/worker/photos', '사진', Camera],
  ['/worker/calendar', '캘린더', CalendarDays],
  ['/worker/records', '내 기록', Trophy],
];

function taskId() {
  try { return localStorage.getItem('banjang.taskId'); }
  catch { return null; }
}

function RequireSession({ user, role, children }) {
  if (!user) return <Navigate to="/login" replace />;
  if (role && user.role !== role) return <Navigate to={user.role === 'worker' ? '/worker/task' : '/'} replace />;
  return children;
}

export default function App() {
  const [user, setUser] = useState(readSession);
  const location = useLocation();
  const navigate = useNavigate();
  const standalone = location.pathname === '/login';
  const isWorker = user?.role === 'worker';
  const activeTabs = isWorker ? workerTabs : tabs;

  function login(nextUser) {
    saveSession(nextUser);
    setUser(nextUser);
    navigate(nextUser.role === 'worker' ? '/worker/task' : '/');
  }

  function clockOut() {
    clearSession();
    setUser(null);
    navigate('/login', { replace: true });
  }

  return (
    <div className="flex h-dvh flex-col">
      {user && location.pathname !== '/login' && location.pathname !== '/' && <SessionHeader user={user} onClockOut={clockOut} />}
      <div className="relative min-h-0 flex-1 overflow-auto">
      <Routes>
        <Route path="/" element={<RequireSession user={user} role="admin"><TaskInput onClockOut={clockOut} /></RequireSession>} />
        <Route path="/workers" element={<RequireSession user={user} role="admin"><Workers /></RequireSession>} />
        <Route path="/calendar" element={<RequireSession user={user} role="admin"><Calendar /></RequireSession>} />
        <Route path="/jsa" element={<RequireSession user={user} role="admin"><Jsa /></RequireSession>} />
        <Route path="/worker/calendar" element={<RequireSession user={user} role="worker"><Calendar worker /></RequireSession>} />
        <Route path="/worker/photos" element={<RequireSession user={user} role="worker"><WorkerReports /></RequireSession>} />
        <Route path="/checklist" element={<RequireSession user={user} role="admin"><Checklist /></RequireSession>} />
        <Route path="/checklist/:taskId" element={<RequireSession user={user} role="admin"><Checklist /></RequireSession>} />
        <Route path="/todo" element={<RequireSession user={user} role="admin"><Todo /></RequireSession>} />
        <Route path="/evidence" element={<RequireSession user={user} role="admin"><Evidence /></RequireSession>} />
        <Route path="/ranking" element={<RequireSession user={user} role="admin"><Ranking /></RequireSession>} />
        <Route path="/eval" element={<RequireSession user={user} role="admin"><Eval /></RequireSession>} />
        <Route path="/worker/task" element={<RequireSession user={user} role="worker"><WorkerTask /></RequireSession>} />
        <Route path="/worker/attendance" element={<RequireSession user={user} role="worker"><Attendance /></RequireSession>} />
        <Route path="/worker/training" element={<RequireSession user={user} role="worker"><Training /></RequireSession>} />
        <Route path="/worker/incidents" element={<RequireSession user={user} role="worker"><Incidents worker /></RequireSession>} />
        <Route path="/worker/records" element={<RequireSession user={user} role="worker"><Ranking /></RequireSession>} />
        <Route path="/worker/:taskId" element={<RequireSession user={user} role="worker"><WorkerForm /></RequireSession>} />
        <Route path="/tbm" element={<RequireSession user={user} role="admin"><Tbm /></RequireSession>} />
        <Route path="/incidents" element={<RequireSession user={user} role="admin"><Incidents /></RequireSession>} />
        <Route path="/reviews" element={<RequireSession user={user} role="admin"><Review /></RequireSession>} />
        <Route path="/login" element={<LoginSample onLogin={login} />} />
        <Route path="*" element={<Navigate to={user ? (user.role === 'worker' ? '/worker/task' : '/') : '/login'} replace />} />
      </Routes>
      </div>
      {!standalone && user && (
        <nav aria-label="주 메뉴" className="fixed inset-x-0 bottom-0 z-30 rounded-t-[28px] bg-white pb-safe shadow-[0_-4px_24px_rgba(0,0,0,0.06)]">
          <div className={`grid h-[68px] ${isWorker ? 'grid-cols-4' : 'grid-cols-5'}`}>
            {activeTabs.map(([path, label, Icon]) => (
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
    </div>
  );
}
