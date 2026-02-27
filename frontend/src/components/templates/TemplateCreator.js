import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  Box,
  TextField,
  Button,
  Card,
  CardContent,
  IconButton,
  Alert,
  Divider,
  AppBar,
  Toolbar,
  CircularProgress,
  FormControl,
  FormLabel,
} from '@mui/material';
import {
  Add,
  Delete,
  ArrowBack,
  Save,
  School,
} from '@mui/icons-material';
import { templatesAPI } from '../../services/api';

const TemplateCreator = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Form state
  const [title, setTitle] = useState('');
  const [subject, setSubject] = useState('');
  const [course, setCourse] = useState('');
  const [questions, setQuestions] = useState([
    {
      question_text: '',
      question_type: 'elaborate',
      example_answer: '',
    },
  ]);

  // Validation errors
  const [validationErrors, setValidationErrors] = useState({
    title: '',
    subject: '',
    course: '',
    questions: [],
  });

  const validateForm = () => {
    const errors = {
      title: '',
      subject: '',
      course: '',
      questions: [],
    };
    let isValid = true;

    // Validate title
    if (!title.trim()) {
      errors.title = 'Title is required and cannot be empty';
      isValid = false;
    }

    // Validate subject
    if (!subject.trim()) {
      errors.subject = 'Subject is required and cannot be empty';
      isValid = false;
    }

    // Validate course
    if (!course.trim()) {
      errors.course = 'Course is required and cannot be empty';
      isValid = false;
    }

    // Validate questions
    questions.forEach((question, index) => {
      const questionErrors = {
        question_text: '',
        example_answer: '',
      };

      if (!question.question_text.trim()) {
        questionErrors.question_text = 'Question text is required';
        isValid = false;
      }

      errors.questions[index] = questionErrors;
    });

    setValidationErrors(errors);
    return isValid;
  };

  const handleAddQuestion = () => {
    setQuestions([
      ...questions,
      {
        question_text: '',
        question_type: 'elaborate',
        example_answer: '',
      },
    ]);
  };

  const handleRemoveQuestion = (index) => {
    if (questions.length > 1) {
      const newQuestions = questions.filter((_, i) => i !== index);
      setQuestions(newQuestions);
      
      // Clear validation errors for removed question
      const newErrors = { ...validationErrors };
      newErrors.questions.splice(index, 1);
      setValidationErrors(newErrors);
    }
  };

  const handleQuestionChange = (index, field, value) => {
    const newQuestions = [...questions];
    newQuestions[index][field] = value;
    setQuestions(newQuestions);
    
    // Clear validation error for this field
    if (validationErrors.questions[index]) {
      const newErrors = { ...validationErrors };
      newErrors.questions[index][field] = '';
      setValidationErrors(newErrors);
    }
  };

  const handleAddOption = (questionIndex) => {
    const newQuestions = [...questions];
    newQuestions[questionIndex].options.push('');
    setQuestions(newQuestions);
  };

  const handleRemoveOption = (questionIndex, optionIndex) => {
    const newQuestions = [...questions];
    if (newQuestions[questionIndex].options.length > 2) {
      newQuestions[questionIndex].options.splice(optionIndex, 1);
      
      // Adjust correct_answer if needed
      if (newQuestions[questionIndex].correct_answer >= newQuestions[questionIndex].options.length) {
        newQuestions[questionIndex].correct_answer = newQuestions[questionIndex].options.length - 1;
      }
      
      setQuestions(newQuestions);
    }
  };

  const handleOptionChange = (questionIndex, optionIndex, value) => {
    const newQuestions = [...questions];
    newQuestions[questionIndex].options[optionIndex] = value;
    setQuestions(newQuestions);
    
    // Clear validation error for options
    if (validationErrors.questions[questionIndex]) {
      const newErrors = { ...validationErrors };
      newErrors.questions[questionIndex].options = '';
      setValidationErrors(newErrors);
    }
  };

  const handleCorrectAnswerChange = (questionIndex, optionIndex) => {
    const newQuestions = [...questions];
    newQuestions[questionIndex].correct_answer = optionIndex;
    setQuestions(newQuestions);
    
    // Clear validation error for correct answer
    if (validationErrors.questions[questionIndex]) {
      const newErrors = { ...validationErrors };
      newErrors.questions[questionIndex].correct_answer = '';
      setValidationErrors(newErrors);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!validateForm()) {
      setError('Please fix the validation errors before submitting');
      return;
    }

    try {
      setLoading(true);
      
      // Prepare questions - all are elaborate type
      const cleanedQuestions = questions.map(q => ({
        question_text: q.question_text.trim(),
        question_type: 'elaborate',
        example_answer: q.example_answer ? q.example_answer.trim() : '',
      }));

      const templateData = {
        title: title.trim(),
        subject: subject.trim(),
        course: course.trim(),
        questions: cleanedQuestions,
      };

      const response = await templatesAPI.createTemplate(templateData);
      setSuccess('Template created successfully!');
      
      // Redirect to dashboard after 2 seconds
      setTimeout(() => {
        navigate('/dashboard');
      }, 2000);
    } catch (err) {
      const errorMessage = err.response?.data?.message || 'Failed to create template';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      <AppBar position="static" elevation={0} sx={{ borderRadius: 0 }}>
        <Toolbar>
          <IconButton
            edge="start"
            color="inherit"
            onClick={() => navigate('/dashboard')}
            sx={{ mr: 2 }}
          >
            <ArrowBack />
          </IconButton>
          <School sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Create Quiz Template
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="md" sx={{ py: 4 }}>
        <form onSubmit={handleSubmit}>
          {/* Template Metadata */}
          <Card elevation={0} sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Template Information
              </Typography>
              
              <TextField
                fullWidth
                label="Title"
                value={title}
                onChange={(e) => {
                  setTitle(e.target.value);
                  setValidationErrors({ ...validationErrors, title: '' });
                }}
                error={!!validationErrors.title}
                helperText={validationErrors.title}
                margin="normal"
                required
              />
              
              <TextField
                fullWidth
                label="Subject"
                value={subject}
                onChange={(e) => {
                  setSubject(e.target.value);
                  setValidationErrors({ ...validationErrors, subject: '' });
                }}
                error={!!validationErrors.subject}
                helperText={validationErrors.subject}
                margin="normal"
                required
              />
              
              <TextField
                fullWidth
                label="Course"
                value={course}
                onChange={(e) => {
                  setCourse(e.target.value);
                  setValidationErrors({ ...validationErrors, course: '' });
                }}
                error={!!validationErrors.course}
                helperText={validationErrors.course}
                margin="normal"
                required
              />
            </CardContent>
          </Card>

          {/* Questions */}
          <Typography variant="h6" gutterBottom>
            Questions
          </Typography>

          {questions.map((question, questionIndex) => (
            <Card key={questionIndex} elevation={0} sx={{ mb: 3 }}>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="subtitle1" fontWeight="bold">
                    Question {questionIndex + 1}
                  </Typography>
                  {questions.length > 1 && (
                    <IconButton
                      color="error"
                      onClick={() => handleRemoveQuestion(questionIndex)}
                      size="small"
                    >
                      <Delete />
                    </IconButton>
                  )}
                </Box>

                <TextField
                  fullWidth
                  label="Question Text"
                  value={question.question_text}
                  onChange={(e) => handleQuestionChange(questionIndex, 'question_text', e.target.value)}
                  error={!!validationErrors.questions[questionIndex]?.question_text}
                  helperText={validationErrors.questions[questionIndex]?.question_text}
                  margin="normal"
                  multiline
                  rows={2}
                  required
                />

                <Divider sx={{ my: 2 }} />

                <FormControl fullWidth>
                  <FormLabel component="legend">
                    Example Answer (optional - for reference/grading)
                  </FormLabel>
                  
                  {validationErrors.questions[questionIndex]?.example_answer && (
                    <Alert severity="error" sx={{ mt: 1, mb: 2 }}>
                      {validationErrors.questions[questionIndex].example_answer}
                    </Alert>
                  )}
                  
                  <TextField
                    fullWidth
                    label="Example Answer"
                    value={question.example_answer || ''}
                    onChange={(e) => handleQuestionChange(questionIndex, 'example_answer', e.target.value)}
                    margin="normal"
                    multiline
                    rows={4}
                    placeholder="Provide an example answer that will be used as a reference for grading..."
                  />
                </FormControl>
              </CardContent>
            </Card>
          ))}

          <Button
            fullWidth
            variant="outlined"
            startIcon={<Add />}
            onClick={handleAddQuestion}
            sx={{ mb: 3 }}
          >
            Add Question
          </Button>

          {/* Error and Success Messages */}
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          {success && (
            <Alert severity="success" sx={{ mb: 3 }}>
              {success}
            </Alert>
          )}

          {/* Submit Button */}
          <Box display="flex" gap={2}>
            <Button
              variant="outlined"
              onClick={() => navigate('/dashboard')}
              fullWidth
              disabled={loading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="contained"
              startIcon={loading ? <CircularProgress size={20} /> : <Save />}
              fullWidth
              disabled={loading}
            >
              {loading ? 'Creating...' : 'Create Template'}
            </Button>
          </Box>
        </form>
      </Container>
    </Box>
  );
};

export default TemplateCreator;
