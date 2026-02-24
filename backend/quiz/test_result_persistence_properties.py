"""
Property-based tests for quiz result persistence using Hypothesis.
Feature: simplify-quiz-app
"""
import json
import sys
import os
from unittest.mock import patch, MagicMock
from datetime import datetime
import uuid

import pytest
from hypothesis import given, strategies as st, settings

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


def results_are_equivalent(original_submission, retrieved_result):
    """
    Check if a retrieved result is equivalent to the original submission.
    The retrieved result should have all the original fields plus:
    - A unique result_id
    - completed_at timestamp
    - created_at and updated_at timestamps
    """
    # Check that all original fields are preserved
    assert retrieved_result['template_id'] == original_submission['template_id'], \
        f"Template ID mismatch: expected '{original_submission['template_id']}', got '{retrieved_result['template_id']}'"
    
    assert retrieved_result['session_id'] == original_submission['session_id'], \
        f"Session ID mismatch: expected '{original_submission['session_id']}', got '{retrieved_result['session_id']}'"
    
    assert retrieved_result['answers'] == original_submission['answers'], \
        f"Answers mismatch: expected {original_submission['answers']}, got {retrieved_result['answers']}"
    
    assert retrieved_result['total_score'] == original_submission['total_score'], \
        f"Total score mismatch: expected {original_submission['total_score']}, got {retrieved_result['total_score']}"
    
    assert retrieved_result['correct_count'] == original_submission['correct_count'], \
        f"Correct count mismatch: expected {original_submission['correct_count']}, got {retrieved_result['correct_count']}"
    
    assert retrieved_result['total_questions'] == original_submission['total_questions'], \
        f"Total questions mismatch: expected {original_submission['total_questions']}, got {retrieved_result['total_questions']}"
    
    # Check that required fields are present
    assert 'result_id' in retrieved_result, "Retrieved result must have result_id"
    assert 'completed_at' in retrieved_result, "Retrieved result must have completed_at"
    
    # Verify result_id is a valid UUID
    try:
        uuid.UUID(retrieved_result['result_id'])
    except (ValueError, TypeError):
        pytest.fail(f"result_id must be a valid UUID, got: {retrieved_result['result_id']}")
    
    return True


# Property 11: Quiz Result Persistence Round-Trip
# **Validates: Requirements 4.4, 5.4**

@settings(max_examples=100)
@given(template=valid_template_with_questions())
def test_property_11_quiz_result_persistence_roundtrip(template):
    """
    Property 11: Quiz Result Persistence Round-Trip
    
    For any quiz result, saving it to the database then retrieving it 
    should produce an equivalent result with a unique result_id and completed_at timestamp.
    
    **Validates: Requirements 4.4, 5.4**
    """
    # Generate valid answers for this template
    answers = []
    correct_count = 0
    
    for idx, question in enumerate(template['questions']):
        num_options = len(question['options'])
        # Alternate between correct and incorrect answers for variety
        if idx % 2 == 0:
            selected_answer = question['correct_answer']
            correct_count += 1
        else:
            # Select a different answer (wrong if possible)
            wrong_options = [i for i in range(num_options) if i != question['correct_answer']]
            selected_answer = wrong_options[0] if wrong_options else question['correct_answer']
            if selected_answer == question['correct_answer']:
                correct_count += 1
        
        answers.append({
            'question_index': idx,
            'selected_answer': selected_answer
        })
    
    # Storage for the saved result (simulating database)
    saved_result = {}
    
    def mock_put_item(Item):
        """Simulate saving to database"""
        saved_result.update(Item)
        return None
    
    def mock_get_item(Key):
        """Simulate retrieving from database"""
        if saved_result.get('result_id') == Key.get('result_id'):
            return {'Item': saved_result}
        return {}
    
    with patch('submit_quiz.dynamodb') as mock_db:
        mock_table = MagicMock()
        mock_db.Table.return_value = mock_table
        mock_table.get_item.side_effect = lambda Key: {'Item': template} if Key.get('template_id') == template['template_id'] else {}
        mock_table.put_item.side_effect = mock_put_item
        
        # Generate a session_id
        session_id = str(uuid.uuid4())
        
        event = {
            'httpMethod': 'POST',
            'body': json.dumps({
                'template_id': template['template_id'],
                'session_id': session_id,
                'answers': answers
            })
        }
        
        # Step 1: Submit the quiz (which saves the result)
        response = lambda_handler(event, None)
        
        # Should return 200 success
        assert response['statusCode'] == 200, \
            f"Expected 200 status code, got {response['statusCode']}"
        
        body = json.loads(response['body'])
        
        # Property assertion: Response must have a unique result_id
        assert 'result_id' in body, "Response must have result_id"
        result_id = body['result_id']
        
        # Property assertion: result_id must be a valid UUID
        try:
            uuid.UUID(result_id)
        except (ValueError, TypeError):
            pytest.fail(f"result_id must be a valid UUID, got: {result_id}")
        
        # Property assertion: Saved result must exist
        assert saved_result, "Result should be saved to database"
        
        # Property assertion: Saved result must have result_id
        assert 'result_id' in saved_result, "Saved result must have result_id"
        assert saved_result['result_id'] == result_id, \
            f"Saved result_id {saved_result['result_id']} must match returned result_id {result_id}"
        
        # Step 2: Simulate retrieving the result from database
        mock_table.get_item.side_effect = mock_get_item
        retrieved_response = mock_table.get_item(Key={'result_id': result_id})
        retrieved_result = retrieved_response.get('Item')
        
        # Property assertion: Retrieved result must not be None
        assert retrieved_result is not None, \
            f"Result with id {result_id} should be retrievable after creation"
        
        # Calculate expected values
        total_questions = len(template['questions'])
        total_score = (correct_count / total_questions * 100) if total_questions > 0 else 0
        
        # Build original submission data for comparison
        original_submission = {
            'template_id': template['template_id'],
            'session_id': session_id,
            'answers': answers,
            'total_score': total_score,
            'correct_count': correct_count,
            'total_questions': total_questions
        }
        
        # Property assertion: Retrieved result must be equivalent to original
        assert results_are_equivalent(original_submission, retrieved_result), \
            "Retrieved result must be equivalent to the original submission"
        
        # Property assertion: result_id must be preserved
        assert retrieved_result['result_id'] == result_id, \
            "Retrieved result must have the same result_id"


# Property 13: Quiz Result Timestamp Presence
# **Validates: Requirements 5.4**

@settings(max_examples=100)
@given(template=valid_template_with_questions())
def test_property_13_quiz_result_timestamp_presence(template):
    """
    Property 13: Quiz Result Timestamp Presence
    
    For any quiz result stored in the database, it should have a completed_at 
    timestamp field with a valid ISO format timestamp.
    
    **Validates: Requirements 5.4**
    """
    # Generate valid answers for this template
    answers = []
    
    for idx, question in enumerate(template['questions']):
        num_options = len(question['options'])
        selected_answer = idx % num_options  # Just pick any answer
        
        answers.append({
            'question_index': idx,
            'selected_answer': selected_answer
        })
    
    # Storage for the saved result
    saved_result = {}
    
    def mock_put_item(Item):
        """Simulate saving to database"""
        saved_result.update(Item)
        return None
    
    with patch('submit_quiz.dynamodb') as mock_db:
        mock_table = MagicMock()
        mock_db.Table.return_value = mock_table
        mock_table.get_item.return_value = {'Item': template}
        mock_table.put_item.side_effect = mock_put_item
        
        event = {
            'httpMethod': 'POST',
            'body': json.dumps({
                'template_id': template['template_id'],
                'answers': answers
            })
        }
        
        # Submit the quiz (which saves the result)
        response = lambda_handler(event, None)
        
        # Should return 200 success
        assert response['statusCode'] == 200, \
            f"Expected 200 status code, got {response['statusCode']}"
        
        # Property assertion: Saved result must exist
        assert saved_result, "Result should be saved to database"
        
        # Property assertion: Saved result must have completed_at timestamp
        assert 'completed_at' in saved_result, \
            "Saved result must have completed_at timestamp"
        
        completed_at = saved_result['completed_at']
        
        # Property assertion: completed_at must be a valid ISO format timestamp
        try:
            parsed_timestamp = datetime.fromisoformat(completed_at)
            assert isinstance(parsed_timestamp, datetime), \
                f"completed_at must be a valid datetime, got: {type(parsed_timestamp)}"
        except (ValueError, TypeError) as e:
            pytest.fail(f"completed_at must be a valid ISO format timestamp, got: {completed_at}, error: {e}")
        
        # Additional check: timestamp should be recent (within last minute)
        now = datetime.utcnow()
        time_diff = abs((now - parsed_timestamp).total_seconds())
        assert time_diff < 60, \
            f"completed_at timestamp should be recent, but differs by {time_diff} seconds"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
