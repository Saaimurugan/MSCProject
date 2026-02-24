import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import './Quiz.css';

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

  const { total_score, correct_count, total_questions, detailed_results } = results;
  const percentage = Math.round(total_score);

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
          {correct_count} out of {total_questions} questions correct
        </div>
      </div>

      <div className="detailed-results">
        <h3>Detailed Feedback</h3>
        {detailed_results.map((result, index) => {
          const question = template.questions[result.question_index];
          const isCorrect = result.is_correct;
          
          return (
            <div key={index} className={`result-item ${isCorrect ? 'correct' : 'incorrect'}`}>
              <div className="result-header">
                <span className="question-number">Question {result.question_index + 1}</span>
                <span className={`result-badge ${isCorrect ? 'correct' : 'incorrect'}`}>
                  {isCorrect ? '✓ Correct' : '✗ Incorrect'}
                </span>
              </div>
              
              <div className="question-text">{question.question_text}</div>
              
              <div className="answer-review">
                <div className="your-answer">
                  <strong>Your answer:</strong>
                  <span className={isCorrect ? 'correct-text' : 'incorrect-text'}>
                    {question.options[result.selected_answer]}
                  </span>
                </div>
                
                {!isCorrect && (
                  <div className="correct-answer">
                    <strong>Correct answer:</strong>
                    <span className="correct-text">
                      {question.options[result.correct_answer]}
                    </span>
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
