import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import QuizResults from './QuizResults';

const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useLocation: () => ({
    state: {
      results: {
        result_id: 'result-123',
        total_score: 75,
        correct_count: 3,
        total_questions: 4,
        detailed_results: [
          {
            question_index: 0,
            is_correct: true,
            selected_answer: 0,
            correct_answer: 0
          },
          {
            question_index: 1,
            is_correct: false,
            selected_answer: 1,
            correct_answer: 2
          },
          {
            question_index: 2,
            is_correct: true,
            selected_answer: 2,
            correct_answer: 2
          },
          {
            question_index: 3,
            is_correct: true,
            selected_answer: 0,
            correct_answer: 0
          }
        ]
      },
      template: {
        template_id: 'template-123',
        title: 'JavaScript Basics',
        subject: 'Programming',
        course: 'CS101',
        questions: [
          {
            question_text: 'What is JavaScript?',
            options: ['A programming language', 'A coffee brand', 'A type of script', 'None'],
            correct_answer: 0
          },
          {
            question_text: 'What does DOM stand for?',
            options: ['Data Object Model', 'Digital Object Model', 'Document Object Model', 'None'],
            correct_answer: 2
          },
          {
            question_text: 'What is a variable?',
            options: ['A constant', 'A function', 'A storage location', 'A loop'],
            correct_answer: 2
          },
          {
            question_text: 'What is an array?',
            options: ['A collection of elements', 'A single value', 'A function', 'A loop'],
            correct_answer: 0
          }
        ]
      }
    }
  })
}));

describe('QuizResults Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('displays score percentage', () => {
    render(
      <BrowserRouter>
        <QuizResults />
      </BrowserRouter>
    );
    
    expect(screen.getByText('75%')).toBeInTheDocument();
  });

  test('displays correct count and total questions', () => {
    render(
      <BrowserRouter>
        <QuizResults />
      </BrowserRouter>
    );
    
    expect(screen.getByText(/3 out of 4 questions correct/i)).toBeInTheDocument();
  });

  test('displays template information', () => {
    render(
      <BrowserRouter>
        <QuizResults />
      </BrowserRouter>
    );
    
    expect(screen.getByText('JavaScript Basics')).toBeInTheDocument();
    expect(screen.getByText('Programming - CS101')).toBeInTheDocument();
  });

  test('shows correct answers for each question', () => {
    render(
      <BrowserRouter>
        <QuizResults />
      </BrowserRouter>
    );
    
    // Check that correct answers are displayed
    expect(screen.getByText('A programming language')).toBeInTheDocument();
    expect(screen.getByText('Document Object Model')).toBeInTheDocument();
  });

  test('displays detailed feedback for each question', () => {
    render(
      <BrowserRouter>
        <QuizResults />
      </BrowserRouter>
    );
    
    // Check for question texts
    expect(screen.getByText('What is JavaScript?')).toBeInTheDocument();
    expect(screen.getByText('What does DOM stand for?')).toBeInTheDocument();
    
    // Check for correct/incorrect badges
    const correctBadges = screen.getAllByText(/✓ Correct/i);
    const incorrectBadges = screen.getAllByText(/✗ Incorrect/i);
    
    expect(correctBadges).toHaveLength(3);
    expect(incorrectBadges).toHaveLength(1);
  });

  test('shows user answer and correct answer for incorrect questions', () => {
    render(
      <BrowserRouter>
        <QuizResults />
      </BrowserRouter>
    );
    
    // For the incorrect question (index 1), both user answer and correct answer should be shown
    expect(screen.getByText('Digital Object Model')).toBeInTheDocument(); // User's wrong answer
    expect(screen.getByText('Document Object Model')).toBeInTheDocument(); // Correct answer
  });

  test('navigates back to dashboard when clicking back button', () => {
    render(
      <BrowserRouter>
        <QuizResults />
      </BrowserRouter>
    );
    
    const backButton = screen.getByText('Back to Dashboard');
    fireEvent.click(backButton);
    
    expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
  });

  test('navigates to retake quiz when clicking retake button', () => {
    render(
      <BrowserRouter>
        <QuizResults />
      </BrowserRouter>
    );
    
    const retakeButton = screen.getByText('Retake Quiz');
    fireEvent.click(retakeButton);
    
    expect(mockNavigate).toHaveBeenCalledWith('/quiz/template-123');
  });

  test('handles missing results gracefully', () => {
    const mockUseLocation = jest.requireMock('react-router-dom').useLocation;
    const originalImplementation = mockUseLocation;
    
    // Temporarily override useLocation for this test
    jest.spyOn(require('react-router-dom'), 'useLocation').mockReturnValue({ state: null });
    
    render(
      <BrowserRouter>
        <QuizResults />
      </BrowserRouter>
    );
    
    expect(screen.getByText(/no results available/i)).toBeInTheDocument();
    expect(screen.getByText('Back to Dashboard')).toBeInTheDocument();
    
    // Restore original implementation
    jest.spyOn(require('react-router-dom'), 'useLocation').mockRestore();
  });
});
