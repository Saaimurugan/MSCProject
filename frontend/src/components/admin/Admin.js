import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthService } from '../../services/auth';
import { adminAPI } from '../../services/api';
import './Admin.css';

const Admin = () => {
  const [activeTab, setActiveTab] = useState('users');
  const [users, setUsers] = useState([]);
  const [usageLogs, setUsageLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const navigate = useNavigate();

  // New user form state
  const [newUser, setNewUser] = useState({
    name: '',
    email: '',
    password: '',
    role: 'student'
  });

  useEffect(() => {
    // Check if user is admin
    if (!AuthService.hasRole('admin')) {
      navigate('/dashboard');
      return;
    }

    if (activeTab === 'users') {
      loadUsers();
    } else if (activeTab === 'logs') {
      loadUsageLogs();
    }
  }, [activeTab, navigate]);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const response = await adminAPI.getUsers();
      setUsers(response.data.users);
    } catch (error) {
      setError('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const loadUsageLogs = async () => {
    try {
      setLoading(true);
      const response = await adminAPI.getUsageLogs();
      setUsageLogs(response.data.logs);
    } catch (error) {
      setError('Failed to load usage logs');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      await adminAPI.createUser(newUser);
      setSuccess('User created successfully');
      setNewUser({ name: '', email: '', password: '', role: 'student' });
      loadUsers();
    } catch (error) {
      setError('Failed to create user');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!window.confirm('Are you sure you want to delete this user?')) {
      return;
    }

    try {
      setLoading(true);
      await adminAPI.deleteUser(userId);
      setSuccess('User deleted successfully');
      loadUsers();
    } catch (error) {
      setError('Failed to delete user');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleAdmin = async (userId, currentRole) => {
    const newRole = currentRole === 'admin' ? 'student' : 'admin';
    
    try {
      setLoading(true);
      await adminAPI.updateUserRole(userId, newRole);
      setSuccess(`User role updated to ${newRole}`);
      loadUsers();
    } catch (error) {
      setError('Failed to update user role');
    } finally {
      setLoading(false);
    }
  };

  const clearMessages = () => {
    setError('');
    setSuccess('');
  };

  return (
    <div className="admin-container">
      <header className="admin-header">
        <div className="header-content">
          <h1>⚙️ Admin Panel</h1>
          <button onClick={() => navigate('/dashboard')} className="btn-back">
            ← Back to Dashboard
          </button>
        </div>
      </header>

      <div className="admin-content">
        <div className="admin-tabs">
          <button 
            className={`tab-btn ${activeTab === 'users' ? 'active' : ''}`}
            onClick={() => setActiveTab('users')}
          >
            👥 User Management
          </button>
          <button 
            className={`tab-btn ${activeTab === 'logs' ? 'active' : ''}`}
            onClick={() => setActiveTab('logs')}
          >
            📊 Usage Logs
          </button>
        </div>

        {error && (
          <div className="message error-message">
            {error}
            <button onClick={clearMessages} className="close-btn">×</button>
          </div>
        )}

        {success && (
          <div className="message success-message">
            {success}
            <button onClick={clearMessages} className="close-btn">×</button>
          </div>
        )}

        {activeTab === 'users' && (
          <div className="users-tab">
            <div className="add-user-section">
              <h3>Add New User</h3>
              <form onSubmit={handleCreateUser} className="add-user-form">
                <div className="form-row">
                  <input
                    type="text"
                    placeholder="Full Name"
                    value={newUser.name}
                    onChange={(e) => setNewUser({...newUser, name: e.target.value})}
                    required
                  />
                  <input
                    type="email"
                    placeholder="Email"
                    value={newUser.email}
                    onChange={(e) => setNewUser({...newUser, email: e.target.value})}
                    required
                  />
                </div>
                <div className="form-row">
                  <input
                    type="password"
                    placeholder="Password"
                    value={newUser.password}
                    onChange={(e) => setNewUser({...newUser, password: e.target.value})}
                    required
                  />
                  <select
                    value={newUser.role}
                    onChange={(e) => setNewUser({...newUser, role: e.target.value})}
                  >
                    <option value="student">Student</option>
                    <option value="tutor">Tutor</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>
                <button type="submit" disabled={loading} className="btn-create-user">
                  {loading ? 'Creating...' : 'Create User'}
                </button>
              </form>
            </div>

            <div className="users-list-section">
              <h3>Existing Users</h3>
              {loading ? (
                <div className="loading">Loading users...</div>
              ) : (
                <div className="users-table">
                  <div className="table-header">
                    <span>Name</span>
                    <span>Email</span>
                    <span>Role</span>
                    <span>Created</span>
                    <span>Actions</span>
                  </div>
                  {users.map((user) => (
                    <div key={user.user_id} className="table-row">
                      <span>{user.name}</span>
                      <span>{user.email}</span>
                      <span className={`role-badge ${user.role}`}>{user.role}</span>
                      <span>{new Date(user.created_at).toLocaleDateString()}</span>
                      <div className="actions">
                        <button
                          onClick={() => handleToggleAdmin(user.user_id, user.role)}
                          className={`btn-toggle ${user.role === 'admin' ? 'remove-admin' : 'make-admin'}`}
                          disabled={loading}
                        >
                          {user.role === 'admin' ? 'Remove Admin' : 'Make Admin'}
                        </button>
                        <button
                          onClick={() => handleDeleteUser(user.user_id)}
                          className="btn-delete"
                          disabled={loading}
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'logs' && (
          <div className="logs-tab">
            <h3>Usage Logs</h3>
            {loading ? (
              <div className="loading">Loading usage logs...</div>
            ) : (
              <div className="logs-table">
                <div className="table-header">
                  <span>User</span>
                  <span>Action</span>
                  <span>Resource</span>
                  <span>Timestamp</span>
                  <span>IP Address</span>
                </div>
                {usageLogs.map((log, index) => (
                  <div key={index} className="table-row">
                    <span>{log.user_name}</span>
                    <span className={`action-badge ${log.action}`}>{log.action}</span>
                    <span>{log.resource}</span>
                    <span>{new Date(log.timestamp).toLocaleString()}</span>
                    <span>{log.ip_address}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Admin;