import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://your-api-gateway-url.amazonaws.com/dev';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include user role in headers
api.interceptors.request.use((config) => {
  const userStr = localStorage.getItem('user');
  if (userStr) {
    try {
      const user = JSON.parse(userStr);
      if (user.role) {
        config.headers['X-User-Role'] = user.role;
      }
    } catch (e) {
      console.error('Failed to parse user from localStorage', e);
    }
  }
  return config;
});

// Authentication API calls
export const authAPI = {
  login: (username, password) => api.post('/users/login', { username, password }),
};

// User Management API calls (Admin only)
export const usersAPI = {
  getUsers: (filters) => {
    const params = {};
    if (filters?.role) params.role = filters.role;
    if (filters?.is_active !== undefined) params.is_active = filters.is_active;
    return api.get('/users', { params });
  },
  getUserById: (userId) => api.get(`/users/${userId}`),
  createUser: (userData) => api.post('/users', userData),
  updateUser: (userId, userData) => api.put(`/users/${userId}`, userData),
  deleteUser: (userId) => api.delete(`/users/${userId}`),
};

// Templates API calls
export const templatesAPI = {
  getTemplates: (subject, course) => {
    const params = {};
    if (subject) params.subject = subject;
    if (course) params.course = course;
    return api.get('/templates', { params });
  },
  getTemplateById: (templateId) => api.get(`/templates/${templateId}`),
  createTemplate: (templateData) => api.post('/templates', templateData),
  updateTemplate: (templateId, templateData) => api.put(`/templates/${templateId}`, templateData),
  deleteTemplate: (templateId) => api.delete(`/templates/${templateId}`),
};

// Quiz API calls
export const quizAPI = {
  submitQuiz: (quizData) => api.post('/submit', quizData),
};

// Results API calls
export const resultsAPI = {
  getAllResults: (filters) => {
    const params = {};
    if (filters?.student_name) params.student_name = filters.student_name;
    if (filters?.course) params.course = filters.course;
    if (filters?.subject) params.subject = filters.subject;
    return api.get('/results', { params });
  },
  deleteResult: (resultId) => api.delete(`/results/${resultId}`),
};

export default api;
