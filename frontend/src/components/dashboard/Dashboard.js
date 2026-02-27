import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  AppBar,
  Toolbar,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Alert,
  Tooltip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Snackbar,
} from '@mui/material';
import {
  Quiz,
  Add,
  FilterList,
  School,
  Edit,
  Delete as DeleteIcon,
  Logout,
} from '@mui/icons-material';
import { templatesAPI } from '../../services/api';
import { isAdmin, logout, getUsername } from '../../utils/auth';

const Dashboard = ({ onLogout }) => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedSubject, setSelectedSubject] = useState('');
  const [selectedCourse, setCourse] = useState('');
  const [availableSubjects, setAvailableSubjects] = useState([]);
  const [availableCourses, setAvailableCourses] = useState([]);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [templateToDelete, setTemplateToDelete] = useState(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const navigate = useNavigate();
  const userIsAdmin = isAdmin();
  const username = getUsername();

  useEffect(() => {
    loadTemplates();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedSubject, selectedCourse]);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      const response = await templatesAPI.getTemplates(selectedSubject, selectedCourse);
      console.log('Templates response:', response);
      
      // Handle different response formats
      let templatesData = [];
      if (response.data) {
        if (Array.isArray(response.data)) {
          templatesData = response.data;
        } else if (response.data.templates) {
          templatesData = response.data.templates;
        } else if (response.data.body) {
          const body = typeof response.data.body === 'string' 
            ? JSON.parse(response.data.body) 
            : response.data.body;
          templatesData = body.templates || [];
        }
      }
      
      setTemplates(templatesData);
      
      // Extract unique subjects and courses from templates
      const subjects = [...new Set(templatesData.map(t => t.subject).filter(Boolean))].sort();
      const courses = [...new Set(templatesData.map(t => t.course).filter(Boolean))].sort();
      
      setAvailableSubjects(subjects);
      setAvailableCourses(courses);
      setError('');
    } catch (error) {
      console.error('Templates error:', error);
      setError('Failed to load templates');
      setTemplates([]);
    } finally {
      setLoading(false);
    }
  };

  const handleTemplateClick = (templateId) => {
    navigate(`/quiz/${templateId}`);
  };

  const handleCreateTemplate = () => {
    navigate('/template/create');
  };

  const handleEditTemplate = (e, templateId) => {
    e.stopPropagation(); // Prevent card click
    navigate(`/template/edit/${templateId}`);
  };

  const handleDeleteClick = (e, template) => {
    e.stopPropagation(); // Prevent card click
    setTemplateToDelete(template);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!templateToDelete) return;

    try {
      await templatesAPI.deleteTemplate(templateToDelete.template_id);
      setSnackbar({
        open: true,
        message: 'Template deleted successfully',
        severity: 'success',
      });
      setDeleteDialogOpen(false);
      setTemplateToDelete(null);
      // Reload templates
      loadTemplates();
    } catch (error) {
      console.error('Delete error:', error);
      setSnackbar({
        open: true,
        message: 'Failed to delete template',
        severity: 'error',
      });
    }
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
    setTemplateToDelete(null);
  };

  const handleSnackbarClose = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  const handleLogout = () => {
    logout();
    if (onLogout) {
      onLogout();
    }
    navigate('/login');
  };

  // Group templates by course and subject
  const groupedTemplates = Array.isArray(templates) ? templates.reduce((acc, template) => {
    const key = `${template.course} - ${template.subject}`;
    if (!acc[key]) {
      acc[key] = [];
    }
    acc[key].push(template);
    return acc;
  }, {}) : {};

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      <AppBar position="static" elevation={0}>
        <Toolbar>
          <School sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            AI Assessment
          </Typography>
          
          <Typography variant="body2" sx={{ mr: 2, color: 'rgba(255,255,255,0.8)' }}>
            {username} ({userIsAdmin ? 'Admin' : 'Student'})
          </Typography>
          
          {userIsAdmin && (
            <>
              <Button 
                color="inherit" 
                onClick={() => navigate('/results')}
                sx={{ mr: 2 }}
              >
                📊 View Results
              </Button>
              
              <Button 
                color="inherit" 
                startIcon={<Add />}
                onClick={handleCreateTemplate}
                sx={{ mr: 2 }}
              >
                Create Template
              </Button>
            </>
          )}
          
          <IconButton 
            color="inherit" 
            onClick={handleLogout}
            title="Logout"
          >
            <Logout />
          </IconButton>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ py: 4 }}>
        {/* Welcome Section */}
        <Box mb={4}>
          <Typography variant="h4" gutterBottom>
            Welcome to AI Assessment! 👋
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {userIsAdmin 
              ? 'Create quiz templates or take quizzes from available templates below.'
              : 'Select a quiz template below to start your assessment.'}
          </Typography>
        </Box>

        {/* Filters */}
        <Card elevation={0} sx={{ mb: 4 }}>
          <CardContent>
            <Box display="flex" alignItems="center" gap={2} mb={2}>
              <FilterList color="primary" />
              <Typography variant="h6">Filter Templates</Typography>
            </Box>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={4}>
                <FormControl fullWidth>
                  <InputLabel>Course</InputLabel>
                  <Select
                    value={selectedCourse}
                    label="Course"
                    onChange={(e) => setCourse(e.target.value)}
                  >
                    <MenuItem value="">All Courses</MenuItem>
                    {availableCourses.map((course) => (
                      <MenuItem key={course} value={course}>
                        {course}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <FormControl fullWidth>
                  <InputLabel>Subject</InputLabel>
                  <Select
                    value={selectedSubject}
                    label="Subject"
                    onChange={(e) => setSelectedSubject(e.target.value)}
                  >
                    <MenuItem value="">All Subjects</MenuItem>
                    {availableSubjects.map((subject) => (
                      <MenuItem key={subject} value={subject}>
                        {subject}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {loading ? (
          <Box display="flex" justifyContent="center" py={8}>
            <CircularProgress size={60} />
          </Box>
        ) : (
          <Box>
            {Object.keys(groupedTemplates).length === 0 ? (
              <Card elevation={0}>
                <CardContent sx={{ textAlign: 'center', py: 8 }}>
                  <Quiz sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    No templates found
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Create your first template to get started!
                  </Typography>
                </CardContent>
              </Card>
            ) : (
              Object.entries(groupedTemplates).map(([courseSubject, templateList]) => (
                <Box key={courseSubject} mb={4}>
                  <Typography variant="h5" gutterBottom sx={{ mb: 2 }}>
                    {courseSubject}
                  </Typography>
                  <Grid container spacing={3}>
                    {templateList.map((template) => (
                      <Grid item xs={12} sm={6} md={4} key={template.template_id}>
                        <Card 
                          elevation={0}
                          sx={{ 
                            height: '100%',
                            display: 'flex',
                            flexDirection: 'column',
                            cursor: 'pointer',
                            transition: 'all 0.3s ease',
                            '&:hover': {
                              transform: 'translateY(-4px)',
                              boxShadow: '0 8px 25px rgba(0,0,0,0.15)',
                            }
                          }}
                          onClick={() => handleTemplateClick(template.template_id)}
                        >
                          <CardContent sx={{ flexGrow: 1 }}>
                            <Box display="flex" justifyContent="space-between" alignItems="start" mb={1}>
                              <Typography variant="h6" gutterBottom sx={{ flexGrow: 1, pr: 1 }}>
                                {template.title}
                              </Typography>
                              {userIsAdmin && (
                                <Box display="flex" gap={0.5}>
                                  <Tooltip title="Edit Template">
                                    <IconButton
                                      size="small"
                                      color="primary"
                                      onClick={(e) => handleEditTemplate(e, template.template_id)}
                                    >
                                      <Edit fontSize="small" />
                                    </IconButton>
                                  </Tooltip>
                                  <Tooltip title="Delete Template">
                                    <IconButton
                                      size="small"
                                      color="error"
                                      onClick={(e) => handleDeleteClick(e, template)}
                                    >
                                      <DeleteIcon fontSize="small" />
                                    </IconButton>
                                  </Tooltip>
                                </Box>
                              )}
                            </Box>
                            <Box display="flex" alignItems="center" gap={1} mb={2}>
                              <Chip 
                                label={`${template.question_count} questions`}
                                size="small"
                                color="primary"
                                variant="outlined"
                              />
                            </Box>
                            <Typography variant="body2" color="text.secondary">
                              Created: {(() => {
                                const date = new Date(template.created_at);
                                const istDate = new Date(date.toLocaleString('en-US', { timeZone: 'Asia/Kolkata' }));
                                const day = String(istDate.getDate()).padStart(2, '0');
                                const month = String(istDate.getMonth() + 1).padStart(2, '0');
                                const year = istDate.getFullYear();
                                return `${day}/${month}/${year}`;
                              })()}
                            </Typography>
                          </CardContent>
                          <CardActions>
                            <Button 
                              size="small" 
                              startIcon={<Quiz />}
                              fullWidth
                              variant="contained"
                            >
                              Take Quiz
                            </Button>
                          </CardActions>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                </Box>
              ))
            )}
          </Box>
        )}
      </Container>

      {/* Floating Action Button removed - students don't need quick access to create templates */}

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={handleDeleteCancel}
      >
        <DialogTitle>Delete Template</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete the template "{templateToDelete?.title}"?
            This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel} color="primary">
            Cancel
          </Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={handleSnackbarClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleSnackbarClose} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Dashboard;