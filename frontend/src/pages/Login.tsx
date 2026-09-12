import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { login } from '../store/authSlice';
import { AppDispatch } from '../store/index';

export const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await dispatch(login({ username, password })).unwrap();
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-screen">
      <div className="auth-visual"><span className="eyebrow">ADAPTIVE DOCUMENT INTELLIGENCE</span><h1>Read deeper.<br /><em>Trust what you find.</em></h1><p>Turn scattered papers and reports into clear, cited answers with retrieval you can inspect.</p><div className="trust-points"><span>01 <strong>Private by design</strong></span><span>02 <strong>Evidence, not guesses</strong></span><span>03 <strong>Research-ready outputs</strong></span></div></div>
      <div className="panel auth-card">
        <div className="auth-brand"><span className="brand-mark">T</span><strong>TrustRAG</strong></div>
        <span className="eyebrow">WELCOME BACK</span><h2>Continue your research</h2><p className="muted">Sign in to your private evidence workspace.</p>
        
        {error && (
          <div className="notice error">{error}</div>
        )}

        <form onSubmit={handleSubmit} className="form-grid">
          <label className="field">
            <span>Username</span>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </label>

          <label className="field">
            <span>Password</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </label>

          <button type="submit" disabled={loading} className="primary full-button">
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <p className="muted auth-switch">
          New to TrustRAG? <a href="/register">Create an account</a>
        </p>
      </div>
    </div>
  );
};

export default Login;
