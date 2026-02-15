import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { quizAPI } from '../../services/api';
import './Quiz.css';

const QuizTaking = () => {
  const { templateId } = useParams();
  const navigate = useNavigate();
  const [quiz, setQuiz] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState([]);
  const [currentAnswer, setCurrentAnswer] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [studentInfo, setStudentInfo] = useState({
    name: '',
    id: ''
  });
  const [showStudentForm, setShowStudentForm] = useState(true);

  useEffect(() => {
    loadQuiz();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [templateId]);

  const loadQuiz = async () => {
    try {
      const response = await quizAPI.getQuiz(templateId);
      setQuiz(response.data);
      setAnswers(new Array(response.data.questions.length).fill(''));
    } catch (error) {
      setError('Failed to load quiz');
    } finally {
      setLoading(false);
    }
  };

  const handleStudentInfoSubmit = (e) => {
    e.preventDefault();
    if (!studentInfo.name.trim() || !studentInfo.id.trim()) {
      setError('Please enter both name and student ID');
      return;
    }
    setShowStudentForm(false);
    setError('');
  };

  const handleAnswerChange = (e) => {
    const newAnswer = e.target.value;
    setCurrentAnswer(newAnswer);
    
    const newAnswers = [...answers];
    newAnswers[currentQuestionIndex] = newAnswer;
    setAnswers(newAnswers);
  };

  const goToQuestion = (index) => {
    setCurrentQuestionIndex(index);
    setCurrentAnswer(answers[index] || '');
  };

  const nextQuestion = () => {
    if (currentQuestionIndex < quiz.questions.length - 1) {
      goToQuestion(currentQuestionIndex + 1);
    }
  };

  const previousQuestion = () => {
    if (currentQuestionIndex > 0) {
      goToQuestion(currentQuestionIndex - 1);
    }
  };

  const submitQuiz = async () => {
    // Check if all questions are answered
    const unansweredQuestions = answers.some(answer => !answer.trim());
    if (unansweredQuestions) {
      if (!window.confirm('Some questions are not answered. Do you want to submit anyway?')) {
        return;
      }
    }

    setSubmitting(true);
    try {
      const quizData = {
        template_id: templateId,
        student_name: studentInfo.name,
        student_id: studentInfo.id,
        answers: answers.map((answer, index) => ({
          question_id: index,
          user_answer: answer
        }))
      };

      const response = await quizAPI.submitQuiz(quizData);
      navigate('/quiz/results', { state: { results: response.data } });
    } catch (error) {
      setError('Failed to submit quiz. Please try again.');
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

  if (error && !quiz) {
    return (
      <div className="quiz-container">
        <div className="error-message">{error}</div>
        <button onClick={() => navigate('/dashboard')} className="btn-primary">
          Back to Dashboard
        </button>
      </div>
    );
  }

  if (showStudentForm) {
    return (
      <div className="quiz-container">
        <div className="student-info-card">
          <h2>📝 {quiz?.title}</h2>
          <p className="quiz-details">{quiz?.subject} - {quiz?.course}</p>
          
          {error && <div className="error-message">{error}</div>}
          
          <form onSubmit={handleStudentInfoSubmit}>
            <div className="form-group">
              <label htmlFor="studentName">Student Name</label>
              <input
                type="text"
                id="studentName"
                value={studentInfo.name}
                onChange={(e) => setStudentInfo({...studentInfo, name: e.target.value})}
                placeholder="Enter your full name"
                required
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="studentId">Student ID</label>
              <input
                type="text"
                id="studentId"
                value={studentInfo.id}
                onChange={(e) => setStudentInfo({...studentInfo, id: e.target.value})}
                placeholder="Enter your student ID"
                required
              />
            </div>
            
            <button type="submit" className="btn-primary">
              Start Quiz ({quiz?.questions.length} questions)
            </button>
          </form>
        </div>
      </div>
    );
  }

  const currentQuestion = quiz.questions[currentQuestionIndex];
  const progress = ((currentQuestionIndex + 1) / quiz.questions.length) * 100;

  return (
    <div className="quiz-container">
      <div className="quiz-header">
        <h1>{quiz.title}</h1>
        <div className="student-info">
          <span>{studentInfo.name} ({studentInfo.id})</span>
        </div>
      </div>

      <div className="quiz-progress">
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${progress}%` }}></div>
        </div>
        <div className="question-counter">
          Question {currentQuestionIndex + 1} of {quiz.questions.length}
        </div>
      </div>

      <div className="question-navigation">
        {quiz.questions.map((_, index) => (
          <button
            key={index}
            className={`nav-dot ${index === currentQuestionIndex ? 'active' : ''} ${answers[index] ? 'answered' : ''}`}
            onClick={() => goToQuestion(index)}
          >
            {index + 1}
          </button>
        ))}
      </div>

      <div className="question-box">
        <h3>{currentQuestion.question}</h3>
      </div>

      <textarea
        value={currentAnswer}
        onChange={handleAnswerChange}
        placeholder="Type your answer here..."
        className="answer-textarea"
      />

      {error && <div className="error-message">{error}</div>}

      <div className="quiz-controls">
        <button 
          onClick={previousQuestion} 
          disabled={currentQuestionIndex === 0}
          className="btn-secondary"
        >
          Previous
        </button>

        {currentQuestionIndex === quiz.questions.length - 1 ? (
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