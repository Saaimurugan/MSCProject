import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Login.css';

const Login = ({ onLogin }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');

    // Hardcoded credentials
    const users = {
      admin: { password: 'admin123', role: 'admin' },
      student: { password: 'student123', role: 'student' }
    };

    const user = users[username.toLowerCase()];

    if (user && user.password === password) {
      // Store user info in localStorage
      const userInfo = {
        username: username.toLowerCase(),
        role: user.role
      };
      localStorage.setItem('user', JSON.stringify(userInfo));
      
      // Call parent callback
      onLogin(userInfo);
      
      // Navigate to dashboard
      navigate('/dashboard');
    } else {
      setError('Invalid username or password');
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1>🎓 AI Evaluate</h1>
          <p>Quiz Management System</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter username"
              autoFocus
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
              placeholder="Enter password"
              required
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button type="submit" className="btn-login">
            Login
          </button>
        </form>

        <div className="login-info">
          <p className="info-title">Demo Credentials:</p>
          <div className="credentials">
            <div className="credential-item">
              <strong>Admin:</strong> admin / admin123
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
