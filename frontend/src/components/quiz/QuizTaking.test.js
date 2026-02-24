import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import QuizTaking from './QuizTaking';
import { templatesAPI, quizAPI } from '../../services/api';

// Mock the API services
jest.mock('../../services/api');

// Mock useNavigate and useParams
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useParams: () => ({ templateId: 'test-template-123' }),
}));

const mockTemplate = {
  template_id: 'test-template-123',
  title: 'JavaScript Basics',
  subject: 'Programming',
  course: 'CS101',
  questions: [
    {
      question_text: 'What is JavaScript?',
      options: ['A programming language', 'A coffee brand', 'A type of script', 'None of the above'],
      correct_answer: 0
    },
    {
      question_text: 'What does DOM stand for?',
      options: ['Document Object Model', 'Data Object Model', 'Digital Object Model', 'None'],
      correct_answer: 0
    }
  ]
};

describe('QuizTaking Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders loading state initially', () => {
    templatesAPI.getTemplateById.mockReturnValue(new Promise(() => {}));
    
    render(
      <BrowserRouter>
        <QuizTaking />
      </BrowserRouter>
    );
    
    expect(screen.getByText(/loading quiz/i)).toBeInTheDocument();
  });

  test('loads and displays quiz template', async () => {
    templatesAPI.getTemplateById.mockResolvedValue({ data: mockTemplate });
    
    render(
      <BrowserRouter>
        <QuizTaking />
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText('JavaScript Basics')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Programming - CS101')).toBeInTheDocument();
    expect(screen.getByText('What is JavaScript?')).toBeInTheDocument();
  });

  test('does not show correct answers during quiz', async () => {
    templatesAPI.getTemplateById.mockResolvedValue({ data: mockTemplate });
    
    render(
      <BrowserRouter>
        <QuizTaking />
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText('What is JavaScript?')).toBeInTheDocument();
    });
    
    // All options should be displayed without indication of which is correct
    expect(screen.getByText('A programming language')).toBeInTheDocument();
    expect(screen.getByText('A coffee brand')).toBeInTheDocument();
    
    // No visual indication of correct answer should be present
    const options = screen.getAllByRole('radio');
    options.forEach(option => {
      expect(option).not.toHaveClass('correct');
      expect(option).not.toHaveAttribute('data-correct');
    });
  });

  test('allows selecting answers', async () => {
    templatesAPI.getTemplateById.mockResolvedValue({ data: mockTemplate });
    
    render(
      <BrowserRouter>
        <QuizTaking />
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText('What is JavaScript?')).toBeInTheDocument();
    });
    
    const firstOption = screen.getByLabelText(/A programming language/i);
    fireEvent.click(firstOption);
    
    expect(firstOption).toBeChecked();
  });

  test('navigates between questions', async () => {
    templatesAPI.getTemplateById.mockResolvedValue({ data: mockTemplate });
    
    render(
      <BrowserRouter>
        <QuizTaking />
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText('What is JavaScript?')).toBeInTheDocument();
    });
    
    const nextButton = screen.getByText('Next');
    fireEvent.click(nextButton);
    
    expect(screen.getByText('What does DOM stand for?')).toBeInTheDocument();
    
    const previousButton = screen.getByText('Previous');
    fireEvent.click(previousButton);
    
    expect(screen.getByText('What is JavaScript?')).toBeInTheDocument();
  });

  test('validates all questions answered before submission', async () => {
    templatesAPI.getTemplateById.mockResolvedValue({ data: mockTemplate });
    
    render(
      <BrowserRouter>
        <QuizTaking />
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText('What is JavaScript?')).toBeInTheDocument();
    });
    
    // Navigate to last question without answering
    const nextButton = screen.getByText('Next');
    fireEvent.click(nextButton);
    
    const submitButton = screen.getByText('Submit Quiz');
    fireEvent.click(submitButton);
    
    // Should show validation error
    await waitFor(() => {
      expect(screen.getByText(/please answer all questions/i)).toBeInTheDocument();
    });
    
    // Should not call submit API
    expect(quizAPI.submitQuiz).not.toHaveBeenCalled();
  });

  test('submits quiz with all answers and navigates to results', async () => {
    templatesAPI.getTemplateById.mockResolvedValue({ data: mockTemplate });
    quizAPI.submitQuiz.mockResolvedValue({
      data: {
        result_id: 'result-123',
        total_score: 100,
        correct_count: 2,
        total_questions: 2,
        detailed_results: []
      }
    });
    
    render(
      <BrowserRouter>
        <QuizTaking />
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText('What is JavaScript?')).toBeInTheDocument();
    });
    
    // Answer first question
    const firstOption = screen.getByLabelText(/A programming language/i);
    fireEvent.click(firstOption);
    
    // Navigate to second question
    const nextButton = screen.getByText('Next');
    fireEvent.click(nextButton);
    
    // Answer second question
    const secondOption = screen.getByLabelText(/Document Object Model/i);
    fireEvent.click(secondOption);
    
    // Submit quiz
    const submitButton = screen.getByText('Submit Quiz');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(quizAPI.submitQuiz).toHaveBeenCalledWith({
        template_id: 'test-template-123',
        answers: [
          { question_index: 0, selected_answer: 0 },
          { question_index: 1, selected_answer: 0 }
        ]
      });
    });
    
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith(
        '/quiz/test-template-123/results',
        expect.objectContaining({
          state: expect.objectContaining({
            results: expect.any(Object),
            template: mockTemplate
          })
        })
      );
    });
  });

  test('displays error message on API failure', async () => {
    templatesAPI.getTemplateById.mockRejectedValue(new Error('API Error'));
    
    render(
      <BrowserRouter>
        <QuizTaking />
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText(/failed to load quiz/i)).toBeInTheDocument();
    });
  });

  test('shows question progress indicator', async () => {
    templatesAPI.getTemplateById.mockResolvedValue({ data: mockTemplate });
    
    render(
      <BrowserRouter>
        <QuizTaking />
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText('Question 1 of 2')).toBeInTheDocument();
    });
    
    const nextButton = screen.getByText('Next');
    fireEvent.click(nextButton);
    
    expect(screen.getByText('Question 2 of 2')).toBeInTheDocument();
  });
});
