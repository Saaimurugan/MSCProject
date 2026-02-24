"""
Property-based tests for quiz submission using Hypothesis.
Feature: simplify-quiz-app
"""
import json
import sys
import os
from unittest.mock import patch, MagicMock

import pytest
from hypothesis import given, strategies as st, settings, assume

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from submit_quiz import lambda_handler


# Custom strategies for generating test data
@st.composite
def valid_question(draw):
    """Generate a valid question with at least 2 options and a correct answer."""
    num_options = draw(st.integers(min_value=2, max_value=10))
    options = [draw(st.text(min_size=1, max_size=100)) for _ in range(num_options)]
    correct_answer = draw(st.integers(min_value=0, max_value=num_options - 1))
    
    return {
        'question_text': draw(st.text(min_size=1, max_size=500)),
        'options': options,
        'correct_answer': correct_answer
    }


@st.composite
def valid_template_with_questions(draw):
    """Generate a valid template with questions."""
    num_questions = draw(st.integers(min_value=1, max_value=20))
    questions = [draw(valid_question()) for _ in range(num_questions)]
    
    return {
        'template_id': draw(st.text(min_size=1, max_size=50)),
        'title': draw(st.text(min_size=1, max_size=200)),
        'subject': draw(st.text(min_size=1, max_size=100)),
        'course': draw(st.text(min_size=1, max_size=100)),
        'questions': questions
    }


@st.composite
def valid_answers_for_template(draw, template):
    """Generate valid answers for all questions in a template."""
    answers = []
    for idx, question in enumerate(template['questions']):
        num_options = len(question['options'])
        selected_answer = draw(st.integers(min_value=0, max_value=num_options - 1))
        answers.append({
            'question_index': idx,
            'selected_answer': selected_answer
        })
    return answers


@st.composite
def incomplete_answers_for_template(draw, template):
    """Generate incomplete answers (missing at least one question)."""
    num_questions = len(template['questions'])
    assume(num_questions > 1)  # Need at least 2 questions to have incomplete answers
    
    # Answer between 0 and num_questions-1 questions (not all)
    num_to_answer = draw(st.integers(min_value=0, max_value=num_questions - 1))
    
    # Select which questions to answer
    questions_to_answer = draw(st.lists(
        st.integers(min_value=0, max_value=num_questions - 1),
        min_size=num_to_answer,
        max_size=num_to_answer,
        unique=True
    ))
    
    answers = []
    for idx in questions_to_answer:
        question = template['questions'][idx]
        num_options = len(question['options'])
        selected_answer = draw(st.integers(min_value=0, max_value=num_options - 1))
        answers.append({
            'question_index': idx,
            'selected_answer': selected_answer
        })
    
    return answers


# Property 7: Score Calculation Accuracy
# **Validates: Requirements 3.4**

@settings(max_examples=100)
@given(template=valid_template_with_questions())
def test_property_score_calculation_accuracy(template):
    """
    Property 7: Score Calculation Accuracy
    
    For any set of quiz answers and corresponding template, the calculated score
    should equal the percentage of questions answered correctly
    (correct_count / total_questions * 100).
    
    **Validates: Requirements 3.4**
    """
    # Generate answers for this template
    answers = []
    expected_correct = 0
    
    for idx, question in enumerate(template['questions']):
        # Randomly decide if this answer is correct or not
        num_options = len(question['options'])
        correct_answer = question['correct_answer']
        
        # 50% chance of correct answer
        if idx % 2 == 0:
            selected_answer = correct_answer
            expected_correct += 1
        else:
            # Select a wrong answer
            wrong_options = [i for i in range(num_options) if i != correct_answer]
            selected_answer = wrong_options[0] if wrong_options else correct_answer
            if selected_answer == correct_answer:
                expected_correct += 1
        
        answers.append({
            'question_index': idx,
            'selected_answer': selected_answer
        })
    
    with patch('submit_quiz.dynamodb') as mock_db:
        mock_table = MagicMock()
        mock_db.Table.return_value = mock_table
        mock_table.get_item.return_value = {'Item': template}
        mock_table.put_item.return_value = {}
        
        event = {
            'httpMethod': 'POST',
            'body': json.dumps({
                'template_id': template['template_id'],
                'answers': answers
            })
        }
        
        response = lambda_handler(event, None)
        
        # Should return 200 success
        assert response['statusCode'] == 200
        
        body = json.loads(response['body'])
        
        # Verify score calculation
        total_questions = len(template['questions'])
        expected_score = (expected_correct / total_questions * 100) if total_questions > 0 else 0
        
        assert body['correct_count'] == expected_correct, \
            f"Expected {expected_correct} correct, got {body['correct_count']}"
        assert body['total_questions'] == total_questions, \
            f"Expected {total_questions} total questions, got {body['total_questions']}"
        assert abs(body['total_score'] - expected_score) < 0.01, \
            f"Expected score {expected_score}, got {body['total_score']}"


# Property 8: Complete Answer Validation
# **Validates: Requirements 3.5**

@settings(max_examples=100)
@given(template=valid_template_with_questions())
def test_property_complete_answer_validation(template):
    """
    Property 8: Complete Answer Validation
    
    For any quiz submission where not all questions have been answered,
    the system should reject the submission and return a validation error.
    
    **Validates: Requirements 3.5**
    """
    # Generate incomplete answers
    num_questions = len(template['questions'])
    assume(num_questions > 1)  # Need at least 2 questions to test incomplete answers
    
    # Answer only some questions (not all)
    num_to_answer = min(num_questions - 1, max(0, num_questions // 2))
    
    answers = []
    for idx in range(num_to_answer):
        question = template['questions'][idx]
        num_options = len(question['options'])
        selected_answer = 0  # Just pick first option
        answers.append({
            'question_index': idx,
            'selected_answer': selected_answer
        })
    
    with patch('submit_quiz.dynamodb') as mock_db:
        mock_table = MagicMock()
        mock_db.Table.return_value = mock_table
        mock_table.get_item.return_value = {'Item': template}
        
        event = {
            'httpMethod': 'POST',
            'body': json.dumps({
                'template_id': template['template_id'],
                'answers': answers
            })
        }
        
        response = lambda_handler(event, None)
        
        # Should return 400 validation error
        assert response['statusCode'] == 400, \
            f"Expected 400 for incomplete answers, got {response['statusCode']}"
        
        body = json.loads(response['body'])
        assert body['error'] == 'All questions must be answered', \
            f"Expected validation error, got: {body.get('error')}"
        assert body['expected_questions'] == num_questions, \
            f"Expected {num_questions} questions, got {body.get('expected_questions')}"
        assert body['answered_questions'] == num_to_answer, \
            f"Expected {num_to_answer} answered, got {body.get('answered_questions')}"


# Property 9: Score Range Validity
# **Validates: Requirements 4.1**

@settings(max_examples=100)
@given(template=valid_template_with_questions())
def test_property_score_range_validity(template):
    """
    Property 9: Score Range Validity
    
    For any calculated quiz score, the value should be between 0 and 100 inclusive.
    
    **Validates: Requirements 4.1**
    """
    # Generate random answers for this template
    answers = []
    
    for idx, question in enumerate(template['questions']):
        num_options = len(question['options'])
        # Pick a random answer (could be correct or incorrect)
        selected_answer = idx % num_options
        
        answers.append({
            'question_index': idx,
            'selected_answer': selected_answer
        })
    
    with patch('submit_quiz.dynamodb') as mock_db:
        mock_table = MagicMock()
        mock_db.Table.return_value = mock_table
        mock_table.get_item.return_value = {'Item': template}
        mock_table.put_item.return_value = {}
        
        event = {
            'httpMethod': 'POST',
            'body': json.dumps({
                'template_id': template['template_id'],
                'answers': answers
            })
        }
        
        response = lambda_handler(event, None)
        
        # Should return 200 success
        assert response['statusCode'] == 200
        
        body = json.loads(response['body'])
        
        # Verify score is within valid range [0, 100]
        total_score = body['total_score']
        assert 0 <= total_score <= 100, \
            f"Score {total_score} is outside valid range [0, 100]"
        
        # Additional verification: score should match the calculation
        correct_count = body['correct_count']
        total_questions = body['total_questions']
        expected_score = (correct_count / total_questions * 100) if total_questions > 0 else 0
        
        assert abs(total_score - expected_score) < 0.01, \
            f"Score {total_score} doesn't match expected {expected_score}"
