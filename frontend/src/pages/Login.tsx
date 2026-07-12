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
      <div className="panel auth-card">
        <h1>TrustRAG</h1>
        <h2>Sign in</h2>
        
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

          <button
            type="submit"
            disabled={loading}
            className="primary"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <p className="muted auth-switch">
          Don't have an account?{' '}
          <a href="/register">
            Register here
          </a>
        </p>
      </div>
    </div>
  );
};

export default Login;
