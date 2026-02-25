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
  Paper,
  Radio,
  RadioGroup,
  FormControlLabel,
  FormControl,
  FormLabel,
  Divider,
  AppBar,
  Toolbar,
  CircularProgress,
} from '@mui/material';
import {
  Add,
  Delete,
  ArrowBack,
  Save,
  School,
} from '@mui/icons-material';
import { templatesAPI } from '../../services/api';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';

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
      question_type: 'multiple_choice', // 'multiple_choice' or 'elaborate'
      options: ['', ''],
      correct_answer: 0,
      example_answer: '', // For elaborate questions
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
        options: '',
        correct_answer: '',
        example_answer: '',
      };

      if (!question.question_text.trim()) {
        questionErrors.question_text = 'Question text is required';
        isValid = false;
      }

      if (question.question_type === 'multiple_choice') {
        // Validate minimum 2 options for multiple choice
        const nonEmptyOptions = question.options.filter(opt => opt.trim() !== '');
        if (nonEmptyOptions.length < 2) {
          questionErrors.options = 'At least 2 answer options are required';
          isValid = false;
        }

        // Validate correct answer is designated
        if (question.correct_answer === null || question.correct_answer === undefined) {
          questionErrors.correct_answer = 'A correct answer must be designated';
          isValid = false;
        }
      }
      // No validation for elaborate questions - example answer is optional

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
        question_type: 'multiple_choice',
        options: ['', ''],
        correct_answer: 0,
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
      
      // Filter out empty options and prepare questions based on type
      const cleanedQuestions = questions.map(q => {
        if (q.question_type === 'elaborate') {
          return {
            question_text: q.question_text.trim(),
            question_type: 'elaborate',
            example_answer: q.example_answer.trim(),
          };
        } else {
          return {
            question_text: q.question_text.trim(),
            question_type: 'multiple_choice',
            options: q.options.filter(opt => opt.trim() !== ''),
            correct_answer: q.correct_answer,
          };
        }
      });

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
      <AppBar position="static" elevation={0}>
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

                <FormControl fullWidth margin="normal">
                  <FormLabel>Question Type</FormLabel>
                  <Select
                    value={question.question_type}
                    onChange={(e) => handleQuestionChange(questionIndex, 'question_type', e.target.value)}
                  >
                    <MenuItem value="multiple_choice">Multiple Choice</MenuItem>
                    <MenuItem value="elaborate">Elaborate Answer</MenuItem>
                  </Select>
                </FormControl>

                <Divider sx={{ my: 2 }} />

                {question.question_type === 'multiple_choice' ? (
                  <FormControl 
                    component="fieldset" 
                    fullWidth
                    error={!!validationErrors.questions[questionIndex]?.options || !!validationErrors.questions[questionIndex]?.correct_answer}
                  >
                    <FormLabel component="legend">
                      Answer Options (select the correct answer)
                    </FormLabel>
                    
                    {validationErrors.questions[questionIndex]?.options && (
                      <Alert severity="error" sx={{ mt: 1, mb: 2 }}>
                        {validationErrors.questions[questionIndex].options}
                      </Alert>
                    )}
                    
                    {validationErrors.questions[questionIndex]?.correct_answer && (
                      <Alert severity="error" sx={{ mt: 1, mb: 2 }}>
                        {validationErrors.questions[questionIndex].correct_answer}
                      </Alert>
                    )}

                    <RadioGroup
                      value={question.correct_answer}
                      onChange={(e) => handleCorrectAnswerChange(questionIndex, parseInt(e.target.value))}
                    >
                      {question.options.map((option, optionIndex) => (
                        <Paper key={optionIndex} elevation={0} sx={{ p: 2, mb: 1, bgcolor: 'grey.50' }}>
                          <Box display="flex" alignItems="center" gap={1}>
                            <FormControlLabel
                              value={optionIndex}
                              control={<Radio />}
                              label=""
                              sx={{ m: 0 }}
                            />
                            <TextField
                              fullWidth
                              label={`Option ${optionIndex + 1}`}
                              value={option}
                              onChange={(e) => handleOptionChange(questionIndex, optionIndex, e.target.value)}
                              size="small"
                            />
                            {question.options.length > 2 && (
                              <IconButton
                                color="error"
                                onClick={() => handleRemoveOption(questionIndex, optionIndex)}
                                size="small"
                              >
                                <Delete />
                              </IconButton>
                            )}
                          </Box>
                        </Paper>
                      ))}
                    </RadioGroup>

                    <Button
                      startIcon={<Add />}
                      onClick={() => handleAddOption(questionIndex)}
                      sx={{ mt: 1 }}
                    >
                      Add Option
                    </Button>
                  </FormControl>
                ) : (
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
                )}
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
