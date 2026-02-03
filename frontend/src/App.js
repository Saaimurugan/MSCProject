import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import theme from './theme';
import { AuthService } from './services/auth';

// Components
import Login from './components/auth/Login';
import Signup from './components/auth/Signup';
import Dashboard from './components/dashboard/Dashboard';
import QuizTaking from './components/quiz/QuizTaking';
import Admin from './components/admin/Admin';
import Reports from './components/reports/Reports';
import Profile from './components/profile/Profile';

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  return AuthService.isAuthenticated() ? children : <Navigate to="/login" />;
};

// Admin Route Component
const AdminRoute = ({ children }) => {
  return AuthService.isAuthenticated() && AuthService.hasRole('admin') 
    ? children 
    : <Navigate to="/dashboard" />;
};

// Public Route Component (redirect if already authenticated)
const PublicRoute = ({ children }) => {
  return !AuthService.isAuthenticated() ? children : <Navigate to="/dashboard" />;
};

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <div className="App">
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={
              <PublicRoute>
                <Login />
              </PublicRoute>
            } />
            <Route path="/signup" element={
              <PublicRoute>
                <Signup />
              </PublicRoute>
            } />

            {/* Protected Routes */}
            <Route path="/dashboard" element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } />
            <Route path="/quiz/:templateId" element={
              <ProtectedRoute>
                <QuizTaking />
              </ProtectedRoute>
            } />
            <Route path="/reports" element={
              <ProtectedRoute>
                <Reports />
              </ProtectedRoute>
            } />
            <Route path="/profile" element={
              <ProtectedRoute>
                <Profile />
              </ProtectedRoute>
            } />

            {/* Admin Routes */}
            <Route path="/admin" element={
              <AdminRoute>
                <Admin />
              </AdminRoute>
            } />

            {/* Default redirect */}
            <Route path="/" element={<Navigate to="/dashboard" />} />
            
            {/* Catch all route */}
            <Route path="*" element={<Navigate to="/dashboard" />} />
          </Routes>
        </div>
      </Router>
    </ThemeProvider>
  );
}

export default App;