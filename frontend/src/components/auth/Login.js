import { useState } from 'react';
import { authAPI } from '../../services/api';
import './Login.css';

const Login = ({ onLogin }) => {
  const [selectedUser, setSelectedUser] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    if (!selectedUser || !password) {
      setError('Please enter username and password');
      return;
    }

    setLoading(true);
    
    try {
      const response = await authAPI.login(selectedUser, password);
      
      if (response.data && response.data.user) {
        const userData = response.data.user;
        
        // Store user data in localStorage
        localStorage.setItem('user', JSON.stringify(userData));
        
        // Call parent onLogin callback
        onLogin(userData);
      } else {
        setError('Invalid response from server');
      }
    } catch (err) {
      console.error('Login error:', err);
      setError(err.response?.data?.error || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1>MSC Evaluate</h1>
          <p>Sign in to continue</p>
        </div>
        
        {error && <div className="error-message">{error}</div>}
        
        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              value={selectedUser}
              onChange={(e) => setSelectedUser(e.target.value)}
              placeholder="Enter your username"
              disabled={loading}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              disabled={loading}
              required
            />
          </div>

          <button 
            type="submit" 
            className="btn-login"
            disabled={loading}
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <div className="login-info">
          <p className="info-title">Default Credentials:</p>
          <div className="credentials">
            <div className="credential-item">
              <strong>Admin:</strong> admin / admin123
            </div>
            <div className="credential-item">
              <strong>Tutor:</strong> tutor / tutor123
            </div>
            <div className="credential-item">
              <strong>Student:</strong> student / student123
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
