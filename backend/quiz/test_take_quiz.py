import json
import sys
import os
import pytest
from unittest.mock import Mock, patch, MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from take_quiz import lambda_handler, get_template_by_id

@pytest.fixture
def mock_dynamodb():
    with patch('take_quiz.dynamodb') as mock:
        yield mock

def test_successful_quiz_retrieval_without_auth(mock_dynamodb):
    """Test successful quiz retrieval without authentication"""
    # Mock DynamoDB response
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    mock_table.get_item.return_value = {
        'Item': {
            'template_id': 'test-template-123',
            'title': 'Math Quiz',
            'subject': 'Mathematics',
            'course': 'Algebra 101',
            'questions': [
                {
                    'question_text': 'What is 2+2?',
                    'options': ['3', '4', '5', '6'],
                    'correct_answer': 1
                },
                {
                    'question_text': 'What is 3*3?',
                    'options': ['6', '9', '12'],
                    'correct_answer': 1
                }
            ],
            'time_limit': 1800,
            'instructions': 'Complete all questions'
        }
    }
    
    event = {
        'httpMethod': 'GET',
        'pathParameters': {
            'templateId': 'test-template-123'
        }
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    # Verify quiz data structure
    assert 'quiz' in body
    quiz = body['quiz']
    assert quiz['template_id'] == 'test-template-123'
    assert quiz['title'] == 'Math Quiz'
    assert quiz['subject'] == 'Mathematics'
    assert quiz['course'] == 'Algebra 101'
    assert len(quiz['questions']) == 2
    
    # Verify no user data is returned
    assert 'user' not in body

def test_questions_dont_reveal_correct_answers(mock_dynamodb):
    """Test that questions don't reveal correct answers in response"""
    # Mock DynamoDB response
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    mock_table.get_item.return_value = {
        'Item': {
            'template_id': 'test-template-456',
            'title': 'Science Quiz',
            'subject': 'Science',
            'course': 'Physics',
            'questions': [
                {
                    'question_text': 'What is the speed of light?',
                    'options': ['299,792 km/s', '150,000 km/s', '500,000 km/s'],
                    'correct_answer': 0
                }
            ]
        }
    }
    
    event = {
        'httpMethod': 'GET',
        'pathParameters': {
            'templateId': 'test-template-456'
        }
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    # Verify questions are present
    questions = body['quiz']['questions']
    assert len(questions) == 1
    
    # Verify each question has question_text and options
    for question in questions:
        assert 'question_text' in question
        assert 'options' in question
        # Verify correct_answer is NOT present
        assert 'correct_answer' not in question

def test_template_not_found(mock_dynamodb):
    """Test template not found error"""
    # Mock DynamoDB response with no item
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    mock_table.get_item.return_value = {}
    
    event = {
        'httpMethod': 'GET',
        'pathParameters': {
            'templateId': 'non-existent-id'
        }
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 404
    body = json.loads(response['body'])
    assert body['error'] == 'Template not found'

def test_cors_preflight_request(mock_dynamodb):
    """Test CORS preflight OPTIONS request"""
    event = {
        'httpMethod': 'OPTIONS'
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    assert 'Access-Control-Allow-Origin' in response['headers']
    assert response['body'] == ''

def test_database_error_handling(mock_dynamodb):
    """Test handling of database errors"""
    # Mock DynamoDB to raise an exception
    # Note: get_template_by_id catches exceptions and returns None,
    # which results in a 404 response
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    mock_table.get_item.side_effect = Exception('Database connection error')
    
    event = {
        'httpMethod': 'GET',
        'pathParameters': {
            'templateId': 'test-template-123'
        }
    }
    
    response = lambda_handler(event, None)
    
    # Database errors in get_template_by_id return None, resulting in 404
    assert response['statusCode'] == 404
    body = json.loads(response['body'])
    assert body['error'] == 'Template not found'

def test_missing_path_parameters(mock_dynamodb):
    """Test handling of missing path parameters"""
    event = {
        'httpMethod': 'GET',
        'pathParameters': {}
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert body['error'] == 'Internal server error'

def test_response_includes_time_limit_and_instructions(mock_dynamodb):
    """Test that response includes time_limit and instructions"""
    # Mock DynamoDB response
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    mock_table.get_item.return_value = {
        'Item': {
            'template_id': 'test-template-789',
            'title': 'History Quiz',
            'subject': 'History',
            'course': 'World History',
            'questions': [
                {
                    'question_text': 'When did WWII end?',
                    'options': ['1943', '1944', '1945', '1946'],
                    'correct_answer': 2
                }
            ],
            'time_limit': 2400,
            'instructions': 'Read each question carefully'
        }
    }
    
    event = {
        'httpMethod': 'GET',
        'pathParameters': {
            'templateId': 'test-template-789'
        }
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    quiz = body['quiz']
    
    assert quiz['time_limit'] == 2400
    assert quiz['instructions'] == 'Read each question carefully'

def test_default_time_limit_and_instructions(mock_dynamodb):
    """Test default values for time_limit and instructions when not provided"""
    # Mock DynamoDB response without time_limit and instructions
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    mock_table.get_item.return_value = {
        'Item': {
            'template_id': 'test-template-999',
            'title': 'Quick Quiz',
            'subject': 'General',
            'course': 'Test',
            'questions': [
                {
                    'question_text': 'Sample question?',
                    'options': ['A', 'B'],
                    'correct_answer': 0
                }
            ]
        }
    }
    
    event = {
        'httpMethod': 'GET',
        'pathParameters': {
            'templateId': 'test-template-999'
        }
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    quiz = body['quiz']
    
    # Verify default values
    assert quiz['time_limit'] == 3600  # Default 1 hour
    assert quiz['instructions'] == 'Answer all questions to the best of your ability.'
