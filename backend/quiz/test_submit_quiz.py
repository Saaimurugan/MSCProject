import json
import sys
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from submit_quiz import lambda_handler, get_template, save_quiz_result

@pytest.fixture
def mock_dynamodb():
    with patch('submit_quiz.dynamodb') as mock:
        yield mock

@pytest.fixture
def sample_template():
    return {
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
            },
            {
                'question_text': 'What is 5-2?',
                'options': ['2', '3', '4'],
                'correct_answer': 1
            }
        ]
    }

def test_successful_quiz_submission_without_auth(mock_dynamodb, sample_template):
    """Test successful quiz submission without authentication"""
    # Mock DynamoDB responses
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    
    # Mock get_item for template retrieval
    mock_table.get_item.return_value = {'Item': sample_template}
    
    # Mock put_item for result storage
    mock_table.put_item.return_value = {}
    
    event = {
        'httpMethod': 'POST',
        'body': json.dumps({
            'template_id': 'test-template-123',
            'answers': [
                {'question_index': 0, 'selected_answer': 1},
                {'question_index': 1, 'selected_answer': 1},
                {'question_index': 2, 'selected_answer': 1}
            ]
        })
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    # Verify response structure
    assert 'result_id' in body
    assert 'session_id' in body
    assert body['total_score'] == 100.0
    assert body['correct_count'] == 3
    assert body['total_questions'] == 3
    assert len(body['detailed_results']) == 3
    
    # Verify no user_id in response
    assert 'user_id' not in body

def test_session_id_generation(mock_dynamodb, sample_template):
    """Test that session_id is generated if not provided"""
    # Mock DynamoDB responses
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    mock_table.get_item.return_value = {'Item': sample_template}
    mock_table.put_item.return_value = {}
    
    event = {
        'httpMethod': 'POST',
        'body': json.dumps({
            'template_id': 'test-template-123',
            'answers': [
                {'question_index': 0, 'selected_answer': 1},
                {'question_index': 1, 'selected_answer': 1},
                {'question_index': 2, 'selected_answer': 1}
            ]
        })
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    # Verify session_id is present and is a valid UUID format
    assert 'session_id' in body
    assert len(body['session_id']) == 36  # UUID format length

def test_session_id_preserved_when_provided(mock_dynamodb, sample_template):
    """Test that provided session_id is preserved"""
    # Mock DynamoDB responses
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    mock_table.get_item.return_value = {'Item': sample_template}
    mock_table.put_item.return_value = {}
    
    provided_session_id = 'my-custom-session-123'
    
    event = {
        'httpMethod': 'POST',
        'body': json.dumps({
            'template_id': 'test-template-123',
            'session_id': provided_session_id,
            'answers': [
                {'question_index': 0, 'selected_answer': 1},
                {'question_index': 1, 'selected_answer': 1},
                {'question_index': 2, 'selected_answer': 1}
            ]
        })
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    # Verify the provided session_id is used
    assert body['session_id'] == provided_session_id

def test_validate_all_questions_answered(mock_dynamodb, sample_template):
    """Test validation that all questions must be answered"""
    # Mock DynamoDB responses
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    mock_table.get_item.return_value = {'Item': sample_template}
    
    event = {
        'httpMethod': 'POST',
        'body': json.dumps({
            'template_id': 'test-template-123',
            'answers': [
                {'question_index': 0, 'selected_answer': 1},
                {'question_index': 1, 'selected_answer': 1}
                # Missing question_index 2
            ]
        })
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert body['error'] == 'All questions must be answered'
    assert body['expected_questions'] == 3
    assert body['answered_questions'] == 2

def test_score_calculation_percentage(mock_dynamodb, sample_template):
    """Test correct score calculation as percentage"""
    # Mock DynamoDB responses
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    mock_table.get_item.return_value = {'Item': sample_template}
    mock_table.put_item.return_value = {}
    
    event = {
        'httpMethod': 'POST',
        'body': json.dumps({
            'template_id': 'test-template-123',
            'answers': [
                {'question_index': 0, 'selected_answer': 1},  # Correct
                {'question_index': 1, 'selected_answer': 0},  # Incorrect
                {'question_index': 2, 'selected_answer': 1}   # Correct
            ]
        })
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    # 2 out of 3 correct = 66.67%
    assert body['correct_count'] == 2
    assert body['total_questions'] == 3
    assert abs(body['total_score'] - 66.666666) < 0.01

def test_detailed_results_correctness(mock_dynamodb, sample_template):
    """Test detailed results include correctness per question"""
    # Mock DynamoDB responses
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    mock_table.get_item.return_value = {'Item': sample_template}
    mock_table.put_item.return_value = {}
    
    event = {
        'httpMethod': 'POST',
        'body': json.dumps({
            'template_id': 'test-template-123',
            'answers': [
                {'question_index': 0, 'selected_answer': 1},  # Correct
                {'question_index': 1, 'selected_answer': 0},  # Incorrect
                {'question_index': 2, 'selected_answer': 2}   # Incorrect
            ]
        })
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    detailed_results = body['detailed_results']
    assert len(detailed_results) == 3
    
    # Check first question (correct)
    assert detailed_results[0]['question_index'] == 0
    assert detailed_results[0]['is_correct'] == True
    assert detailed_results[0]['selected_answer'] == 1
    assert detailed_results[0]['correct_answer'] == 1
    
    # Check second question (incorrect)
    assert detailed_results[1]['question_index'] == 1
    assert detailed_results[1]['is_correct'] == False
    assert detailed_results[1]['selected_answer'] == 0
    assert detailed_results[1]['correct_answer'] == 1
    
    # Check third question (incorrect)
    assert detailed_results[2]['question_index'] == 2
    assert detailed_results[2]['is_correct'] == False
    assert detailed_results[2]['selected_answer'] == 2
    assert detailed_results[2]['correct_answer'] == 1

def test_result_includes_completed_at_timestamp(mock_dynamodb, sample_template):
    """Test that result includes completed_at timestamp"""
    # Mock DynamoDB responses
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    mock_table.get_item.return_value = {'Item': sample_template}
    
    # Capture the put_item call
    captured_item = None
    def capture_put_item(Item):
        nonlocal captured_item
        captured_item = Item
        return {}
    
    mock_table.put_item.side_effect = capture_put_item
    
    event = {
        'httpMethod': 'POST',
        'body': json.dumps({
            'template_id': 'test-template-123',
            'answers': [
                {'question_index': 0, 'selected_answer': 1},
                {'question_index': 1, 'selected_answer': 1},
                {'question_index': 2, 'selected_answer': 1}
            ]
        })
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    
    # Verify the saved item has completed_at timestamp
    assert captured_item is not None
    assert 'completed_at' in captured_item
    assert 'created_at' in captured_item
    assert 'updated_at' in captured_item
    
    # Verify timestamp format (ISO format)
    datetime.fromisoformat(captured_item['completed_at'])

def test_result_stored_with_session_id(mock_dynamodb, sample_template):
    """Test that result is stored with session_id instead of user_id"""
    # Mock DynamoDB responses
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    mock_table.get_item.return_value = {'Item': sample_template}
    
    # Capture the put_item call
    captured_item = None
    def capture_put_item(Item):
        nonlocal captured_item
        captured_item = Item
        return {}
    
    mock_table.put_item.side_effect = capture_put_item
    
    event = {
        'httpMethod': 'POST',
        'body': json.dumps({
            'template_id': 'test-template-123',
            'session_id': 'test-session-456',
            'answers': [
                {'question_index': 0, 'selected_answer': 1},
                {'question_index': 1, 'selected_answer': 1},
                {'question_index': 2, 'selected_answer': 1}
            ]
        })
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    
    # Verify the saved item has session_id and NOT user_id
    assert captured_item is not None
    assert 'session_id' in captured_item
    assert captured_item['session_id'] == 'test-session-456'
    assert 'user_id' not in captured_item

def test_missing_template_id(mock_dynamodb):
    """Test error when template_id is missing"""
    event = {
        'httpMethod': 'POST',
        'body': json.dumps({
            'answers': [
                {'question_index': 0, 'selected_answer': 1}
            ]
        })
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert body['error'] == 'Template ID is required'

def test_missing_answers(mock_dynamodb):
    """Test error when answers are missing"""
    event = {
        'httpMethod': 'POST',
        'body': json.dumps({
            'template_id': 'test-template-123'
        })
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert body['error'] == 'Answers are required'

def test_template_not_found(mock_dynamodb):
    """Test error when template is not found"""
    # Mock DynamoDB to return no item
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    mock_table.get_item.return_value = {}
    
    event = {
        'httpMethod': 'POST',
        'body': json.dumps({
            'template_id': 'non-existent-template',
            'answers': [
                {'question_index': 0, 'selected_answer': 1}
            ]
        })
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 404
    body = json.loads(response['body'])
    assert body['error'] == 'Template not found'

def test_invalid_question_index(mock_dynamodb, sample_template):
    """Test error when question_index is invalid"""
    # Mock DynamoDB responses
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    mock_table.get_item.return_value = {'Item': sample_template}
    
    # Provide all required question indices but one is out of range
    event = {
        'httpMethod': 'POST',
        'body': json.dumps({
            'template_id': 'test-template-123',
            'answers': [
                {'question_index': 0, 'selected_answer': 1},
                {'question_index': 1, 'selected_answer': 1},
                {'question_index': 2, 'selected_answer': 1},
                {'question_index': 5, 'selected_answer': 1}  # Invalid index (extra answer)
            ]
        })
    }
    
    response = lambda_handler(event, None)
    
    # This will fail the "all questions answered" check because we have 4 answers for 3 questions
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert body['error'] == 'All questions must be answered'

def test_negative_question_index(mock_dynamodb, sample_template):
    """Test error when question_index is negative"""
    # Mock DynamoDB responses
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    mock_table.get_item.return_value = {'Item': sample_template}
    
    # Use negative index - this will fail the "all questions answered" check
    # because -1 is not in the expected set {0, 1, 2}
    event = {
        'httpMethod': 'POST',
        'body': json.dumps({
            'template_id': 'test-template-123',
            'answers': [
                {'question_index': -1, 'selected_answer': 1},  # Negative index
                {'question_index': 1, 'selected_answer': 1},
                {'question_index': 2, 'selected_answer': 1}
            ]
        })
    }
    
    response = lambda_handler(event, None)
    
    # The validation catches this as "not all questions answered" first
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert body['error'] == 'All questions must be answered'

def test_cors_preflight_request(mock_dynamodb):
    """Test CORS preflight OPTIONS request"""
    event = {
        'httpMethod': 'OPTIONS'
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    assert 'Access-Control-Allow-Origin' in response['headers']
    assert response['body'] == ''

def test_invalid_json_body(mock_dynamodb):
    """Test error handling for invalid JSON"""
    event = {
        'httpMethod': 'POST',
        'body': 'invalid json {'
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert body['error'] == 'Invalid JSON in request body'

def test_zero_score_when_all_wrong(mock_dynamodb, sample_template):
    """Test score is 0% when all answers are wrong"""
    # Mock DynamoDB responses
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    mock_table.get_item.return_value = {'Item': sample_template}
    mock_table.put_item.return_value = {}
    
    event = {
        'httpMethod': 'POST',
        'body': json.dumps({
            'template_id': 'test-template-123',
            'answers': [
                {'question_index': 0, 'selected_answer': 0},  # Wrong
                {'question_index': 1, 'selected_answer': 0},  # Wrong
                {'question_index': 2, 'selected_answer': 0}   # Wrong
            ]
        })
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    assert body['total_score'] == 0.0
    assert body['correct_count'] == 0
    assert body['total_questions'] == 3

# Edge case tests for task 4.6

def test_incomplete_answers_with_duplicate_indices(mock_dynamodb, sample_template):
    """Test rejection when answers have duplicate question indices"""
    # Mock DynamoDB responses
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    mock_table.get_item.return_value = {'Item': sample_template}
    
    event = {
        'httpMethod': 'POST',
        'body': json.dumps({
            'template_id': 'test-template-123',
            'answers': [
                {'question_index': 0, 'selected_answer': 1},
                {'question_index': 0, 'selected_answer': 1},  # Duplicate
                {'question_index': 1, 'selected_answer': 1}
                # Missing question_index 2
            ]
        })
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert body['error'] == 'All questions must be answered'

def test_invalid_answer_index_out_of_range(mock_dynamodb, sample_template):
    """Test error when answer index is out of range for question options"""
    # Mock DynamoDB responses
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    mock_table.get_item.return_value = {'Item': sample_template}
    
    # Note: The current implementation doesn't validate selected_answer range
    # This test documents the current behavior
    event = {
        'httpMethod': 'POST',
        'body': json.dumps({
            'template_id': 'test-template-123',
            'answers': [
                {'question_index': 0, 'selected_answer': 99},  # Out of range
                {'question_index': 1, 'selected_answer': 1},
                {'question_index': 2, 'selected_answer': 1}
            ]
        })
    }
    
    response = lambda_handler(event, None)
    
    # Current implementation allows this and just marks it as incorrect
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['detailed_results'][0]['is_correct'] == False

def test_invalid_question_index_exceeds_template_questions(mock_dynamodb, sample_template):
    """Test error when question_index exceeds number of questions in template"""
    # Mock DynamoDB responses
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    mock_table.get_item.return_value = {'Item': sample_template}
    
    event = {
        'httpMethod': 'POST',
        'body': json.dumps({
            'template_id': 'test-template-123',
            'answers': [
                {'question_index': 0, 'selected_answer': 1},
                {'question_index': 1, 'selected_answer': 1},
                {'question_index': 10, 'selected_answer': 1}  # Exceeds template questions
            ]
        })
    }
    
    response = lambda_handler(event, None)
    
    # The validation catches this as "not all questions answered" first
    # because index 10 is not in the expected set {0, 1, 2}
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert body['error'] == 'All questions must be answered'

def test_database_error_on_template_retrieval(mock_dynamodb):
    """Test error handling when database fails to retrieve template"""
    # Mock DynamoDB to raise an exception
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    mock_table.get_item.side_effect = Exception("DynamoDB connection error")
    
    event = {
        'httpMethod': 'POST',
        'body': json.dumps({
            'template_id': 'test-template-123',
            'answers': [
                {'question_index': 0, 'selected_answer': 1}
            ]
        })
    }
    
    response = lambda_handler(event, None)
    
    # When get_template fails, it returns None, which triggers 404
    assert response['statusCode'] == 404
    body = json.loads(response['body'])
    assert body['error'] == 'Template not found'

def test_database_error_on_result_save(mock_dynamodb, sample_template):
    """Test error handling when database fails to save quiz result"""
    # Mock DynamoDB responses
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    mock_table.get_item.return_value = {'Item': sample_template}
    
    # Mock put_item to raise an exception
    mock_table.put_item.side_effect = Exception("DynamoDB write error")
    
    event = {
        'httpMethod': 'POST',
        'body': json.dumps({
            'template_id': 'test-template-123',
            'answers': [
                {'question_index': 0, 'selected_answer': 1},
                {'question_index': 1, 'selected_answer': 1},
                {'question_index': 2, 'selected_answer': 1}
            ]
        })
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert body['error'] == 'Internal server error'

def test_empty_template_id_string(mock_dynamodb):
    """Test error when template_id is an empty string"""
    event = {
        'httpMethod': 'POST',
        'body': json.dumps({
            'template_id': '',
            'answers': [
                {'question_index': 0, 'selected_answer': 1}
            ]
        })
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert body['error'] == 'Template ID is required'

def test_empty_answers_list(mock_dynamodb):
    """Test error when answers list is empty"""
    event = {
        'httpMethod': 'POST',
        'body': json.dumps({
            'template_id': 'test-template-123',
            'answers': []
        })
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert body['error'] == 'Answers are required'

def test_malformed_answer_missing_fields(mock_dynamodb, sample_template):
    """Test handling of malformed answers missing required fields"""
    # Mock DynamoDB responses
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    mock_table.get_item.return_value = {'Item': sample_template}
    
    event = {
        'httpMethod': 'POST',
        'body': json.dumps({
            'template_id': 'test-template-123',
            'answers': [
                {'question_index': 0},  # Missing selected_answer
                {'selected_answer': 1},  # Missing question_index
                {'question_index': 2, 'selected_answer': 1}
            ]
        })
    }
    
    response = lambda_handler(event, None)
    
    # The validation will fail because None is not in the expected set
    assert response['statusCode'] == 400
