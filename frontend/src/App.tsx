
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { RootState } from './store';
import { useDispatch } from 'react-redux';
import { logout } from './store/authSlice';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Chat from './pages/Chat';
import Upload from './pages/Upload';

function ProtectedRoute({ children }: { children: JSX.Element }) {
  const token = useSelector((state: RootState) => state.auth.token);
  
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
}

function App() {
  const token = useSelector((state: RootState) => state.auth.token);
  const dispatch = useDispatch();

  const shell = (child: JSX.Element) => (
    <div className="app-shell">
      <header className="panel header">
        <div className="brand">
          <h1>TrustRAG</h1>
          <p>Adaptive, explainable document intelligence</p>
        </div>
        <nav className="nav">
          <a href="/dashboard">Library</a>
          <a href="/upload">Upload</a>
          <a href="/chat">Chat</a>
          <button className="secondary compact" onClick={() => dispatch(logout())}>Logout</button>
        </nav>
      </header>
      {child}
    </div>
  );
  
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
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </>
        )}
      </Routes>
    </Router>
  );
}

export default App;
