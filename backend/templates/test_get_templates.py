import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from get_templates import lambda_handler, get_templates


@pytest.fixture
def mock_dynamodb_table():
    """Mock DynamoDB table for testing"""
    with patch('get_templates.dynamodb') as mock_db:
        mock_table = MagicMock()
        mock_db.Table.return_value = mock_table
        yield mock_table


def test_get_templates_no_auth_required(mock_dynamodb_table):
    """Test that get_templates works without authentication"""
    # Setup mock response
    mock_dynamodb_table.scan.return_value = {
        'Items': [
            {
                'template_id': 'test-1',
                'title': 'Test Template',
                'subject': 'Math',
                'course': 'Algebra',
                'questions': [{'q': 1}, {'q': 2}],
                'is_active': True
            }
        ]
    }
    
    # Create event without authentication headers
    event = {
        'httpMethod': 'GET',
        'queryStringParameters': None
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert 'templates' in body
    assert len(body['templates']) == 1
    assert body['templates'][0]['question_count'] == 2


def test_get_templates_with_subject_filter(mock_dynamodb_table):
    """Test filtering templates by subject"""
    # Setup mock response
    mock_dynamodb_table.scan.return_value = {
        'Items': [
            {
                'template_id': 'test-1',
                'title': 'Math Template',
                'subject': 'Math',
                'course': 'Algebra',
                'questions': [{'q': 1}],
                'is_active': True
            }
        ]
    }
    
    event = {
        'httpMethod': 'GET',
        'queryStringParameters': {
            'subject': 'Math'
        }
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert len(body['templates']) == 1
    assert body['templates'][0]['subject'] == 'Math'
    
    # Verify scan was called with subject filter
    mock_dynamodb_table.scan.assert_called_once()
    call_args = mock_dynamodb_table.scan.call_args
    assert ':subject' in call_args[1]['ExpressionAttributeValues']
    assert call_args[1]['ExpressionAttributeValues'][':subject'] == 'Math'


def test_get_templates_with_course_filter(mock_dynamodb_table):
    """Test filtering templates by course"""
    # Setup mock response
    mock_dynamodb_table.scan.return_value = {
        'Items': [
            {
                'template_id': 'test-1',
                'title': 'Algebra Template',
                'subject': 'Math',
                'course': 'Algebra',
                'questions': [{'q': 1}, {'q': 2}, {'q': 3}],
                'is_active': True
            }
        ]
    }
    
    event = {
        'httpMethod': 'GET',
        'queryStringParameters': {
            'course': 'Algebra'
        }
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert len(body['templates']) == 1
    assert body['templates'][0]['course'] == 'Algebra'
    
    # Verify scan was called with course filter
    mock_dynamodb_table.scan.assert_called_once()
    call_args = mock_dynamodb_table.scan.call_args
    assert ':course' in call_args[1]['ExpressionAttributeValues']
    assert call_args[1]['ExpressionAttributeValues'][':course'] == 'Algebra'


def test_get_templates_with_both_filters(mock_dynamodb_table):
    """Test filtering templates by both subject and course"""
    # Setup mock response
    mock_dynamodb_table.scan.return_value = {
        'Items': [
            {
                'template_id': 'test-1',
                'title': 'Algebra Template',
                'subject': 'Math',
                'course': 'Algebra',
                'questions': [{'q': 1}],
                'is_active': True
            }
        ]
    }
    
    event = {
        'httpMethod': 'GET',
        'queryStringParameters': {
            'subject': 'Math',
            'course': 'Algebra'
        }
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert len(body['templates']) == 1
    
    # Verify scan was called with both filters
    mock_dynamodb_table.scan.assert_called_once()
    call_args = mock_dynamodb_table.scan.call_args
    assert ':subject' in call_args[1]['ExpressionAttributeValues']
    assert ':course' in call_args[1]['ExpressionAttributeValues']


def test_get_templates_includes_question_count(mock_dynamodb_table):
    """Test that response includes question_count for each template"""
    # Setup mock response with varying question counts
    mock_dynamodb_table.scan.return_value = {
        'Items': [
            {
                'template_id': 'test-1',
                'title': 'Template 1',
                'subject': 'Math',
                'course': 'Algebra',
                'questions': [{'q': 1}, {'q': 2}, {'q': 3}],
                'is_active': True
            },
            {
                'template_id': 'test-2',
                'title': 'Template 2',
                'subject': 'Science',
                'course': 'Physics',
                'questions': [{'q': 1}],
                'is_active': True
            }
        ]
    }
    
    event = {
        'httpMethod': 'GET',
        'queryStringParameters': None
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert len(body['templates']) == 2
    assert body['templates'][0]['question_count'] == 3
    assert body['templates'][1]['question_count'] == 1


def test_get_templates_empty_result(mock_dynamodb_table):
    """Test handling of empty template list"""
    # Setup mock response with no items
    mock_dynamodb_table.scan.return_value = {
        'Items': []
    }
    
    event = {
        'httpMethod': 'GET',
        'queryStringParameters': None
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['templates'] == []
    assert body['count'] == 0


def test_get_templates_cors_preflight(mock_dynamodb_table):
    """Test CORS preflight OPTIONS request"""
    event = {
        'httpMethod': 'OPTIONS'
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    assert 'Access-Control-Allow-Origin' in response['headers']
    assert response['headers']['Access-Control-Allow-Origin'] == '*'


def test_get_templates_database_error(mock_dynamodb_table):
    """Test handling of database errors - returns empty list gracefully"""
    # Setup mock to raise exception
    mock_dynamodb_table.scan.side_effect = Exception('Database connection error')
    
    event = {
        'httpMethod': 'GET',
        'queryStringParameters': None
    }
    
    response = lambda_handler(event, None)
    
    # The get_templates function catches exceptions and returns empty list
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['templates'] == []
    assert body['count'] == 0


def test_get_templates_no_questions_field(mock_dynamodb_table):
    """Test handling of templates without questions field"""
    # Setup mock response with template missing questions
    mock_dynamodb_table.scan.return_value = {
        'Items': [
            {
                'template_id': 'test-1',
                'title': 'Template Without Questions',
                'subject': 'Math',
                'course': 'Algebra',
                'is_active': True
            }
        ]
    }
    
    event = {
        'httpMethod': 'GET',
        'queryStringParameters': None
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['templates'][0]['question_count'] == 0
