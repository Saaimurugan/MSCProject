import React, { useState, useEffect } from 'react';
import { usersAPI } from '../../services/api';
import './UserManagement.css';

const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [filterRole, setFilterRole] = useState('');
  
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    email: '',
    role: 'student',
    full_name: '',
    is_active: true
  });

  useEffect(() => {
    loadUsers();
  }, [filterRole]);

  const loadUsers = async () => {
    setLoading(true);
    setError('');
    try {
      const filters = filterRole ? { role: filterRole } : {};
      const response = await usersAPI.getUsers(filters);
      setUsers(response.data.users);
    } catch (err) {
      console.error('Error loading users:', err);
      setError(err.response?.data?.error || 'Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingUser(null);
    setFormData({
      username: '',
      password: '',
      email: '',
      role: 'student',
      full_name: '',
      is_active: true
    });
    setShowModal(true);
  };

  const handleEdit = (user) => {
    setEditingUser(user);
    setFormData({
      username: user.username,
      password: '',
      email: user.email,
      role: user.role,
      full_name: user.full_name || '',
      is_active: user.is_active
    });
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    try {
      if (editingUser) {
        // Update existing user
        const updateData = {
          email: formData.email,
          role: formData.role,
          full_name: formData.full_name,
          is_active: formData.is_active
        };
        if (formData.password) {
          updateData.password = formData.password;
        }
        await usersAPI.updateUser(editingUser.user_id, updateData);
      } else {
        // Create new user
        await usersAPI.createUser(formData);
      }
      
      setShowModal(false);
      loadUsers();
    } catch (err) {
      console.error('Error saving user:', err);
      setError(err.response?.data?.error || 'Failed to save user');
    }
  };

  const handleDelete = async (userId, username) => {
    if (!window.confirm(`Are you sure you want to delete user "${username}"?`)) {
      return;
    }
    
    try {
      await usersAPI.deleteUser(userId);
      loadUsers();
    } catch (err) {
      console.error('Error deleting user:', err);
      setError(err.response?.data?.error || 'Failed to delete user');
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  return (
    <div className="user-management">
      <div className="user-management-header">
        <h2>User Management</h2>
        <button className="btn-primary" onClick={handleCreate}>
          + Create User
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="filters">
        <label>
          Filter by Role:
          <select value={filterRole} onChange={(e) => setFilterRole(e.target.value)}>
            <option value="">All Roles</option>
            <option value="admin">Admin</option>
            <option value="tutor">Tutor</option>
            <option value="student">Student</option>
          </select>
        </label>
      </div>

      {loading ? (
        <div className="loading">Loading users...</div>
      ) : (
        <div className="users-table-container">
          <table className="users-table">
            <thead>
              <tr>
                <th>Username</th>
                <th>Email</th>
                <th>Full Name</th>
                <th>Role</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.length === 0 ? (
                <tr>
                  <td colSpan="6" className="no-data">No users found</td>
                </tr>
              ) : (
                users.map(user => (
                  <tr key={user.user_id}>
                    <td>{user.username}</td>
                    <td>{user.email}</td>
                    <td>{user.full_name || '-'}</td>
                    <td>
                      <span className={`role-badge role-${user.role}`}>
                        {user.role}
                      </span>
                    </td>
                    <td>
                      <span className={`status-badge ${user.is_active ? 'active' : 'inactive'}`}>
                        {user.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="actions">
                      <button 
                        className="btn-edit" 
                        onClick={() => handleEdit(user)}
                        title="Edit user"
                      >
                        Edit
                      </button>
                      <button 
                        className="btn-delete" 
                        onClick={() => handleDelete(user.user_id, user.username)}
                        title="Delete user"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editingUser ? 'Edit User' : 'Create New User'}</h3>
              <button className="modal-close" onClick={() => setShowModal(false)}>×</button>
            </div>
            
            <form onSubmit={handleSubmit} className="user-form">
              <div className="form-group">
                <label htmlFor="username">Username *</label>
                <input
                  id="username"
                  name="username"
                  type="text"
                  value={formData.username}
                  onChange={handleInputChange}
                  required
                  disabled={editingUser !== null}
                />
                {editingUser && <small>Username cannot be changed</small>}
              </div>

              <div className="form-group">
                <label htmlFor="password">
                  Password {editingUser ? '(leave blank to keep current)' : '*'}
                </label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  required={!editingUser}
                />
              </div>

              <div className="form-group">
                <label htmlFor="email">Email *</label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="full_name">Full Name</label>
                <input
                  id="full_name"
                  name="full_name"
                  type="text"
                  value={formData.full_name}
                  onChange={handleInputChange}
                />
              </div>

              <div className="form-group">
                <label htmlFor="role">Role *</label>
                <select
                  id="role"
                  name="role"
                  value={formData.role}
                  onChange={handleInputChange}
                  required
                >
                  <option value="student">Student</option>
                  <option value="tutor">Tutor</option>
                  <option value="admin">Admin</option>
                </select>
              </div>

              <div className="form-group checkbox-group">
                <label>
                  <input
                    name="is_active"
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={handleInputChange}
                  />
                  Active
                </label>
              </div>

              <div className="form-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  {editingUser ? 'Update User' : 'Create User'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserManagement;
