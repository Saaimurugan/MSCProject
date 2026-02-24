import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { templatesAPI, quizAPI } from '../../services/api';
import './Quiz.css';

const QuizTaking = () => {
  const { templateId } = useParams();
  const navigate = useNavigate();
  const [template, setTemplate] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadTemplate();
  }, [templateId]);

  const loadTemplate = async () => {
    try {
      const response = await templatesAPI.getTemplateById(templateId);
      setTemplate(response.data);
      // Initialize answers array with null values
      setAnswers(new Array(response.data.questions.length).fill(null));
    } catch (error) {
      setError('Failed to load quiz');
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerChange = (optionIndex) => {
    const newAnswers = [...answers];
    newAnswers[currentQuestionIndex] = optionIndex;
    setAnswers(newAnswers);
  };

  const goToQuestion = (index) => {
    setCurrentQuestionIndex(index);
  };

  const nextQuestion = () => {
    if (currentQuestionIndex < template.questions.length - 1) {
      goToQuestion(currentQuestionIndex + 1);
    }
  };

  const previousQuestion = () => {
    if (currentQuestionIndex > 0) {
      goToQuestion(currentQuestionIndex - 1);
    }
  };

  const submitQuiz = async () => {
    // Validate all questions are answered
    const unansweredQuestions = answers.some(answer => answer === null);
    if (unansweredQuestions) {
      setError('Please answer all questions before submitting');
      return;
    }

    setSubmitting(true);
    setError('');
    try {
      const quizData = {
        template_id: templateId,
        answers: answers.map((selectedAnswer, index) => ({
          question_index: index,
          selected_answer: selectedAnswer
        }))
      };

      const response = await quizAPI.submitQuiz(quizData);
      // Navigate to results with template and results data
      navigate(`/quiz/${templateId}/results`, { 
        state: { 
          results: response.data,
          template: template
        } 
      });
    } catch (error) {
      const errorMessage = error.response?.data?.error || 'Failed to submit quiz. Please try again.';
      setError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="quiz-container">
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading quiz...</p>
        </div>
      </div>
    );
  }

  if (error && !template) {
    return (
      <div className="quiz-container">
        <div className="error-message">{error}</div>
        <button onClick={() => navigate('/dashboard')} className="btn-primary">
          Back to Dashboard
        </button>
      </div>
    );
  }

  const currentQuestion = template.questions[currentQuestionIndex];
  const progress = ((currentQuestionIndex + 1) / template.questions.length) * 100;

  return (
    <div className="quiz-container">
      <div className="quiz-header">
        <h1>{template.title}</h1>
        <p className="quiz-details">{template.subject} - {template.course}</p>
      </div>

      <div className="quiz-progress">
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${progress}%` }}></div>
        </div>
        <div className="question-counter">
          Question {currentQuestionIndex + 1} of {template.questions.length}
        </div>
      </div>

      <div className="question-navigation">
        {template.questions.map((_, index) => (
          <button
            key={index}
            className={`nav-dot ${index === currentQuestionIndex ? 'active' : ''} ${answers[index] !== null ? 'answered' : ''}`}
            onClick={() => goToQuestion(index)}
          >
            {index + 1}
          </button>
        ))}
      </div>

      <div className="question-box">
        <h3>{currentQuestion.question_text}</h3>
      </div>

      <div className="answer-options">
        {currentQuestion.options.map((option, index) => (
          <div key={index} className="option-item">
            <label>
              <input
                type="radio"
                name={`question-${currentQuestionIndex}`}
                value={index}
                checked={answers[currentQuestionIndex] === index}
                onChange={() => handleAnswerChange(index)}
              />
              <span className="option-text">{option}</span>
            </label>
          </div>
        ))}
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="quiz-controls">
        <button 
          onClick={previousQuestion} 
          disabled={currentQuestionIndex === 0}
          className="btn-secondary"
        >
          Previous
        </button>

        {currentQuestionIndex === template.questions.length - 1 ? (
          <button 
            onClick={submitQuiz} 
            disabled={submitting}
            className="btn-primary submit-btn"
          >
            {submitting ? 'Submitting...' : 'Submit Quiz'}
          </button>
        ) : (
          <button 
            onClick={nextQuestion}
            className="btn-primary"
          >
            Next
          </button>
        )}
      </div>
    </div>
  );
};

export default QuizTaking;