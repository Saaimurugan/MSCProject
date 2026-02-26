import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import './Quiz.css';
import './Quiz-Results.css';

const QuizResults = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { results, template } = location.state || {};

  if (!results || !template) {
    return (
      <div className="quiz-container">
        <div className="error-message">No results available</div>
        <button onClick={() => navigate('/dashboard')} className="btn-primary">
          Back to Dashboard
        </button>
      </div>
    );
  }

  const { average_score, total_questions, evaluations } = results;
  const percentage = Math.round(average_score);

  // Determine performance level
  let performanceLevel = '';
  let performanceClass = '';
  if (percentage >= 90) {
    performanceLevel = 'Excellent!';
    performanceClass = 'excellent';
  } else if (percentage >= 70) {
    performanceLevel = 'Good Job!';
    performanceClass = 'good';
  } else if (percentage >= 50) {
    performanceLevel = 'Fair';
    performanceClass = 'fair';
  } else {
    performanceLevel = 'Needs Improvement';
    performanceClass = 'poor';
  }

  return (
    <div className="quiz-container">
      <div className="results-header">
        <h1>Quiz Results</h1>
        <h2>{template.title}</h2>
        <p className="quiz-details">{template.subject} - {template.course}</p>
      </div>

      <div className={`score-card ${performanceClass}`}>
        <div className="score-percentage">{percentage}%</div>
        <div className="score-label">{performanceLevel}</div>
        <div className="score-details">
          Average Score: {average_score.toFixed(2)} / 100
        </div>
      </div>

      <div className="detailed-results">
        <h3>Detailed Feedback</h3>
        {evaluations.map((evaluation, index) => {
          const question = template.questions[evaluation.question_index];
          
          return (
            <div key={index} className="result-item elaborate">
              <div className="result-header">
                <span className="question-number">Question {evaluation.question_index + 1}</span>
                <span className="result-badge score">
                  Score: {evaluation.score}
                </span>
              </div>
              
              <div className="question-text">{question.question_text}</div>
              
              <div className="answer-review">
                <div className="your-answer">
                  <strong>Your answer:</strong>
                  <div className="answer-text">
                    {evaluation.user_answer}
                  </div>
                </div>
                
                {question.example_answer && (
                  <div className="example-answer">
                    <strong>Example answer:</strong>
                    <div className="answer-text">
                      {question.example_answer}
                    </div>
                  </div>
                )}
                
                <div className="evaluation-section">
                  <strong>Evaluation:</strong>
                  <div className="evaluation-text">
                    {evaluation.evaluation}
                  </div>
                </div>
                
                {evaluation.justification && (
                  <div className="justification-section">
                    <strong>Justification:</strong>
                    <div className="justification-text">
                      {evaluation.justification}
                    </div>
                  </div>
                )}
                
                {evaluation.suggessions && (
                  <div className="suggestions-section">
                    <strong>Suggestions:</strong>
                    <div className="suggestions-text">
                      {evaluation.suggessions}
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div className="results-actions">
        <button onClick={() => navigate('/dashboard')} className="btn-secondary">
          Back to Dashboard
        </button>
        <button onClick={() => navigate(`/quiz/${template.template_id}`)} className="btn-primary">
          Retake Quiz
        </button>
      </div>
    </div>
  );
};

export default QuizResults;
