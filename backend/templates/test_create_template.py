import json
import sys
import os
import pytest
from unittest.mock import Mock, patch, MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from create_template import lambda_handler

@pytest.fixture
def mock_template_model():
    with patch('create_template.Template') as mock:
        instance = MagicMock()
        mock.return_value = instance
        instance.create_template.return_value = {
            'template_id': 'test-template-id-123',
            'title': 'Test Template',
            'subject': 'Math',
            'course': 'Algebra',
            'questions': [],
            'is_active': True,
            'created_at': '2024-01-01T00:00:00',
            'updated_at': '2024-01-01T00:00:00'
        }
        yield instance

def test_create_template_success(mock_template_model):
    """Test successful template creation"""
    event = {
        'body': json.dumps({
            'title': 'Test Template',
            'subject': 'Math',
            'course': 'Algebra',
            'questions': [
                {
                    'question_text': 'What is 2+2?',
                    'options': ['3', '4', '5'],
                    'correct_answer': 1
                }
            ]
        })
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 201
    body = json.loads(response['body'])
    assert body['template_id'] == 'test-template-id-123'
    assert body['message'] == 'Template created successfully'

def test_empty_title_validation(mock_template_model):
    """Test validation for empty title"""
    event = {
        'body': json.dumps({
            'title': '   ',
            'subject': 'Math',
            'course': 'Algebra',
            'questions': [
                {
                    'question_text': 'What is 2+2?',
                    'options': ['3', '4'],
                    'correct_answer': 1
                }
            ]
        })
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert body['error'] == 'Validation Error'
    assert 'Title' in body['message']

def test_empty_subject_validation(mock_template_model):
    """Test validation for empty subject"""
    event = {
        'body': json.dumps({
            'title': 'Test',
            'subject': '',
            'course': 'Algebra',
            'questions': [
                {
                    'question_text': 'What is 2+2?',
                    'options': ['3', '4'],
                    'correct_answer': 1
                }
            ]
        })
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert body['error'] == 'Validation Error'
    assert 'Subject' in body['message']

def test_empty_course_validation(mock_template_model):
    """Test validation for empty course"""
    event = {
        'body': json.dumps({
            'title': 'Test',
            'subject': 'Math',
            'course': '',
            'questions': [
                {
                    'question_text': 'What is 2+2?',
                    'options': ['3', '4'],
                    'correct_answer': 1
                }
            ]
        })
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert body['error'] == 'Validation Error'
    assert 'Course' in body['message']

def test_question_min_options_validation(mock_template_model):
    """Test validation for minimum 2 options per question"""
    event = {
        'body': json.dumps({
            'title': 'Test',
            'subject': 'Math',
            'course': 'Algebra',
            'questions': [
                {
                    'question_text': 'What is 2+2?',
                    'options': ['4'],
                    'correct_answer': 0
                }
            ]
        })
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert body['error'] == 'Validation Error'
    assert 'at least 2 answer options' in body['message']

def test_question_correct_answer_required(mock_template_model):
    """Test validation for correct answer required"""
    event = {
        'body': json.dumps({
            'title': 'Test',
            'subject': 'Math',
            'course': 'Algebra',
            'questions': [
                {
                    'question_text': 'What is 2+2?',
                    'options': ['3', '4']
                }
            ]
        })
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert body['error'] == 'Validation Error'
    assert 'correct answer designated' in body['message']

def test_invalid_json(mock_template_model):
    """Test handling of invalid JSON"""
    event = {
        'body': 'invalid json {'
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert body['error'] == 'Invalid JSON'

def test_database_error_handling(mock_template_model):
    """Test handling of database errors"""
    mock_template_model.create_template.side_effect = Exception('Database error')
    
    event = {
        'body': json.dumps({
            'title': 'Test',
            'subject': 'Math',
            'course': 'Algebra',
            'questions': [
                {
                    'question_text': 'What is 2+2?',
                    'options': ['3', '4'],
                    'correct_answer': 1
                }
            ]
        })
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert body['error'] == 'Internal Server Error'
