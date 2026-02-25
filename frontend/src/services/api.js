import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://your-api-gateway-url.amazonaws.com/dev';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

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

export default api;