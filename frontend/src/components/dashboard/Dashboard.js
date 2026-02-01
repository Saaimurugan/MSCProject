import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { templatesAPI } from '../../services/api';
import { AuthService } from '../../services/auth';
import './Dashboard.css';

const Dashboard = () => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedSubject, setSelectedSubject] = useState('');
  const [selectedCourse, setCourse] = useState('');
  const navigate = useNavigate();
  const user = AuthService.getUser();

  useEffect(() => {
    loadTemplates();
  }, [selectedSubject, selectedCourse]);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      const response = await templatesAPI.getTemplates(selectedSubject, selectedCourse);
      setTemplates(response.data.templates);
    } catch (error) {
      setError('Failed to load templates');
    } finally {
      setLoading(false);
    }
  };

  const handleTemplateClick = (templateId) => {
    navigate(`/quiz/${templateId}`);
  };

  const handleCreateTemplate = () => {
    navigate('/template/create');
  };

  const handleLogout = () => {
    AuthService.logout();
  };

  // Group templates by subject and course
  const groupedTemplates = templates.reduce((acc, template) => {
    const key = `${template.subject} - ${template.course}`;
    if (!acc[key]) {
      acc[key] = [];
    }
    acc[key].push(template);
    return acc;
  }, {});

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <div className="header-content">
          <h1>📝 MSC Evaluate Dashboard</h1>
          <div className="user-info">
            <span>Welcome, {user?.name} ({user?.role})</span>
            <button onClick={handleLogout} className="btn-logout">Logout</button>
          </div>
        </div>
      </header>

      <div className="dashboard-content">
        <div className="dashboard-controls">
          <div className="filters">
            <select 
              value={selectedSubject} 
              onChange={(e) => setSelectedSubject(e.target.value)}
              className="filter-select"
            >
              <option value="">All Subjects</option>
              <option value="Computer Science">Computer Science</option>
              <option value="Mathematics">Mathematics</option>
              <option value="Physics">Physics</option>
              <option value="Chemistry">Chemistry</option>
            </select>
            
            <select 
              value={selectedCourse} 
              onChange={(e) => setCourse(e.target.value)}
              className="filter-select"
            >
              <option value="">All Courses</option>
              <option value="MSC-101">MSC-101</option>
              <option value="MSC-102">MSC-102</option>
              <option value="MSC-201">MSC-201</option>
              <option value="MSC-202">MSC-202</option>
            </select>
          </div>

          {AuthService.hasAnyRole(['admin', 'tutor']) && (
            <button onClick={handleCreateTemplate} className="btn-create">
              + Create Template
            </button>
          )}
        </div>

        {error && <div className="error-message">{error}</div>}

        {loading ? (
          <div className="loading">
            <div className="spinner"></div>
            <p>Loading templates...</p>
          </div>
        ) : (
          <div className="templates-grid">
            {Object.keys(groupedTemplates).length === 0 ? (
              <div className="no-templates">
                <p>No templates found. {AuthService.hasAnyRole(['admin', 'tutor']) ? 'Create your first template!' : 'Check back later for new assignments.'}</p>
              </div>
            ) : (
              Object.entries(groupedTemplates).map(([subjectCourse, templateList]) => (
                <div key={subjectCourse} className="subject-section">
                  <h3 className="subject-title">{subjectCourse}</h3>
                  <div className="template-cards">
                    {templateList.map((template) => (
                      <div 
                        key={template.template_id} 
                        className="template-card"
                        onClick={() => handleTemplateClick(template.template_id)}
                      >
                        <div className="card-header">
                          <h4>{template.title}</h4>
                          <span className="question-count">{template.question_count} questions</span>
                        </div>
                        <div className="card-footer">
                          <span className="created-date">
                            Created: {new Date(template.created_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        <div className="dashboard-nav">
          <button onClick={() => navigate('/profile')} className="nav-btn">
            👤 Profile
          </button>
          <button onClick={() => navigate('/reports')} className="nav-btn">
            📊 Reports
          </button>
          {AuthService.hasRole('admin') && (
            <button onClick={() => navigate('/admin')} className="nav-btn">
              ⚙️ Admin
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;