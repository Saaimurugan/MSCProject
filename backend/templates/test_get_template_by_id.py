import json
import sys
import os
import pytest
from unittest.mock import Mock, patch, MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from get_template_by_id import lambda_handler

@pytest.fixture
def mock_template_model():
    with patch('get_template_by_id.Template') as mock:
        instance = MagicMock()
        mock.return_value = instance
        yield instance

def test_successful_retrieval(mock_template_model):
    """Test successful template retrieval"""
    mock_template_model.get_item.return_value = {
        'template_id': 'test-template-id-123',
        'title': 'Test Template',
        'subject': 'Math',
        'course': 'Algebra',
        'questions': [
            {
                'question_text': 'What is 2+2?',
                'options': ['3', '4', '5'],
                'correct_answer': 1
            }
        ],
        'is_active': True,
        'created_at': '2024-01-01T00:00:00',
        'updated_at': '2024-01-01T00:00:00'
    }
    
    event = {
        'pathParameters': {
            'template_id': 'test-template-id-123'
        }
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['template_id'] == 'test-template-id-123'
    assert body['title'] == 'Test Template'
    assert body['subject'] == 'Math'
    assert body['course'] == 'Algebra'
    assert len(body['questions']) == 1
    assert body['questions'][0]['question_text'] == 'What is 2+2?'

def test_not_found_error(mock_template_model):
    """Test template not found error"""
    mock_template_model.get_item.return_value = None
    
    event = {
        'pathParameters': {
            'template_id': 'non-existent-id'
        }
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 404
    body = json.loads(response['body'])
    assert body['error'] == 'Not Found'
    assert body['message'] == 'Template not found'

def test_inactive_template_not_found(mock_template_model):
    """Test inactive template returns not found"""
    mock_template_model.get_item.return_value = {
        'template_id': 'test-template-id-123',
        'title': 'Test Template',
        'subject': 'Math',
        'course': 'Algebra',
        'questions': [],
        'is_active': False,
        'created_at': '2024-01-01T00:00:00',
        'updated_at': '2024-01-01T00:00:00'
    }
    
    event = {
        'pathParameters': {
            'template_id': 'test-template-id-123'
        }
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 404
    body = json.loads(response['body'])
    assert body['error'] == 'Not Found'
    assert body['message'] == 'Template not found'

def test_invalid_template_id_format(mock_template_model):
    """Test invalid template_id format (missing template_id)"""
    event = {
        'pathParameters': {}
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert body['error'] == 'Bad Request'
    assert body['message'] == 'template_id is required'

def test_missing_path_parameters(mock_template_model):
    """Test missing path parameters"""
    event = {}
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert body['error'] == 'Bad Request'
    assert body['message'] == 'template_id is required'

def test_database_error_handling(mock_template_model):
    """Test handling of database errors"""
    mock_template_model.get_item.side_effect = Exception('Database error')
    
    event = {
        'pathParameters': {
            'template_id': 'test-template-id-123'
        }
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert body['error'] == 'Internal Server Error'
    assert body['message'] == 'Unable to process request'
