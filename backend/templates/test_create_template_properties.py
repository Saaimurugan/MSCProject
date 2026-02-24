"""
Property-based tests for template creation using Hypothesis.
Feature: simplify-quiz-app
"""
import json
import sys
import os
from unittest.mock import patch, MagicMock

import pytest
from hypothesis import given, strategies as st, settings

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from create_template import lambda_handler


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
def invalid_question_few_options(draw):
    """Generate a question with fewer than 2 options."""
    num_options = draw(st.integers(min_value=0, max_value=1))
    options = [draw(st.text(min_size=1, max_size=100)) for _ in range(num_options)]
    correct_answer = 0 if num_options > 0 else None
    
    return {
        'question_text': draw(st.text(min_size=1, max_size=500)),
        'options': options,
        'correct_answer': correct_answer
    }


@st.composite
def invalid_question_no_correct_answer(draw):
    """Generate a question without a correct answer designation."""
    num_options = draw(st.integers(min_value=2, max_value=10))
    options = [draw(st.text(min_size=1, max_size=100)) for _ in range(num_options)]
    
    return {
        'question_text': draw(st.text(min_size=1, max_size=500)),
        'options': options
        # No correct_answer field
    }


@st.composite
def template_with_empty_field(draw, empty_field):
    """Generate a template with one empty required field."""
    fields = {
        'title': draw(st.text(min_size=1, max_size=200)),
        'subject': draw(st.text(min_size=1, max_size=100)),
        'course': draw(st.text(min_size=1, max_size=100)),
        'questions': [draw(valid_question())]
    }
    
    # Make the specified field empty
    fields[empty_field] = draw(st.sampled_from(['', '   ', '\t', '\n']))
    
    return fields


def mock_template_model():
    """Context manager to mock the Template model."""
    with patch('create_template.Template') as mock:
        instance = MagicMock()
        mock.return_value = instance
        instance.create_template.return_value = {
            'template_id': 'test-id',
            'title': 'Test',
            'subject': 'Test',
            'course': 'Test',
            'questions': [],
            'is_active': True,
            'created_at': '2024-01-01T00:00:00',
            'updated_at': '2024-01-01T00:00:00'
        }
        return mock


# Property 1: Question Validation
# **Validates: Requirements 1.3**

@settings(max_examples=100)
@given(
    title=st.text(min_size=1, max_size=200),
    subject=st.text(min_size=1, max_size=100),
    course=st.text(min_size=1, max_size=100),
    question=invalid_question_few_options()
)
def test_property_question_validation_min_options(title, subject, course, question):
    """
    Property 1: Question Validation - Minimum Options
    
    For any question being added to a template with fewer than 2 answer options,
    the system should reject the question.
    
    **Validates: Requirements 1.3**
    """
    with mock_template_model():
        event = {
            'body': json.dumps({
                'title': title,
                'subject': subject,
                'course': course,
                'questions': [question]
            })
        }
        
        response = lambda_handler(event, None)
        
        # Should return 400 validation error
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'Validation Error'
        assert 'at least 2 answer options' in body['message']


@settings(max_examples=100)
@given(
    title=st.text(min_size=1, max_size=200),
    subject=st.text(min_size=1, max_size=100),
    course=st.text(min_size=1, max_size=100),
    question=invalid_question_no_correct_answer()
)
def test_property_question_validation_correct_answer(title, subject, course, question):
    """
    Property 1: Question Validation - Correct Answer Required
    
    For any question being added to a template without a designated correct answer,
    the system should reject the question.
    
    **Validates: Requirements 1.3**
    """
    with mock_template_model():
        event = {
            'body': json.dumps({
                'title': title,
                'subject': subject,
                'course': course,
                'questions': [question]
            })
        }
        
        response = lambda_handler(event, None)
        
        # Should return 400 validation error
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'Validation Error'
        assert 'correct answer designated' in body['message']


# Property 3: Template Field Validation
# **Validates: Requirements 1.5**

@settings(max_examples=100)
@given(template_data=template_with_empty_field('title'))
def test_property_template_field_validation_empty_title(template_data):
    """
    Property 3: Template Field Validation - Empty Title
    
    For any template submission with empty title field,
    the system should reject the template and return a validation error.
    
    **Validates: Requirements 1.5**
    """
    with mock_template_model():
        event = {
            'body': json.dumps(template_data)
        }
        
        response = lambda_handler(event, None)
        
        # Should return 400 validation error
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'Validation Error'
        assert 'Title' in body['message']


@settings(max_examples=100)
@given(template_data=template_with_empty_field('subject'))
def test_property_template_field_validation_empty_subject(template_data):
    """
    Property 3: Template Field Validation - Empty Subject
    
    For any template submission with empty subject field,
    the system should reject the template and return a validation error.
    
    **Validates: Requirements 1.5**
    """
    with mock_template_model():
        event = {
            'body': json.dumps(template_data)
        }
        
        response = lambda_handler(event, None)
        
        # Should return 400 validation error
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'Validation Error'
        assert 'Subject' in body['message']


@settings(max_examples=100)
@given(template_data=template_with_empty_field('course'))
def test_property_template_field_validation_empty_course(template_data):
    """
    Property 3: Template Field Validation - Empty Course
    
    For any template submission with empty course field,
    the system should reject the template and return a validation error.
    
    **Validates: Requirements 1.5**
    """
    with mock_template_model():
        event = {
            'body': json.dumps(template_data)
        }
        
        response = lambda_handler(event, None)
        
        # Should return 400 validation error
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'Validation Error'
        assert 'Course' in body['message']
