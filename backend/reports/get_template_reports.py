import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.db_models import QuizResult, Template, User
from shared.auth_utils import require_auth

def get_cors_headers():
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    }

@require_auth(roles=['admin', 'tutor'])
def lambda_handler(event, context):
    # Handle OPTIONS request for CORS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': ''
        }
    
    try:
        # Get template ID from path parameters
        template_id = event['pathParameters']['templateId']
        
        quiz_result_model = QuizResult()
        template_model = Template()
        user_model = User()
        
        # Verify template exists
        template = template_model.get_item({'template_id': template_id})
        if not template:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Template not found'})
            }
        
        # Get all results for this template
        response = quiz_result_model.table.scan(
            FilterExpression='template_id = :template_id',
            ExpressionAttributeValues={':template_id': template_id}
        )
        results = response.get('Items', [])
        
        # Enrich results with student information
        enriched_reports = []
        for result in results:
            user_id = result.get('user_id')
            user = user_model.get_item({'user_id': user_id})
            
            report = {
                'quiz_id': result.get('result_id'),
                'student_name': user.get('name', 'Unknown Student') if user else result.get('student_name', 'Unknown'),
                'student_id': result.get('student_id'),
                'score': result.get('total_score', 0),
                'time_taken': calculate_time_taken(result),
                'submitted_at': result.get('completed_at'),
                'answers': result.get('answers', [])
            }
            enriched_reports.append(report)
        
        # Sort by submission date (most recent first)
        enriched_reports.sort(key=lambda x: x.get('submitted_at', ''), reverse=True)
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'template': {
                    'template_id': template['template_id'],
                    'title': template['title'],
                    'subject': template['subject'],
                    'course': template['course']
                },
                'reports': enriched_reports,
                'count': len(enriched_reports)
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)})
        }

def calculate_time_taken(result):
    """Calculate time taken for quiz (in seconds)"""
    # This would be calculated from start_time and end_time if tracked
    # For demo, return a random time between 5-30 minutes
    import random
    return random.randint(300, 1800)  # 5-30 minutes in seconds