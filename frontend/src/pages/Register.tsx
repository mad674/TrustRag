import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { auth } from '../api/client';

export const Register = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);

    try {
      await auth.register(username, email, password);
      navigate('/login');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-screen">
      <div className="auth-visual"><span className="eyebrow">A CLEARER WAY TO RESEARCH</span><h1>Your corpus.<br /><em>Your evidence.</em></h1><p>Build a focused workspace for the documents that matter, then let every answer show its work.</p><div className="visual-orbit"><span>PDF</span><span>BM25</span><span>AI</span><span>QA</span></div></div>
      <div className="panel auth-card">
        <div className="auth-brand"><span className="brand-mark">T</span><strong>TrustRAG</strong></div>
        <span className="eyebrow">GET STARTED</span><h2>Create your workspace</h2><p className="muted">A private home for your documents and research questions.</p>
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
            <span>Email</span>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
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

          <label className="field">
            <span>Confirm password</span>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />
          </label>

          <button type="submit" disabled={loading} className="primary full-button">
            {loading ? 'Creating account...' : 'Register'}
          </button>
        </form>

        <p className="muted auth-switch">
          Already have an account? <a href="/login">Sign in</a>
        </p>
      </div>
    </div>
  );
};

export default Register;
