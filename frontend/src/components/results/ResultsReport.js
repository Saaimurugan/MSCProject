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
      
      // Extract unique courses and subjects
      const uniqueCourses = [...new Set(response.data.results.map(r => r.course))].sort();
      const uniqueSubjects = [...new Set(response.data.results.map(r => r.subject))].sort();
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
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
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
            <div className="summary-label">Total Results</div>
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
            <div className="summary-label">Courses</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="summary-icon">📚</div>
          <div className="summary-content">
            <div className="summary-value">{subjects.length}</div>
            <div className="summary-label">Subjects</div>
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
                </tr>
              </thead>
              <tbody>
                {filteredResults.map((result) => (
                  <tr key={result.result_id}>
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
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default ResultsReport;
