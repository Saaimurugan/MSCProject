import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import theme from './theme';

// Components
import Dashboard from './components/dashboard/Dashboard';
import QuizTaking from './components/quiz/QuizTaking';
import QuizResults from './components/quiz/QuizResults';
import TemplateCreator from './components/templates/TemplateCreator';

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <div className="App">
          <Routes>
            {/* Main Routes */}
            <Route path="/" element={<Dashboard />} />
            <Route path="/template/create" element={<TemplateCreator />} />
            <Route path="/quiz/:templateId" element={<QuizTaking />} />
            <Route path="/quiz/:templateId/results" element={<QuizResults />} />
            
            {/* Catch all route - redirect to landing page */}
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </div>
      </Router>
    </ThemeProvider>
  );
}

export default App;