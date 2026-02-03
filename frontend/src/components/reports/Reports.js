import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthService } from '../../services/auth';
import { reportsAPI } from '../../services/api';
import './Reports.css';

const Reports = () => {
  const [activeTab, setActiveTab] = useState('personal');
  const [reports, setReports] = useState([]);
  const [templateReports, setTemplateReports] = useState([]);
  const [allReports, setAllReports] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [dateRange, setDateRange] = useState({
    startDate: '',
    endDate: ''
  });
  const navigate = useNavigate();
  const user = AuthService.getUser();

  useEffect(() => {
    loadReports();
  }, [activeTab, selectedTemplate, dateRange]);

  const loadReports = async () => {
    try {
      setLoading(true);
      setError('');

      if (activeTab === 'personal') {
        const response = await reportsAPI.getUserReports(user.user_id);
        setReports(response.data.reports);
      } else if (activeTab === 'template' && selectedTemplate) {
        const response = await reportsAPI.getTemplateReports(selectedTemplate);
        setTemplateReports(response.data.reports);
      } else if (activeTab === 'all' && AuthService.hasAnyRole(['admin', 'tutor'])) {
        const response = await reportsAPI.getAllReports();
        setAllReports(response.data.reports);
      }
    } catch (error) {
      setError('Failed to load reports');
    } finally {
      setLoading(false);
    }
  };

  const calculateStats = (reportsList) => {
    if (!reportsList.length) return { avgScore: 0, totalQuizzes: 0, passRate: 0 };

    const totalQuizzes = reportsList.length;
    const totalScore = reportsList.reduce((sum, report) => sum + report.score, 0);
    const avgScore = totalScore / totalQuizzes;
    const passedQuizzes = reportsList.filter(report => report.score >= 60).length;
    const passRate = (passedQuizzes / totalQuizzes) * 100;

    return { avgScore: avgScore.toFixed(1), totalQuizzes, passRate: passRate.toFixed(1) };
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'excellent';
    if (score >= 60) return 'good';
    if (score >= 40) return 'average';
    return 'poor';
  };

  const exportToCSV = (data, filename) => {
    const headers = ['Date', 'Template', 'Subject', 'Course', 'Score', 'Time Taken', 'Status'];
    const csvContent = [
      headers.join(','),
      ...data.map(report => [
        new Date(report.submitted_at).toLocaleDateString(),
        report.template_title,
        report.subject,
        report.course,
        report.score,
        `${report.time_taken}s`,
        report.score >= 60 ? 'Passed' : 'Failed'
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const personalStats = calculateStats(reports);
  const templateStats = calculateStats(templateReports);
  const allStats = calculateStats(allReports);

  return (
    <div className="reports-container">
      <header className="reports-header">
        <div className="header-content">
          <h1>📊 Reports & Analytics</h1>
          <button onClick={() => navigate('/dashboard')} className="btn-back">
            ← Back to Dashboard
          </button>
        </div>
      </header>

      <div className="reports-content">
        <div className="reports-tabs">
          <button 
            className={`tab-btn ${activeTab === 'personal' ? 'active' : ''}`}
            onClick={() => setActiveTab('personal')}
          >
            📈 My Performance
          </button>
          {AuthService.hasAnyRole(['admin', 'tutor']) && (
            <>
              <button 
                className={`tab-btn ${activeTab === 'template' ? 'active' : ''}`}
                onClick={() => setActiveTab('template')}
              >
                📋 Template Reports
              </button>
              <button 
                className={`tab-btn ${activeTab === 'all' ? 'active' : ''}`}
                onClick={() => setActiveTab('all')}
              >
                🌐 All Reports
              </button>
            </>
          )}
        </div>

        {error && (
          <div className="error-message">
            {error}
            <button onClick={() => setError('')} className="close-btn">×</button>
          </div>
        )}

        {/* Personal Reports Tab */}
        {activeTab === 'personal' && (
          <div className="personal-tab">
            <div className="stats-cards">
              <div className="stat-card">
                <div className="stat-value">{personalStats.avgScore}%</div>
                <div className="stat-label">Average Score</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{personalStats.totalQuizzes}</div>
                <div className="stat-label">Quizzes Taken</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{personalStats.passRate}%</div>
                <div className="stat-label">Pass Rate</div>
              </div>
            </div>

            <div className="reports-section">
              <div className="section-header">
                <h3>My Quiz History</h3>
                <button 
                  onClick={() => exportToCSV(reports, 'my-quiz-reports.csv')}
                  className="btn-export"
                  disabled={!reports.length}
                >
                  📥 Export CSV
                </button>
              </div>

              {loading ? (
                <div className="loading">Loading reports...</div>
              ) : (
                <div className="reports-table">
                  <div className="table-header">
                    <span>Date</span>
                    <span>Template</span>
                    <span>Subject</span>
                    <span>Score</span>
                    <span>Time</span>
                    <span>Status</span>
                  </div>
                  {reports.map((report) => (
                    <div key={report.quiz_id} className="table-row">
                      <span>{new Date(report.submitted_at).toLocaleDateString()}</span>
                      <span>{report.template_title}</span>
                      <span>{report.subject} - {report.course}</span>
                      <span className={`score ${getScoreColor(report.score)}`}>
                        {report.score}%
                      </span>
                      <span>{report.time_taken}s</span>
                      <span className={`status ${report.score >= 60 ? 'passed' : 'failed'}`}>
                        {report.score >= 60 ? 'Passed' : 'Failed'}
                      </span>
                    </div>
                  ))}
                  {reports.length === 0 && (
                    <div className="no-data">No quiz reports found</div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Template Reports Tab */}
        {activeTab === 'template' && AuthService.hasAnyRole(['admin', 'tutor']) && (
          <div className="template-tab">
            <div className="filters">
              <select
                value={selectedTemplate}
                onChange={(e) => setSelectedTemplate(e.target.value)}
                className="template-select"
              >
                <option value="">Select a template...</option>
                <option value="template-1">Computer Science - Data Structures</option>
                <option value="template-2">Mathematics - Calculus I</option>
                <option value="template-3">Physics - Mechanics</option>
              </select>
            </div>

            {selectedTemplate && (
              <>
                <div className="stats-cards">
                  <div className="stat-card">
                    <div className="stat-value">{templateStats.avgScore}%</div>
                    <div className="stat-label">Average Score</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-value">{templateStats.totalQuizzes}</div>
                    <div className="stat-label">Submissions</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-value">{templateStats.passRate}%</div>
                    <div className="stat-label">Pass Rate</div>
                  </div>
                </div>

                <div className="reports-section">
                  <div className="section-header">
                    <h3>Template Performance</h3>
                    <button 
                      onClick={() => exportToCSV(templateReports, `template-${selectedTemplate}-reports.csv`)}
                      className="btn-export"
                      disabled={!templateReports.length}
                    >
                      📥 Export CSV
                    </button>
                  </div>

                  {loading ? (
                    <div className="loading">Loading template reports...</div>
                  ) : (
                    <div className="reports-table">
                      <div className="table-header">
                        <span>Student</span>
                        <span>Date</span>
                        <span>Score</span>
                        <span>Time</span>
                        <span>Status</span>
                      </div>
                      {templateReports.map((report) => (
                        <div key={report.quiz_id} className="table-row">
                          <span>{report.student_name}</span>
                          <span>{new Date(report.submitted_at).toLocaleDateString()}</span>
                          <span className={`score ${getScoreColor(report.score)}`}>
                            {report.score}%
                          </span>
                          <span>{report.time_taken}s</span>
                          <span className={`status ${report.score >= 60 ? 'passed' : 'failed'}`}>
                            {report.score >= 60 ? 'Passed' : 'Failed'}
                          </span>
                        </div>
                      ))}
                      {templateReports.length === 0 && (
                        <div className="no-data">No reports found for this template</div>
                      )}
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        )}

        {/* All Reports Tab */}
        {activeTab === 'all' && AuthService.hasAnyRole(['admin', 'tutor']) && (
          <div className="all-tab">
            <div className="filters">
              <input
                type="date"
                value={dateRange.startDate}
                onChange={(e) => setDateRange({...dateRange, startDate: e.target.value})}
                className="date-input"
              />
              <span>to</span>
              <input
                type="date"
                value={dateRange.endDate}
                onChange={(e) => setDateRange({...dateRange, endDate: e.target.value})}
                className="date-input"
              />
            </div>

            <div className="stats-cards">
              <div className="stat-card">
                <div className="stat-value">{allStats.avgScore}%</div>
                <div className="stat-label">Overall Average</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{allStats.totalQuizzes}</div>
                <div className="stat-label">Total Submissions</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{allStats.passRate}%</div>
                <div className="stat-label">Overall Pass Rate</div>
              </div>
            </div>

            <div className="reports-section">
              <div className="section-header">
                <h3>All Quiz Reports</h3>
                <button 
                  onClick={() => exportToCSV(allReports, 'all-quiz-reports.csv')}
                  className="btn-export"
                  disabled={!allReports.length}
                >
                  📥 Export CSV
                </button>
              </div>

              {loading ? (
                <div className="loading">Loading all reports...</div>
              ) : (
                <div className="reports-table">
                  <div className="table-header">
                    <span>Student</span>
                    <span>Template</span>
                    <span>Date</span>
                    <span>Score</span>
                    <span>Status</span>
                  </div>
                  {allReports.map((report) => (
                    <div key={report.quiz_id} className="table-row">
                      <span>{report.student_name}</span>
                      <span>{report.template_title}</span>
                      <span>{new Date(report.submitted_at).toLocaleDateString()}</span>
                      <span className={`score ${getScoreColor(report.score)}`}>
                        {report.score}%
                      </span>
                      <span className={`status ${report.score >= 60 ? 'passed' : 'failed'}`}>
                        {report.score >= 60 ? 'Passed' : 'Failed'}
                      </span>
                    </div>
                  ))}
                  {allReports.length === 0 && (
                    <div className="no-data">No reports found</div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Reports;