
import { BrowserRouter as Router, Routes, Route, Navigate, NavLink, Link } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { RootState } from './store';
import { useDispatch } from 'react-redux';
import { logout } from './store/authSlice';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Chat from './pages/Chat';
import Upload from './pages/Upload';
import Evaluation from './pages/Evaluation';
import DocumentDetail from './pages/DocumentDetail';
import Compare from './pages/Compare';
import Reports from './pages/Reports';
import Settings from './pages/Settings';

function App() {
  const token = useSelector((state: RootState) => state.auth.token);
  const username = useSelector((state: RootState) => state.auth.user?.username);
  const dispatch = useDispatch();

  const shell = (child: JSX.Element) => {
    const links = [
      ['/dashboard', 'Library', 'Your evidence corpus'],
      ['/chat', 'Ask TrustRAG', 'Grounded answers'],
      ['/upload', 'Add documents', 'Build your corpus'],
      ['/compare', 'Compare', 'Find differences'],
      ['/reports', 'Reports', 'Export research'],
      ['/evaluation', 'Evaluation', 'Measure retrieval'],
    ];
    return <div className="product-shell">
      <aside className="sidebar">
        <Link to="/dashboard" className="brand-lockup"><span className="brand-mark">T</span><span><strong>TrustRAG</strong><small>Evidence intelligence</small></span></Link>
        <div className="sidebar-label">Workspace</div>
        <nav className="side-nav">{links.map(([to, label, hint]) => <NavLink key={to} to={to} className={({ isActive }) => isActive ? 'side-link active' : 'side-link'}><span className="side-icon">{label.slice(0, 1)}</span><span><strong>{label}</strong><small>{hint}</small></span></NavLink>)}</nav>
        <div className="sidebar-spacer" />
        <NavLink to="/settings" className={({ isActive }) => isActive ? 'side-link active' : 'side-link'}><span className="side-icon">S</span><span><strong>AI settings</strong><small>Provider and privacy</small></span></NavLink>
        <div className="profile-strip"><span className="avatar">{String((username || 'U')).slice(0, 1).toUpperCase()}</span><span><strong>{username || 'Researcher'}</strong><small>Private workspace</small></span><button aria-label="Sign out" onClick={() => dispatch(logout())}>↗</button></div>
      </aside>
      <div className="main-area">
        <header className="mobile-header"><Link to="/dashboard" className="brand-lockup"><span className="brand-mark">T</span><strong>TrustRAG</strong></Link><button className="secondary compact" onClick={() => dispatch(logout())}>Sign out</button></header>
        <div className="workspace-topbar"><span>Evidence workspace</span><span className="system-status"><i /> All systems operational</span></div>
        {child}
      </div>
    </div>;
  };
  
  return (
    <Router>
      <Routes>
        {!token ? (
          <>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="*" element={<Navigate to="/login" replace />} />
          </>
        ) : (
          <>
            <Route path="/dashboard" element={shell(<Dashboard />)} />
            <Route path="/chat" element={shell(<Chat />)} />
            <Route path="/upload" element={shell(<Upload />)} />
              <Route path="/evaluation" element={shell(<Evaluation />)} />
              <Route path="/documents" element={shell(<Dashboard />)} />
              <Route path="/documents/:id" element={shell(<DocumentDetail />)} />
              <Route path="/compare" element={shell(<Compare />)} />
              <Route path="/reports" element={shell(<Reports />)} />
              <Route path="/settings" element={shell(<Settings />)} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </>
        )}
      </Routes>
    </Router>
  );
}

export default App;
