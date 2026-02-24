"""
Property-based tests for quiz taking using Hypothesis.
Feature: simplify-quiz-app
"""
import json
import sys
import os
from unittest.mock import patch, MagicMock

import pytest
from hypothesis import given, strategies as st, settings

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from take_quiz import lambda_handler


# Custom strategies for generating test data
@st.composite
def valid_question_with_answer(draw):
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
def valid_template(draw):
    """Generate a valid template with questions."""
    num_questions = draw(st.integers(min_value=1, max_value=20))
    questions = [draw(valid_question_with_answer()) for _ in range(num_questions)]
    
    return {
        'template_id': draw(st.text(min_size=1, max_size=50)),
        'title': draw(st.text(min_size=1, max_size=200)),
        'subject': draw(st.text(min_size=1, max_size=100)),
        'course': draw(st.text(min_size=1, max_size=100)),
        'questions': questions,
        'time_limit': draw(st.integers(min_value=60, max_value=7200)),
        'instructions': draw(st.text(min_size=1, max_size=500))
    }


# Property 6: Question Display Concealment
# **Validates: Requirements 3.2**

@settings(max_examples=100)
@given(template=valid_template())
def test_property_question_display_concealment(template):
    """
    Property 6: Question Display Concealment
    
    For any question displayed during quiz taking, the rendered output should not
    reveal which answer option is correct.
    
    **Validates: Requirements 3.2**
    """
    with patch('take_quiz.dynamodb') as mock_db:
        mock_table = MagicMock()
        mock_db.Table.return_value = mock_table
        mock_table.get_item.return_value = {'Item': template}
        
        event = {
            'httpMethod': 'GET',
            'pathParameters': {
                'templateId': template['template_id']
            }
        }
        
        response = lambda_handler(event, None)
        
        # Should return 200 success
        assert response['statusCode'] == 200
        
        body = json.loads(response['body'])
        assert 'quiz' in body
        
        quiz = body['quiz']
        assert 'questions' in quiz
        
        # Verify that NONE of the questions contain the 'correct_answer' field
        for question in quiz['questions']:
            assert 'correct_answer' not in question, \
                f"Question should not reveal correct answer: {question}"
            
            # Verify that questions still have the necessary fields
            assert 'question_text' in question, \
                "Question must have question_text"
            assert 'options' in question, \
                "Question must have options"
            
            # Verify options are present (at least 2)
            assert len(question['options']) >= 2, \
                "Question must have at least 2 options"
