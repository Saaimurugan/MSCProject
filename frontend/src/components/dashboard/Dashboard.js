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
  IconButton,
  Menu,
  MenuItem,
  Chip,
  FormControl,
  InputLabel,
  Select,
  CircularProgress,
  Alert,
  Avatar,
  Fab,
  Tooltip,
} from '@mui/material';
import {
  AccountCircle,
  Logout,
  Quiz,
  Assessment,
  AdminPanelSettings,
  Add,
  FilterList,
  School,
  Person,
} from '@mui/icons-material';
import { templatesAPI } from '../../services/api';
import { AuthService } from '../../services/auth';

const Dashboard = () => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedSubject, setSelectedSubject] = useState('');
  const [selectedCourse, setCourse] = useState('');
  const [anchorEl, setAnchorEl] = useState(null);
  const navigate = useNavigate();
  const user = AuthService.getUser();

  useEffect(() => {
    loadTemplates();
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

  const handleMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    AuthService.logout();
  };

  const getRoleColor = (role) => {
    switch (role) {
      case 'admin': return 'error';
      case 'tutor': return 'warning';
      case 'student': return 'success';
      default: return 'default';
    }
  };

  // Group templates by subject and course
  const groupedTemplates = Array.isArray(templates) ? templates.reduce((acc, template) => {
    const key = `${template.subject} - ${template.course}`;
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
            MSC Evaluate Dashboard
          </Typography>
          
          <Box display="flex" alignItems="center" gap={2}>
            <Chip
              label={user?.role?.toUpperCase()}
              color={getRoleColor(user?.role)}
              size="small"
              sx={{ color: 'white', borderColor: 'rgba(255,255,255,0.3)' }}
              variant="outlined"
            />
            <IconButton
              size="large"
              edge="end"
              color="inherit"
              onClick={handleMenuOpen}
            >
              <Avatar sx={{ width: 32, height: 32, bgcolor: 'rgba(255,255,255,0.2)' }}>
                <Person fontSize="small" />
              </Avatar>
            </IconButton>
          </Box>

          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
            transformOrigin={{ horizontal: 'right', vertical: 'top' }}
            anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
          >
            <MenuItem onClick={() => { navigate('/profile'); handleMenuClose(); }}>
              <AccountCircle sx={{ mr: 1 }} /> Profile
            </MenuItem>
            <MenuItem onClick={() => { navigate('/reports'); handleMenuClose(); }}>
              <Assessment sx={{ mr: 1 }} /> Reports
            </MenuItem>
            {AuthService.hasRole('admin') && (
              <MenuItem onClick={() => { navigate('/admin'); handleMenuClose(); }}>
                <AdminPanelSettings sx={{ mr: 1 }} /> Admin Panel
              </MenuItem>
            )}
            <MenuItem onClick={handleLogout}>
              <Logout sx={{ mr: 1 }} /> Logout
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ py: 4 }}>
        {/* Welcome Section */}
        <Box mb={4}>
          <Typography variant="h4" gutterBottom>
            Welcome back, {user?.name}! 👋
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Ready to take some quizzes? Choose from the available templates below.
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
                  <InputLabel>Subject</InputLabel>
                  <Select
                    value={selectedSubject}
                    label="Subject"
                    onChange={(e) => setSelectedSubject(e.target.value)}
                  >
                    <MenuItem value="">All Subjects</MenuItem>
                    <MenuItem value="Computer Science">Computer Science</MenuItem>
                    <MenuItem value="Mathematics">Mathematics</MenuItem>
                    <MenuItem value="Physics">Physics</MenuItem>
                    <MenuItem value="Chemistry">Chemistry</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <FormControl fullWidth>
                  <InputLabel>Course</InputLabel>
                  <Select
                    value={selectedCourse}
                    label="Course"
                    onChange={(e) => setCourse(e.target.value)}
                  >
                    <MenuItem value="">All Courses</MenuItem>
                    <MenuItem value="MSC-101">MSC-101</MenuItem>
                    <MenuItem value="MSC-102">MSC-102</MenuItem>
                    <MenuItem value="MSC-201">MSC-201</MenuItem>
                    <MenuItem value="MSC-202">MSC-202</MenuItem>
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
                    {AuthService.hasAnyRole(['admin', 'tutor']) 
                      ? 'Create your first template to get started!' 
                      : 'Check back later for new assignments.'}
                  </Typography>
                </CardContent>
              </Card>
            ) : (
              Object.entries(groupedTemplates).map(([subjectCourse, templateList]) => (
                <Box key={subjectCourse} mb={4}>
                  <Typography variant="h5" gutterBottom sx={{ mb: 2 }}>
                    {subjectCourse}
                  </Typography>
                  <Grid container spacing={3}>
                    {templateList.map((template) => (
                      <Grid item xs={12} sm={6} md={4} key={template.template_id}>
                        <Card 
                          elevation={0}
                          sx={{ 
                            height: '100%',
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
                            <Typography variant="h6" gutterBottom>
                              {template.title}
                            </Typography>
                            <Box display="flex" alignItems="center" gap={1} mb={2}>
                              <Chip 
                                label={`${template.question_count} questions`}
                                size="small"
                                color="primary"
                                variant="outlined"
                              />
                            </Box>
                            <Typography variant="body2" color="text.secondary">
                              Created: {new Date(template.created_at).toLocaleDateString()}
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

      {/* Floating Action Button for Create Template */}
      {AuthService.hasAnyRole(['admin', 'tutor']) && (
        <Tooltip title="Create Template">
          <Fab
            color="primary"
            sx={{
              position: 'fixed',
              bottom: 24,
              right: 24,
            }}
            onClick={handleCreateTemplate}
          >
            <Add />
          </Fab>
        </Tooltip>
      )}
    </Box>
  );
};

export default Dashboard;