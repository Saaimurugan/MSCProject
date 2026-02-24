import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import TemplateCreator from './TemplateCreator';
import { templatesAPI } from '../../services/api';

// Mock the API
jest.mock('../../services/api', () => ({
  templatesAPI: {
    createTemplate: jest.fn(),
  },
}));

// Mock useNavigate
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

describe('TemplateCreator Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const renderComponent = () => {
    return render(
      <BrowserRouter>
        <TemplateCreator />
      </BrowserRouter>
    );
  };

  test('renders template creation form', () => {
    renderComponent();
    
    expect(screen.getByText('Create Quiz Template')).toBeInTheDocument();
    expect(screen.getByLabelText(/Title/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Subject/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Course/i)).toBeInTheDocument();
    expect(screen.getByText('Question 1')).toBeInTheDocument();
  });

  test('validates title as non-empty', async () => {
    renderComponent();
    
    const submitButton = screen.getByRole('button', { name: /Create Template/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Title is required and cannot be empty')).toBeInTheDocument();
    });
  });

  test('validates subject as non-empty', async () => {
    renderComponent();
    
    const submitButton = screen.getByRole('button', { name: /Create Template/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Subject is required and cannot be empty')).toBeInTheDocument();
    });
  });

  test('validates course as non-empty', async () => {
    renderComponent();
    
    const submitButton = screen.getByRole('button', { name: /Create Template/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Course is required and cannot be empty')).toBeInTheDocument();
    });
  });

  test('validates minimum 2 options per question', async () => {
    renderComponent();
    
    // Fill in required fields
    fireEvent.change(screen.getByLabelText(/Title/i), { target: { value: 'Test Quiz' } });
    fireEvent.change(screen.getByLabelText(/Subject/i), { target: { value: 'Math' } });
    fireEvent.change(screen.getByLabelText(/Course/i), { target: { value: 'MATH-101' } });
    
    // Clear one option to have less than 2
    const optionInputs = screen.getAllByLabelText(/Option \d+/i);
    fireEvent.change(optionInputs[0], { target: { value: '' } });
    fireEvent.change(optionInputs[1], { target: { value: '' } });
    
    const submitButton = screen.getByRole('button', { name: /Create Template/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('At least 2 answer options are required')).toBeInTheDocument();
    });
  });

  test('allows adding and removing questions', () => {
    renderComponent();
    
    // Initially should have 1 question
    expect(screen.getByText('Question 1')).toBeInTheDocument();
    expect(screen.queryByText('Question 2')).not.toBeInTheDocument();
    
    // Add a question
    const addQuestionButton = screen.getByRole('button', { name: /Add Question/i });
    fireEvent.click(addQuestionButton);
    
    expect(screen.getByText('Question 2')).toBeInTheDocument();
  });

  test('allows adding and removing options', () => {
    renderComponent();
    
    // Initially should have 2 options
    const initialOptions = screen.getAllByLabelText(/Option \d+/i);
    expect(initialOptions).toHaveLength(2);
    
    // Add an option
    const addOptionButton = screen.getByRole('button', { name: /Add Option/i });
    fireEvent.click(addOptionButton);
    
    const updatedOptions = screen.getAllByLabelText(/Option \d+/i);
    expect(updatedOptions).toHaveLength(3);
  });

  test('submits valid template successfully', async () => {
    templatesAPI.createTemplate.mockResolvedValue({
      data: { template_id: '123', message: 'Template created successfully' },
    });
    
    renderComponent();
    
    // Fill in all required fields
    fireEvent.change(screen.getByLabelText(/Title/i), { target: { value: 'Test Quiz' } });
    fireEvent.change(screen.getByLabelText(/Subject/i), { target: { value: 'Math' } });
    fireEvent.change(screen.getByLabelText(/Course/i), { target: { value: 'MATH-101' } });
    
    // Fill in question
    fireEvent.change(screen.getByLabelText(/Question Text/i), { 
      target: { value: 'What is 2+2?' } 
    });
    
    // Fill in options
    const optionInputs = screen.getAllByLabelText(/Option \d+/i);
    fireEvent.change(optionInputs[0], { target: { value: '3' } });
    fireEvent.change(optionInputs[1], { target: { value: '4' } });
    
    // Select correct answer
    const radioButtons = screen.getAllByRole('radio');
    fireEvent.click(radioButtons[1]); // Select second option as correct
    
    // Submit
    const submitButton = screen.getByRole('button', { name: /Create Template/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(templatesAPI.createTemplate).toHaveBeenCalledWith({
        title: 'Test Quiz',
        subject: 'Math',
        course: 'MATH-101',
        questions: [
          {
            question_text: 'What is 2+2?',
            options: ['3', '4'],
            correct_answer: 1,
          },
        ],
      });
    });
    
    await waitFor(() => {
      expect(screen.getByText('Template created successfully!')).toBeInTheDocument();
    });
  });

  test('displays error message on API failure', async () => {
    templatesAPI.createTemplate.mockRejectedValue({
      response: { data: { message: 'Failed to create template' } },
    });
    
    renderComponent();
    
    // Fill in all required fields
    fireEvent.change(screen.getByLabelText(/Title/i), { target: { value: 'Test Quiz' } });
    fireEvent.change(screen.getByLabelText(/Subject/i), { target: { value: 'Math' } });
    fireEvent.change(screen.getByLabelText(/Course/i), { target: { value: 'MATH-101' } });
    
    // Fill in question
    fireEvent.change(screen.getByLabelText(/Question Text/i), { 
      target: { value: 'What is 2+2?' } 
    });
    
    // Fill in options
    const optionInputs = screen.getAllByLabelText(/Option \d+/i);
    fireEvent.change(optionInputs[0], { target: { value: '3' } });
    fireEvent.change(optionInputs[1], { target: { value: '4' } });
    
    // Submit
    const submitButton = screen.getByRole('button', { name: /Create Template/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Failed to create template')).toBeInTheDocument();
    });
  });

  test('clears validation errors when user corrects input', async () => {
    renderComponent();
    
    // Submit to trigger validation errors
    const submitButton = screen.getByRole('button', { name: /Create Template/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Title is required and cannot be empty')).toBeInTheDocument();
    });
    
    // Fix the error
    fireEvent.change(screen.getByLabelText(/Title/i), { target: { value: 'Test Quiz' } });
    
    // Error should be cleared
    await waitFor(() => {
      expect(screen.queryByText('Title is required and cannot be empty')).not.toBeInTheDocument();
    });
  });

  test('navigates back to dashboard on cancel', () => {
    renderComponent();
    
    const cancelButton = screen.getByRole('button', { name: /Cancel/i });
    fireEvent.click(cancelButton);
    
    expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
  });
});
