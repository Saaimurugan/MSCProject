import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthService } from './services/auth';

// Components
import Login from './components/auth/Login';
import Signup from './components/auth/Signup';
import Dashboard from './components/dashboard/Dashboard';
import QuizTaking from './components/quiz/QuizTaking';

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  return AuthService.isAuthenticated() ? children : <Navigate to="/login" />;
};

// Public Route Component (redirect if already authenticated)
const PublicRoute = ({ children }) => {
  return !AuthService.isAuthenticated() ? children : <Navigate to="/dashboard" />;
};

function App() {
  return (
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

          {/* Default redirect */}
          <Route path="/" element={<Navigate to="/dashboard" />} />
          
          {/* Catch all route */}
          <Route path="*" element={<Navigate to="/dashboard" />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;