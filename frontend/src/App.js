import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import theme from './theme';
import { isAuthenticated, isAdmin } from './utils/auth';

// Components
import Login from './components/auth/Login';
import Dashboard from './components/dashboard/Dashboard';
import QuizTaking from './components/quiz/QuizTaking';
import QuizResults from './components/quiz/QuizResults';
import TemplateCreator from './components/templates/TemplateCreator';
import TemplateEditor from './components/templates/TemplateEditor';
import ResultsReport from './components/results/ResultsReport';

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  return isAuthenticated() ? children : <Navigate to="/login" />;
};

// Admin Only Route Component
const AdminRoute = ({ children }) => {
  if (!isAuthenticated()) {
    return <Navigate to="/login" />;
  }
  if (!isAdmin()) {
    return <Navigate to="/dashboard" />;
  }
  return children;
};

function App() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    // Check if user is already logged in
    const userStr = localStorage.getItem('user');
    if (userStr) {
      try {
        setUser(JSON.parse(userStr));
      } catch (e) {
        localStorage.removeItem('user');
      }
    }
  }, []);

  const handleLogin = (userInfo) => {
    setUser(userInfo);
  };

  const handleLogout = () => {
    localStorage.removeItem('user');
    setUser(null);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <div className="App">
          <Routes>
            {/* Login Route */}
            <Route 
              path="/login" 
              element={
                isAuthenticated() ? <Navigate to="/dashboard" /> : <Login onLogin={handleLogin} />
              } 
            />

            {/* Protected Routes */}
            <Route 
              path="/" 
              element={
                <ProtectedRoute>
                  <Dashboard onLogout={handleLogout} />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/dashboard" 
              element={
                <ProtectedRoute>
                  <Dashboard onLogout={handleLogout} />
                </ProtectedRoute>
              } 
            />
            
            {/* Admin Only Routes */}
            <Route 
              path="/template/create" 
              element={
                <AdminRoute>
                  <TemplateCreator />
                </AdminRoute>
              } 
            />
            <Route 
              path="/template/edit/:templateId" 
              element={
                <AdminRoute>
                  <TemplateEditor />
                </AdminRoute>
              } 
            />
            <Route 
              path="/results" 
              element={
                <AdminRoute>
                  <ResultsReport />
                </AdminRoute>
              } 
            />

            {/* Student and Admin Routes */}
            <Route 
              path="/quiz/:templateId" 
              element={
                <ProtectedRoute>
                  <QuizTaking />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/quiz/:templateId/results" 
              element={
                <ProtectedRoute>
                  <QuizResults />
                </ProtectedRoute>
              } 
            />
            
            {/* Catch all route - redirect to login or dashboard */}
            <Route 
              path="*" 
              element={<Navigate to={isAuthenticated() ? "/dashboard" : "/login"} />} 
            />
          </Routes>
        </div>
      </Router>
    </ThemeProvider>
  );
}

export default App;