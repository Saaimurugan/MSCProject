"""
Property-based tests for template filtering using Hypothesis.
Feature: simplify-quiz-app
"""
import json
import sys
import os
from unittest.mock import patch, MagicMock

import pytest
from hypothesis import given, strategies as st, settings

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from get_templates import lambda_handler


# Custom strategies for generating test data
@st.composite
def template_with_metadata(draw):
    """Generate a template with subject and course metadata."""
    num_questions = draw(st.integers(min_value=1, max_value=5))
    questions = []
    
    for _ in range(num_questions):
        num_options = draw(st.integers(min_value=2, max_value=4))
        options = [draw(st.text(min_size=1, max_size=50)) for _ in range(num_options)]
        correct_answer = draw(st.integers(min_value=0, max_value=num_options - 1))
        
        questions.append({
            'question_text': draw(st.text(min_size=1, max_size=100)),
            'options': options,
            'correct_answer': correct_answer
        })
    
    return {
        'template_id': draw(st.uuids()).hex,
        'title': draw(st.text(min_size=1, max_size=100)),
        'subject': draw(st.text(min_size=1, max_size=50)),
        'course': draw(st.text(min_size=1, max_size=50)),
        'questions': questions,
        'is_active': True,
        'created_at': '2024-01-01T00:00:00',
        'updated_at': '2024-01-01T00:00:00'
    }


@st.composite
def template_collection(draw):
    """Generate a collection of templates with various subjects and courses."""
    num_templates = draw(st.integers(min_value=5, max_value=20))
    templates = [draw(template_with_metadata()) for _ in range(num_templates)]
    return templates


def mock_dynamodb_table(templates):
    """Create a mock DynamoDB table that returns filtered templates."""
    def mock_scan(**kwargs):
        """Simulate DynamoDB scan with filtering."""
        filter_expr = kwargs.get('FilterExpression', '')
        expr_values = kwargs.get('ExpressionAttributeValues', {})
        
        # Start with all active templates
        filtered = [t for t in templates if t.get('is_active', True)]
        
        # Apply subject filter if present
        if ':subject' in expr_values:
            subject_filter = expr_values[':subject']
            filtered = [t for t in filtered if t.get('subject') == subject_filter]
        
        # Apply course filter if present
        if ':course' in expr_values:
            course_filter = expr_values[':course']
            filtered = [t for t in filtered if t.get('course') == course_filter]
        
        return {'Items': filtered}
    
    mock_table = MagicMock()
    mock_table.scan.side_effect = mock_scan
    return mock_table


# Property 5: Template Filtering Correctness
# **Validates: Requirements 2.3**

@settings(max_examples=100)
@given(
    templates=template_collection(),
    filter_by_subject=st.booleans()
)
def test_property_5_template_filtering_by_subject(templates, filter_by_subject):
    """
    Property 5: Template Filtering Correctness - Subject Filter
    
    For any subject filter applied to template retrieval,
    all returned templates should match the specified filter criteria.
    
    **Validates: Requirements 2.3**
    """
    if not templates:
        return  # Skip if no templates generated
    
    # Pick a subject from the generated templates
    subject_to_filter = templates[0]['subject'] if filter_by_subject else None
    
    with patch('get_templates.dynamodb') as mock_dynamodb:
        mock_table = mock_dynamodb_table(templates)
        mock_dynamodb.Table.return_value = mock_table
        
        # Build event with subject filter
        event = {
            'httpMethod': 'GET',
            'queryStringParameters': {'subject': subject_to_filter} if subject_to_filter else None
        }
        
        response = lambda_handler(event, None)
        
        # Should return 200
        assert response['statusCode'] == 200, \
            f"Expected status 200, got {response['statusCode']}"
        
        body = json.loads(response['body'])
        returned_templates = body.get('templates', [])
        
        # Property assertion: All returned templates must match the subject filter
        if subject_to_filter:
            for template in returned_templates:
                assert template['subject'] == subject_to_filter, \
                    f"Template {template['template_id']} has subject '{template['subject']}', " \
                    f"but filter was for '{subject_to_filter}'"
        
        # Property assertion: All matching templates should be returned
        if subject_to_filter:
            expected_templates = [t for t in templates if t['subject'] == subject_to_filter and t.get('is_active', True)]
            assert len(returned_templates) == len(expected_templates), \
                f"Expected {len(expected_templates)} templates with subject '{subject_to_filter}', " \
                f"but got {len(returned_templates)}"


@settings(max_examples=100)
@given(
    templates=template_collection(),
    filter_by_course=st.booleans()
)
def test_property_5_template_filtering_by_course(templates, filter_by_course):
    """
    Property 5: Template Filtering Correctness - Course Filter
    
    For any course filter applied to template retrieval,
    all returned templates should match the specified filter criteria.
    
    **Validates: Requirements 2.3**
    """
    if not templates:
        return  # Skip if no templates generated
    
    # Pick a course from the generated templates
    course_to_filter = templates[0]['course'] if filter_by_course else None
    
    with patch('get_templates.dynamodb') as mock_dynamodb:
        mock_table = mock_dynamodb_table(templates)
        mock_dynamodb.Table.return_value = mock_table
        
        # Build event with course filter
        event = {
            'httpMethod': 'GET',
            'queryStringParameters': {'course': course_to_filter} if course_to_filter else None
        }
        
        response = lambda_handler(event, None)
        
        # Should return 200
        assert response['statusCode'] == 200, \
            f"Expected status 200, got {response['statusCode']}"
        
        body = json.loads(response['body'])
        returned_templates = body.get('templates', [])
        
        # Property assertion: All returned templates must match the course filter
        if course_to_filter:
            for template in returned_templates:
                assert template['course'] == course_to_filter, \
                    f"Template {template['template_id']} has course '{template['course']}', " \
                    f"but filter was for '{course_to_filter}'"
        
        # Property assertion: All matching templates should be returned
        if course_to_filter:
            expected_templates = [t for t in templates if t['course'] == course_to_filter and t.get('is_active', True)]
            assert len(returned_templates) == len(expected_templates), \
                f"Expected {len(expected_templates)} templates with course '{course_to_filter}', " \
                f"but got {len(returned_templates)}"


@settings(max_examples=100)
@given(templates=template_collection())
def test_property_5_template_filtering_by_both(templates):
    """
    Property 5: Template Filtering Correctness - Subject and Course Filter
    
    For any subject and course filter applied to template retrieval,
    all returned templates should match both specified filter criteria.
    
    **Validates: Requirements 2.3**
    """
    if not templates:
        return  # Skip if no templates generated
    
    # Pick subject and course from the generated templates
    subject_to_filter = templates[0]['subject']
    course_to_filter = templates[0]['course']
    
    with patch('get_templates.dynamodb') as mock_dynamodb:
        mock_table = mock_dynamodb_table(templates)
        mock_dynamodb.Table.return_value = mock_table
        
        # Build event with both filters
        event = {
            'httpMethod': 'GET',
            'queryStringParameters': {
                'subject': subject_to_filter,
                'course': course_to_filter
            }
        }
        
        response = lambda_handler(event, None)
        
        # Should return 200
        assert response['statusCode'] == 200, \
            f"Expected status 200, got {response['statusCode']}"
        
        body = json.loads(response['body'])
        returned_templates = body.get('templates', [])
        
        # Property assertion: All returned templates must match both filters
        for template in returned_templates:
            assert template['subject'] == subject_to_filter, \
                f"Template {template['template_id']} has subject '{template['subject']}', " \
                f"but filter was for '{subject_to_filter}'"
            assert template['course'] == course_to_filter, \
                f"Template {template['template_id']} has course '{template['course']}', " \
                f"but filter was for '{course_to_filter}'"
        
        # Property assertion: All matching templates should be returned
        expected_templates = [
            t for t in templates 
            if t['subject'] == subject_to_filter 
            and t['course'] == course_to_filter 
            and t.get('is_active', True)
        ]
        assert len(returned_templates) == len(expected_templates), \
            f"Expected {len(expected_templates)} templates with subject '{subject_to_filter}' " \
            f"and course '{course_to_filter}', but got {len(returned_templates)}"


@settings(max_examples=100)
@given(templates=template_collection())
def test_property_5_template_filtering_no_filter(templates):
    """
    Property 5: Template Filtering Correctness - No Filter
    
    When no filter is applied to template retrieval,
    all active templates should be returned.
    
    **Validates: Requirements 2.3**
    """
    with patch('get_templates.dynamodb') as mock_dynamodb:
        mock_table = mock_dynamodb_table(templates)
        mock_dynamodb.Table.return_value = mock_table
        
        # Build event with no filters
        event = {
            'httpMethod': 'GET',
            'queryStringParameters': None
        }
        
        response = lambda_handler(event, None)
        
        # Should return 200
        assert response['statusCode'] == 200, \
            f"Expected status 200, got {response['statusCode']}"
        
        body = json.loads(response['body'])
        returned_templates = body.get('templates', [])
        
        # Property assertion: All active templates should be returned
        expected_templates = [t for t in templates if t.get('is_active', True)]
        assert len(returned_templates) == len(expected_templates), \
            f"Expected {len(expected_templates)} active templates, but got {len(returned_templates)}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
