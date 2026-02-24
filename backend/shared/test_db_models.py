"""
Property-based tests for database models

Feature: simplify-quiz-app
Tests Properties 12 and 14 for database model correctness
"""

import pytest
from hypothesis import given, strategies as st
from datetime import datetime
import uuid
import os
from unittest.mock import MagicMock, patch
from db_models import Template, QuizResult


# Custom strategies for generating test data
@st.composite
def valid_template_data(draw):
    """Generate valid template data for testing"""
    return {
        'title': draw(st.text(min_size=1, max_size=100)),
        'subject': draw(st.text(min_size=1, max_size=50)),
        'course': draw(st.text(min_size=1, max_size=50)),
        'questions': draw(st.lists(
            st.fixed_dictionaries({
                'question_text': st.text(min_size=1, max_size=200),
                'options': st.lists(st.text(min_size=1, max_size=100), min_size=2, max_size=6),
                'correct_answer': st.integers(min_value=0, max_value=5)
            }),
            min_size=1,
            max_size=20
        ))
    }


@st.composite
def valid_quiz_result_data(draw):
    """Generate valid quiz result data for testing"""
    num_questions = draw(st.integers(min_value=1, max_value=20))
    return {
        'template_id': str(uuid.uuid4()),
        'session_id': str(uuid.uuid4()),
        'answers': [
            {
                'question_index': i,
                'selected_answer': draw(st.integers(min_value=0, max_value=5))
            }
            for i in range(num_questions)
        ],
        'total_score': draw(st.floats(min_value=0.0, max_value=100.0)),
        'correct_count': draw(st.integers(min_value=0, max_value=num_questions)),
        'total_questions': num_questions
    }


def is_valid_iso_timestamp(timestamp_str):
    """Check if a string is a valid ISO format timestamp"""
    try:
        datetime.fromisoformat(timestamp_str)
        return True
    except (ValueError, TypeError):
        return False


def is_valid_uuid(uuid_str):
    """Check if a string is a valid UUID"""
    try:
        uuid.UUID(uuid_str)
        return True
    except (ValueError, TypeError):
        return False


# Property 12: Template Timestamp Presence
@given(valid_template_data())
def test_property_12_template_timestamp_presence(template_data):
    """
    **Validates: Requirements 5.3**
    
    Property 12: Template Timestamp Presence
    For any template stored in the database, it should have both created_at 
    and updated_at timestamp fields with valid ISO format timestamps.
    """
    # Mock the DynamoDB table to avoid actual AWS calls
    with patch('db_models.dynamodb') as mock_dynamodb:
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        
        # Create template instance
        template = Template()
        
        # Create the template
        result = template.create_template(
            title=template_data['title'],
            subject=template_data['subject'],
            course=template_data['course'],
            questions=template_data['questions']
        )
        
        # Property assertion: Template must have created_at timestamp
        assert 'created_at' in result, "Template must have created_at field"
        assert is_valid_iso_timestamp(result['created_at']), \
            f"created_at must be valid ISO timestamp, got: {result['created_at']}"
        
        # Property assertion: Template must have updated_at timestamp
        assert 'updated_at' in result, "Template must have updated_at field"
        assert is_valid_iso_timestamp(result['updated_at']), \
            f"updated_at must be valid ISO timestamp, got: {result['updated_at']}"


# Property 14: Session Identifier Presence
@given(valid_quiz_result_data())
def test_property_14_session_identifier_presence(result_data):
    """
    **Validates: Requirements 9.4**
    
    Property 14: Session Identifier Presence
    For any quiz result stored in the database, it should have a session_id 
    field containing a valid UUID.
    """
    # Mock the DynamoDB table to avoid actual AWS calls
    with patch('db_models.dynamodb') as mock_dynamodb:
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        
        # Create quiz result instance
        quiz_result = QuizResult()
        
        # Save the quiz result
        result = quiz_result.save_result(
            template_id=result_data['template_id'],
            session_id=result_data['session_id'],
            answers=result_data['answers'],
            total_score=result_data['total_score'],
            correct_count=result_data['correct_count'],
            total_questions=result_data['total_questions']
        )
        
        # Property assertion: Result must have session_id field
        assert 'session_id' in result, "Quiz result must have session_id field"
        
        # Property assertion: session_id must be a valid UUID
        assert is_valid_uuid(result['session_id']), \
            f"session_id must be a valid UUID, got: {result['session_id']}"
        
        # Property assertion: session_id must match the provided session_id
        assert result['session_id'] == result_data['session_id'], \
            "session_id in result must match the provided session_id"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
