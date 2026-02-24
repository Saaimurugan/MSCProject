"""
Property-based tests for template persistence using Hypothesis.
Feature: simplify-quiz-app
"""
import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime
import uuid
import os
import sys
from unittest.mock import MagicMock, patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.db_models import Template


# Custom strategies for generating test data
@st.composite
def valid_template_data(draw):
    """Generate valid template data for testing"""
    num_questions = draw(st.integers(min_value=1, max_value=20))
    questions = []
    
    for _ in range(num_questions):
        num_options = draw(st.integers(min_value=2, max_value=6))
        options = [draw(st.text(min_size=1, max_size=100)) for _ in range(num_options)]
        correct_answer = draw(st.integers(min_value=0, max_value=num_options - 1))
        
        questions.append({
            'question_text': draw(st.text(min_size=1, max_size=200)),
            'options': options,
            'correct_answer': correct_answer
        })
    
    return {
        'title': draw(st.text(min_size=1, max_size=100)),
        'subject': draw(st.text(min_size=1, max_size=50)),
        'course': draw(st.text(min_size=1, max_size=50)),
        'questions': questions
    }


def templates_are_equivalent(original_data, retrieved_template):
    """
    Check if a retrieved template is equivalent to the original data.
    The retrieved template should have all the original fields plus:
    - A unique template_id
    - created_at and updated_at timestamps
    - is_active flag
    """
    # Check that all original fields are preserved
    assert retrieved_template['title'] == original_data['title'], \
        f"Title mismatch: expected '{original_data['title']}', got '{retrieved_template['title']}'"
    
    assert retrieved_template['subject'] == original_data['subject'], \
        f"Subject mismatch: expected '{original_data['subject']}', got '{retrieved_template['subject']}'"
    
    assert retrieved_template['course'] == original_data['course'], \
        f"Course mismatch: expected '{original_data['course']}', got '{retrieved_template['course']}'"
    
    assert len(retrieved_template['questions']) == len(original_data['questions']), \
        f"Question count mismatch: expected {len(original_data['questions'])}, got {len(retrieved_template['questions'])}"
    
    # Check each question
    for i, (orig_q, retr_q) in enumerate(zip(original_data['questions'], retrieved_template['questions'])):
        assert retr_q['question_text'] == orig_q['question_text'], \
            f"Question {i} text mismatch"
        assert retr_q['options'] == orig_q['options'], \
            f"Question {i} options mismatch"
        assert retr_q['correct_answer'] == orig_q['correct_answer'], \
            f"Question {i} correct_answer mismatch"
    
    # Check that required fields are present
    assert 'template_id' in retrieved_template, "Retrieved template must have template_id"
    assert 'created_at' in retrieved_template, "Retrieved template must have created_at"
    assert 'updated_at' in retrieved_template, "Retrieved template must have updated_at"
    assert 'is_active' in retrieved_template, "Retrieved template must have is_active"
    
    return True


# Property 2: Template Persistence Round-Trip
# **Validates: Requirements 1.4**

@settings(max_examples=100)
@given(template_data=valid_template_data())
def test_property_2_template_persistence_roundtrip(template_data):
    """
    Property 2: Template Persistence Round-Trip
    
    For any valid template, saving it to the database then retrieving it 
    should produce an equivalent template with a unique template_id assigned.
    
    **Validates: Requirements 1.4**
    """
    # Mock the DynamoDB table to simulate database operations
    with patch('shared.db_models.dynamodb') as mock_dynamodb:
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        
        # Storage for the saved template (simulating database)
        saved_template = {}
        
        def mock_put_item(Item):
            """Simulate saving to database"""
            saved_template.update(Item)
            return None
        
        def mock_get_item(Key):
            """Simulate retrieving from database"""
            if saved_template.get('template_id') == Key.get('template_id'):
                return {'Item': saved_template}
            return {}
        
        mock_table.put_item.side_effect = mock_put_item
        mock_table.get_item.side_effect = mock_get_item
        
        # Create template instance
        template_model = Template()
        
        # Step 1: Save the template
        created_template = template_model.create_template(
            title=template_data['title'],
            subject=template_data['subject'],
            course=template_data['course'],
            questions=template_data['questions']
        )
        
        # Property assertion: Created template must have a unique template_id
        assert 'template_id' in created_template, "Created template must have template_id"
        template_id = created_template['template_id']
        
        # Property assertion: template_id must be a valid UUID
        try:
            uuid.UUID(template_id)
        except (ValueError, TypeError):
            pytest.fail(f"template_id must be a valid UUID, got: {template_id}")
        
        # Step 2: Retrieve the template
        retrieved_template = template_model.get_item({'template_id': template_id})
        
        # Property assertion: Retrieved template must not be None
        assert retrieved_template is not None, \
            f"Template with id {template_id} should be retrievable after creation"
        
        # Property assertion: Retrieved template must be equivalent to original
        assert templates_are_equivalent(template_data, retrieved_template), \
            "Retrieved template must be equivalent to the original template data"
        
        # Property assertion: template_id must be preserved
        assert retrieved_template['template_id'] == template_id, \
            "Retrieved template must have the same template_id as the created template"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
