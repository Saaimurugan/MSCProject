import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { resultsAPI } from '../../services/api';
import './ResultsReport.css';

const ResultsReport = () => {
  const navigate = useNavigate();
  const [results, setResults] = useState([]);
  const [filteredResults, setFilteredResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedResult, setSelectedResult] = useState(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  
  // Filter states
  const [studentFilter, setStudentFilter] = useState('');
  const [courseFilter, setCourseFilter] = useState('');
  const [subjectFilter, setSubjectFilter] = useState('');
  
  // Unique values for filters
  const [courses, setCourses] = useState([]);
  const [subjects, setSubjects] = useState([]);

  useEffect(() => {
    loadResults();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [studentFilter, courseFilter, subjectFilter, results]);

  const loadResults = async () => {
    try {
      setLoading(true);
      const response = await resultsAPI.getAllResults();
      setResults(response.data.results);
      
      // Extract unique courses and subjects (filter out empty/null values)
      const uniqueCourses = [...new Set(response.data.results
        .map(r => r.course)
        .filter(c => c && c.trim())
      )].sort();
      const uniqueSubjects = [...new Set(response.data.results
        .map(r => r.subject)
        .filter(s => s && s.trim())
      )].sort();
      setCourses(uniqueCourses);
      setSubjects(uniqueSubjects);
    } catch (error) {
      setError('Failed to load results');
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...results];

    if (studentFilter) {
      filtered = filtered.filter(r => 
        r.student_name.toLowerCase().includes(studentFilter.toLowerCase())
      );
    }

    if (courseFilter) {
      filtered = filtered.filter(r => r.course === courseFilter);
    }

    if (subjectFilter) {
      filtered = filtered.filter(r => r.subject === subjectFilter);
    }

    setFilteredResults(filtered);
  };

  const clearFilters = () => {
    setStudentFilter('');
    setCourseFilter('');
    setSubjectFilter('');
  };

  const getScoreClass = (score) => {
    if (score >= 90) return 'excellent';
    if (score >= 70) return 'good';
    if (score >= 50) return 'fair';
    return 'poor';
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    
    // Add 5 hours 30 minutes to convert UTC to IST
    const istOffset = 5.5 * 60 * 60 * 1000; // IST is UTC+5:30
    const istDate = new Date(date.getTime() + istOffset);
    
    // Format as dd/mm/yyyy (Indian date format) - use regular methods, not UTC
    const day = String(istDate.getDate()).padStart(2, '0');
    const month = String(istDate.getMonth() + 1).padStart(2, '0');
    const year = istDate.getFullYear();
    
    // Format time as 12-hour with AM/PM - use regular methods, not UTC
    const hours = istDate.getHours();
    const minutes = String(istDate.getMinutes()).padStart(2, '0');
    const ampm = hours >= 12 ? 'PM' : 'AM';
    const displayHours = hours % 12 || 12;
    
    const formatted = `${day}/${month}/${year} ${displayHours}:${minutes} ${ampm}`;
    console.log('Date conversion:', { input: dateString, utc: date.toISOString(), ist: formatted });
    return formatted;
  };

  const handleViewDetails = (result) => {
    setSelectedResult(result);
    setShowDetailModal(true);
  };

  const handleCloseDetail = () => {
    setShowDetailModal(false);
    setSelectedResult(null);
  };

  const handleDeleteClick = (e, result) => {
    e.stopPropagation();
    setDeleteConfirm(result);
  };

  const handleDeleteConfirm = async () => {
    if (!deleteConfirm) return;
    
    try {
      await resultsAPI.deleteResult(deleteConfirm.result_id);
      setResults(results.filter(r => r.result_id !== deleteConfirm.result_id));
      setDeleteConfirm(null);
    } catch (error) {
      setError('Failed to delete result');
      setTimeout(() => setError(''), 3000);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteConfirm(null);
  };

  if (loading) {
    return (
      <div className="results-report-container">
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading results...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="results-report-container">
      <div className="report-header">
        <h1>📊 Student Results Report</h1>
        <button onClick={() => navigate('/dashboard')} className="btn-back">
          ← Back to Dashboard
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="filters-card">
        <h3>Filters</h3>
        <div className="filters-grid">
          <div className="filter-group">
            <label>Student Name</label>
            <input
              type="text"
              value={studentFilter}
              onChange={(e) => setStudentFilter(e.target.value)}
              placeholder="Search by name..."
            />
          </div>

          <div className="filter-group">
            <label>Course</label>
            <select value={courseFilter} onChange={(e) => setCourseFilter(e.target.value)}>
              <option value="">All Courses</option>
              {courses.map(course => (
                <option key={course} value={course}>{course}</option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label>Subject</label>
            <select value={subjectFilter} onChange={(e) => setSubjectFilter(e.target.value)}>
              <option value="">All Subjects</option>
              {subjects.map(subject => (
                <option key={subject} value={subject}>{subject}</option>
              ))}
            </select>
          </div>

          <div className="filter-actions">
            <button onClick={clearFilters} className="btn-clear">
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      <div className="results-summary">
        <div className="summary-card">
          <div className="summary-icon">👥</div>
          <div className="summary-content">
            <div className="summary-value">{filteredResults.length}</div>
            <div className="summary-label">Result(s)</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="summary-icon">📈</div>
          <div className="summary-content">
            <div className="summary-value">
              {filteredResults.length > 0
                ? (filteredResults.reduce((sum, r) => sum + r.average_score, 0) / filteredResults.length).toFixed(1)
                : '0'}%
            </div>
            <div className="summary-label">Average Score</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="summary-icon">🎓</div>
          <div className="summary-content">
            <div className="summary-value">{courses.length}</div>
            <div className="summary-label">Course(s)</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="summary-icon">📚</div>
          <div className="summary-content">
            <div className="summary-value">{subjects.length}</div>
            <div className="summary-label">Subject(s)</div>
          </div>
        </div>
      </div>

      <div className="results-table-card">
        <h3>Results ({filteredResults.length})</h3>
        
        {filteredResults.length === 0 ? (
          <div className="no-results">
            <p>No results found matching your filters.</p>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="results-table">
              <thead>
                <tr>
                  <th>Student Name</th>
                  <th>Course</th>
                  <th>Subject</th>
                  <th>Quiz Title</th>
                  <th>Score</th>
                  <th>Questions</th>
                  <th>Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredResults.map((result) => (
                  <tr 
                    key={result.result_id} 
                    onClick={() => handleViewDetails(result)}
                    className="clickable-row"
                  >
                    <td className="student-name">{result.student_name}</td>
                    <td>{result.course}</td>
                    <td>{result.subject}</td>
                    <td>{result.title}</td>
                    <td>
                      <span className={`score-badge ${getScoreClass(result.average_score)}`}>
                        {result.average_score.toFixed(1)}%
                      </span>
                    </td>
                    <td className="text-center">{result.total_questions}</td>
                    <td className="date-cell">{formatDate(result.completed_at)}</td>
                    <td>
                      <button 
                        className="btn-delete-small"
                        onClick={(e) => handleDeleteClick(e, result)}
                        title="Delete result"
                      >
                        🗑️
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {showDetailModal && selectedResult && (
        <div className="modal-overlay" onClick={handleCloseDetail}>
          <div className="modal-content detail-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>📝 Quiz Details</h2>
              <button className="btn-close" onClick={handleCloseDetail}>✕</button>
            </div>
            
            <div className="modal-body">
              <div className="detail-info">
                <div className="info-row">
                  <span className="info-label">Student:</span>
                  <span className="info-value">{selectedResult.student_name}</span>
                </div>
                <div className="info-row">
                  <span className="info-label">Course:</span>
                  <span className="info-value">{selectedResult.course}</span>
                </div>
                <div className="info-row">
                  <span className="info-label">Subject:</span>
                  <span className="info-value">{selectedResult.subject}</span>
                </div>
                <div className="info-row">
                  <span className="info-label">Quiz Title:</span>
                  <span className="info-value">{selectedResult.title}</span>
                </div>
                <div className="info-row">
                  <span className="info-label">Average Score:</span>
                  <span className={`score-badge ${getScoreClass(selectedResult.average_score)}`}>
                    {selectedResult.average_score.toFixed(1)}%
                  </span>
                </div>
                <div className="info-row">
                  <span className="info-label">Completed:</span>
                  <span className="info-value">{formatDate(selectedResult.completed_at)}</span>
                </div>
              </div>

              <div className="questions-answers">
                <h3>Questions & Answers</h3>
                {selectedResult.evaluations && selectedResult.evaluations.map((evaluation, index) => {
                  const question = selectedResult.questions && selectedResult.questions[evaluation.question_index];
                  return (
                    <div key={index} className="qa-card">
                      <div className="qa-header">
                        <span className="qa-number">Question {evaluation.question_index + 1}</span>
                        <span className={`qa-score ${getScoreClass(parseFloat(evaluation.score) || 0)}`}>
                          Score: {evaluation.score}
                        </span>
                      </div>
                      
                      <div className="qa-content">
                        {question && (
                          <div className="qa-section question-section">
                            <strong>Question:</strong>
                            <p>{question.question_text}</p>
                          </div>
                        )}
                        
                        <div className="qa-section">
                          <strong>Student's Answer:</strong>
                          <p>{evaluation.user_answer}</p>
                        </div>
                        
                        {question && question.example_answer && (
                          <div className="qa-section">
                            <strong>Example Answer:</strong>
                            <p>{question.example_answer}</p>
                          </div>
                        )}
                        
                        <div className="qa-section">
                          <strong>Evaluation:</strong>
                          <p>{evaluation.evaluation}</p>
                        </div>
                        
                        {evaluation.justification && (
                          <div className="qa-section">
                            <strong>Justification:</strong>
                            <p>{evaluation.justification}</p>
                          </div>
                        )}
                        
                        {evaluation.suggessions && (
                          <div className="qa-section">
                            <strong>Suggestions:</strong>
                            <p>{evaluation.suggessions}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div className="modal-overlay" onClick={handleDeleteCancel}>
          <div className="modal-content confirm-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>⚠️ Confirm Delete</h2>
            </div>
            <div className="modal-body">
              <p>Are you sure you want to delete this result?</p>
              <div className="confirm-details">
                <p><strong>Student:</strong> {deleteConfirm.student_name}</p>
                <p><strong>Quiz:</strong> {deleteConfirm.title}</p>
                <p><strong>Score:</strong> {deleteConfirm.average_score.toFixed(1)}%</p>
              </div>
              <p className="warning-text">This action cannot be undone.</p>
            </div>
            <div className="modal-footer">
              <button className="btn-cancel" onClick={handleDeleteCancel}>Cancel</button>
              <button className="btn-delete" onClick={handleDeleteConfirm}>Delete</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ResultsReport;
