import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.db_models import Template

def get_cors_headers():
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET, OPTIONS'
    }

def lambda_handler(event, context):
    try:
        # Extract template_id from path parameters
        template_id = event.get('pathParameters', {}).get('template_id')
        
        if not template_id:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Bad Request', 'message': 'template_id is required'})
            }
        
        # Retrieve template from database
        template_model = Template()
        template = template_model.get_item({'template_id': template_id})
        
        if not template:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Not Found', 'message': 'Template not found'})
            }
        
        # Check if template is active
        if not template.get('is_active', True):
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Not Found', 'message': 'Template not found'})
            }
        
        # Return template with all details
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'template_id': template['template_id'],
                'title': template['title'],
                'subject': template['subject'],
                'course': template['course'],
                'questions': template['questions'],
                'created_at': template.get('created_at'),
                'updated_at': template.get('updated_at')
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Internal Server Error', 'message': 'Unable to process request'})
        }
