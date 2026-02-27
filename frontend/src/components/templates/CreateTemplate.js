import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  Box,
  IconButton,
  Card,
  CardContent,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  AppBar,
  Toolbar,
  Divider,
} from '@mui/material';
import {
  ArrowBack,
  Add,
  Delete,
  Save,
} from '@mui/icons-material';
import { templatesAPI } from '../../services/api';

const CreateTemplate = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  const [templateData, setTemplateData] = useState({
    title: '',
    subject: '',
    course: '',
    questions: [
      {
        question_text: '',
        sample_answer: '',
      }
    ]
  });

  const handleTemplateChange = (field, value) => {
    setTemplateData({ ...templateData, [field]: value });
  };

  const handleQuestionChange = (index, field, value) => {
    const newQuestions = [...templateData.questions];
    newQuestions[index][field] = value;
    setTemplateData({ ...templateData, questions: newQuestions });
  };

  const addQuestion = () => {
    setTemplateData({
      ...templateData,
      questions: [
        ...templateData.questions,
        {
          question_text: '',
          sample_answer: '',
        }
      ]
    });
  };

  const removeQuestion = (index) => {
    if (templateData.questions.length > 1) {
      const newQuestions = templateData.questions.filter((_, i) => i !== index);
      setTemplateData({ ...templateData, questions: newQuestions });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      await templatesAPI.createTemplate(templateData);
      setSuccess('Template created successfully!');
      setTimeout(() => navigate('/dashboard'), 2000);
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to create template');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      <AppBar position="static" elevation={0} sx={{ borderRadius: 0 }}>
        <Toolbar>
          <IconButton edge="start" color="inherit" onClick={() => navigate('/dashboard')}>
            <ArrowBack />
          </IconButton>
          <Typography variant="h6" sx={{ ml: 2 }}>
            Create New Template
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="md" sx={{ py: 4 }}>
        {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 3 }}>{success}</Alert>}

        <Paper elevation={0} sx={{ p: 4 }}>
          <Box component="form" onSubmit={handleSubmit}>
            <Typography variant="h5" gutterBottom>Template Details</Typography>
            <Divider sx={{ mb: 3 }} />

            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Template Title"
                  value={templateData.title}
                  onChange={(e) => handleTemplateChange('title', e.target.value)}
                  required
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth required>
                  <InputLabel>Subject</InputLabel>
                  <Select
                    value={templateData.subject}
                    label="Subject"
                    onChange={(e) => handleTemplateChange('subject', e.target.value)}
                  >
                    <MenuItem value="Computer Science">Computer Science</MenuItem>
                    <MenuItem value="Mathematics">Mathematics</MenuItem>
                    <MenuItem value="Physics">Physics</MenuItem>
                    <MenuItem value="Chemistry">Chemistry</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth required>
                  <InputLabel>Course</InputLabel>
                  <Select
                    value={templateData.course}
                    label="Course"
                    onChange={(e) => handleTemplateChange('course', e.target.value)}
                  >
                    <MenuItem value="MSC-101">MSC-101</MenuItem>
                    <MenuItem value="MSC-102">MSC-102</MenuItem>
                    <MenuItem value="MSC-201">MSC-201</MenuItem>
                    <MenuItem value="MSC-202">MSC-202</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>

            <Box mt={4} mb={2}>
              <Typography variant="h5" gutterBottom>Questions</Typography>
              <Divider />
            </Box>

            {templateData.questions.map((question, qIndex) => (
              <Card key={qIndex} sx={{ mb: 3 }}>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Typography variant="h6">Question {qIndex + 1}</Typography>
                    {templateData.questions.length > 1 && (
                      <IconButton color="error" onClick={() => removeQuestion(qIndex)}>
                        <Delete />
                      </IconButton>
                    )}
                  </Box>

                  <TextField
                    fullWidth
                    label="Question Text"
                    multiline
                    rows={3}
                    value={question.question_text}
                    onChange={(e) => handleQuestionChange(qIndex, 'question_text', e.target.value)}
                    required
                    sx={{ mb: 2 }}
                    placeholder="Enter the question that students need to answer in detail..."
                  />

                  <TextField
                    fullWidth
                    label="Sample Answer / Key Points"
                    multiline
                    rows={5}
                    value={question.sample_answer}
                    onChange={(e) => handleQuestionChange(qIndex, 'sample_answer', e.target.value)}
                    required
                    placeholder="Provide a sample answer or key points that should be covered in the answer..."
                    helperText="This will be used for evaluation reference"
                  />
                </CardContent>
              </Card>
            ))}

            <Button
              fullWidth
              variant="outlined"
              startIcon={<Add />}
              onClick={addQuestion}
              sx={{ mb: 3 }}
            >
              Add Question
            </Button>

            <Box display="flex" gap={2}>
              <Button
                variant="outlined"
                onClick={() => navigate('/dashboard')}
                fullWidth
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="contained"
                startIcon={<Save />}
                disabled={loading}
                fullWidth
              >
                {loading ? 'Creating...' : 'Create Template'}
              </Button>
            </Box>
          </Box>
        </Paper>
      </Container>
    </Box>
  );
};

export default CreateTemplate;
