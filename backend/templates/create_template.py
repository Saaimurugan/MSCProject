import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.db_models import Template
from shared.auth_utils import require_auth

@require_auth(roles=['admin', 'tutor'])
def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        title = body.get('title')
        subject = body.get('subject')
        course = body.get('course')
        questions = body.get('questions', [])
        
        if not title or not subject or not course or not questions:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Title, subject, course, and questions are required'})
            }
        
        # Validate questions format
        for i, question in enumerate(questions):
            if not question.get('question') or not question.get('example_answer'):
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': f'Question {i+1} must have question and example_answer'})
                }
        
        template_model = Template()
        template = template_model.create_template(
            title=title,
            subject=subject,
            course=course,
            questions=questions,
            created_by=event['user']['user_id']
        )
        
        return {
            'statusCode': 201,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'template_id': template['template_id'],
                'message': 'Template created successfully'
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }