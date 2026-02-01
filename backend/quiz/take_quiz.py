import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.db_models import Template
from shared.auth_utils import require_auth

@require_auth()
def lambda_handler(event, context):
    try:
        # Get template_id from path parameters
        path_params = event.get('pathParameters') or {}
        template_id = path_params.get('template_id')
        
        if not template_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Template ID is required'})
            }
        
        template_model = Template()
        template = template_model.get_item({'template_id': template_id})
        
        if not template or not template.get('is_active'):
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Template not found'})
            }
        
        # Return template data for quiz taking
        quiz_data = {
            'template_id': template['template_id'],
            'title': template['title'],
            'subject': template['subject'],
            'course': template['course'],
            'questions': [
                {
                    'question_id': i,
                    'question': q['question']
                    # Don't include example_answer in response for security
                }
                for i, q in enumerate(template['questions'])
            ]
        }
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(quiz_data)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }