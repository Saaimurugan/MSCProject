import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
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

const TemplateEditor = () => {
  const navigate = useNavigate();
  const { templateId } = useParams();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Form state
  const [title, setTitle] = useState('');
  const [subject, setSubject] = useState('');
  const [course, setCourse] = useState('');
  const [questions, setQuestions] = useState([]);

  // Validation errors
  const [validationErrors, setValidationErrors] = useState({
    title: '',
    subject: '',
    course: '',
    questions: [],
  });

  useEffect(() => {
    loadTemplate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [templateId]);

  const loadTemplate = async () => {
    try {
      setLoading(true);
      const response = await templatesAPI.getTemplateById(templateId);
      const template = response.data;
      
      setTitle(template.title);
      setSubject(template.subject);
      setCourse(template.course);
      
      // Convert questions to elaborate format (handle both old MCQ and new elaborate formats)
      setQuestions(template.questions.map(q => ({
        question_text: q.question_text,
        question_type: 'elaborate',
        example_answer: q.example_answer || '',
      })));
      setError('');
    } catch (error) {
      console.error('Load template error:', error);
      setError('Failed to load template');
    } finally {
      setLoading(false);
    }
  };

  const validateForm = () => {
    const errors = {
      title: '',
      subject: '',
      course: '',
      questions: [],
    };
    let isValid = true;

    if (!title.trim()) {
      errors.title = 'Title is required';
      isValid = false;
    }

    if (!subject.trim()) {
      errors.subject = 'Subject is required';
      isValid = false;
    }

    if (!course.trim()) {
      errors.course = 'Course is required';
      isValid = false;
    }

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
    }
  };

  const handleQuestionChange = (index, field, value) => {
    const newQuestions = [...questions];
    newQuestions[index][field] = value;
    setQuestions(newQuestions);
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
  };

  const handleCorrectAnswerChange = (questionIndex, optionIndex) => {
    const newQuestions = [...questions];
    newQuestions[questionIndex].correct_answer = optionIndex;
    setQuestions(newQuestions);
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
      setSaving(true);
      
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

      await templatesAPI.updateTemplate(templateId, templateData);
      setSuccess('Template updated successfully!');
      
      setTimeout(() => {
        navigate('/dashboard');
      }, 2000);
    } catch (err) {
      const errorMessage = err.response?.data?.message || 'Failed to update template';
      setError(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <CircularProgress size={60} />
      </Box>
    );
  }

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
            Edit Quiz Template
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
              disabled={saving}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="contained"
              startIcon={saving ? <CircularProgress size={20} /> : <Save />}
              fullWidth
              disabled={saving}
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </Button>
          </Box>
        </form>
      </Container>
    </Box>
  );
};

export default TemplateEditor;
