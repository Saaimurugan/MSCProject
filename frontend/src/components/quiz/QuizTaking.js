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
  const [pdfFiles, setPdfFiles] = useState([]);
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
      // Initialize answers array with empty strings for elaborate questions
      setAnswers(new Array(response.data.questions.length).fill(''));
      setPdfFiles(new Array(response.data.questions.length).fill(null));
    } catch (error) {
      setError('Failed to load quiz');
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerChange = (value) => {
    const newAnswers = [...answers];
    newAnswers[currentQuestionIndex] = value;
    setAnswers(newAnswers);
    // Clear PDF if text is entered
    if (value) {
      const newPdfFiles = [...pdfFiles];
      newPdfFiles[currentQuestionIndex] = null;
      setPdfFiles(newPdfFiles);
    }
  };

  const handlePdfUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Validate file type
      if (file.type !== 'application/pdf') {
        setError('Please upload a PDF file');
        return;
      }
      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        setError('PDF file size must be less than 5MB');
        return;
      }
      
      const newPdfFiles = [...pdfFiles];
      newPdfFiles[currentQuestionIndex] = file;
      setPdfFiles(newPdfFiles);
      
      // Clear text answer if PDF is uploaded
      const newAnswers = [...answers];
      newAnswers[currentQuestionIndex] = '';
      setAnswers(newAnswers);
      setError('');
    }
  };

  const removePdf = () => {
    const newPdfFiles = [...pdfFiles];
    newPdfFiles[currentQuestionIndex] = null;
    setPdfFiles(newPdfFiles);
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
    // Validate all questions are answered (either text or PDF)
    const unansweredQuestions = answers.some((answer, index) => 
      !answer && !pdfFiles[index]
    );
    if (unansweredQuestions) {
      setError('Please answer all questions (text or PDF) before submitting');
      return;
    }

    setSubmitting(true);
    setError('');
    try {
      // Convert PDFs to base64
      const answersWithPdf = await Promise.all(
        answers.map(async (answer, index) => {
          const pdfFile = pdfFiles[index];
          if (pdfFile) {
            // Convert PDF to base64
            const base64 = await fileToBase64(pdfFile);
            return {
              question_index: index,
              answer_text: '',
              pdf_data: base64,
              pdf_filename: pdfFile.name
            };
          } else {
            return {
              question_index: index,
              answer_text: answer,
              pdf_data: null,
              pdf_filename: null
            };
          }
        })
      );

      const quizData = {
        template_id: templateId,
        answers: answersWithPdf
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

  const fileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result.split(',')[1]);
      reader.onerror = error => reject(error);
    });
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
            className={`nav-dot ${index === currentQuestionIndex ? 'active' : ''} ${
              answers[index] || pdfFiles[index] ? 'answered' : ''
            }`}
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
        <div className="elaborate-answer">
          <textarea
            value={answers[currentQuestionIndex]}
            onChange={(e) => handleAnswerChange(e.target.value)}
            placeholder="Type your answer here..."
            rows="8"
            disabled={pdfFiles[currentQuestionIndex] !== null}
          />
          
          <div className="pdf-upload-section">
            <div className="upload-divider">
              <span>OR</span>
            </div>
            
            <div className="pdf-upload-container">
              {pdfFiles[currentQuestionIndex] ? (
                <div className="pdf-uploaded">
                  <span className="pdf-icon">📄</span>
                  <span className="pdf-name">{pdfFiles[currentQuestionIndex].name}</span>
                  <button 
                    type="button" 
                    onClick={removePdf}
                    className="btn-remove-pdf"
                  >
                    ✕
                  </button>
                </div>
              ) : (
                <div className="pdf-upload-input">
                  <label htmlFor={`pdf-upload-${currentQuestionIndex}`} className="btn-upload">
                    📎 Upload PDF Answer
                  </label>
                  <input
                    id={`pdf-upload-${currentQuestionIndex}`}
                    type="file"
                    accept="application/pdf"
                    onChange={handlePdfUpload}
                    style={{ display: 'none' }}
                    disabled={answers[currentQuestionIndex] !== ''}
                  />
                  <p className="upload-hint">Max 5MB</p>
                </div>
              )}
            </div>
          </div>

          {currentQuestion.example_answer && (
            <div className="example-answer-hint">
              <strong>Example Answer:</strong>
              <p>{currentQuestion.example_answer}</p>
            </div>
          )}
        </div>
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