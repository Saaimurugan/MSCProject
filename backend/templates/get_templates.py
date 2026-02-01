import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.db_models import Template
from shared.auth_utils import require_auth

@require_auth()
def lambda_handler(event, context):
    try:
        # Get query parameters
        query_params = event.get('queryStringParameters') or {}
        subject = query_params.get('subject')
        course = query_params.get('course')
        
        template_model = Template()
        
        if subject and course:
            # Get templates for specific subject and course
            templates = template_model.get_templates_by_subject_course(subject, course)
        else:
            # Get all templates (for admin/tutor dashboard)
            response = template_model.table.scan(
                FilterExpression='is_active = :active',
                ExpressionAttributeValues={':active': True}
            )
            templates = response.get('Items', [])
        
        # Remove sensitive data and format response
        formatted_templates = []
        for template in templates:
            formatted_template = {
                'template_id': template['template_id'],
                'title': template['title'],
                'subject': template['subject'],
                'course': template['course'],
                'question_count': len(template.get('questions', [])),
                'created_at': template['created_at']
            }
            formatted_templates.append(formatted_template)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'templates': formatted_templates})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }