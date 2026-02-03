import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://your-api-gateway-url.amazonaws.com/dev';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API calls
export const authAPI = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  signup: (email, password, name, role = 'student') => 
    api.post('/auth/signup', { email, password, name, role }),
  forgotPassword: (email) => api.post('/auth/forgot-password', { email }),
};

// Templates API calls
export const templatesAPI = {
  getTemplates: (subject, course) => {
    const params = {};
    if (subject) params.subject = subject;
    if (course) params.course = course;
    return api.get('/templates', { params });
  },
  getTemplate: (templateId) => api.get(`/templates/${templateId}`),
  createTemplate: (templateData) => api.post('/templates', templateData),
  updateTemplate: (templateId, templateData) => 
    api.put(`/templates/${templateId}`, templateData),
  deleteTemplate: (templateId) => api.delete(`/templates/${templateId}`),
};

// Quiz API calls
export const quizAPI = {
  getQuiz: (templateId) => api.get(`/quiz/${templateId}`),
  submitQuiz: (quizData) => api.post('/quiz/submit', quizData),
  getResults: (userId) => api.get(`/quiz/results/${userId}`),
};

// Reports API calls
export const reportsAPI = {
  getUserReports: (userId) => api.get(`/reports/user/${userId}`),
  getTemplateReports: (templateId) => api.get(`/reports/template/${templateId}`),
  getAllReports: () => api.get('/reports/all'),
};

// Admin API calls
export const adminAPI = {
  getUsers: () => api.get('/admin/users'),
  createUser: (userData) => api.post('/admin/users', userData),
  updateUserRole: (userId, role) => api.put(`/admin/users/${userId}/role`, { role }),
  deleteUser: (userId) => api.delete(`/admin/users/${userId}`),
  getUsageLogs: () => api.get('/admin/logs'),
};

// Profile API calls
export const profileAPI = {
  getProfile: () => api.get('/profile'),
  updateProfile: (profileData) => api.put('/profile', profileData),
  changePassword: (passwordData) => api.put('/profile/password', passwordData),
};

export default api;