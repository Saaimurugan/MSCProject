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
        quiz_result_model = QuizResult()
        template_model = Template()
        user_model = User()
        
        # Get query parameters for filtering
        query_params = event.get('queryStringParameters') or {}
        start_date = query_params.get('startDate')
        end_date = query_params.get('endDate')
        
        # Get all quiz results
        response = quiz_result_model.table.scan()
        results = response.get('Items', [])
        
        # Filter by date range if provided
        if start_date or end_date:
            filtered_results = []
            for result in results:
                result_date = result.get('completed_at', '')
                if start_date and result_date < start_date:
                    continue
                if end_date and result_date > end_date:
                    continue
                filtered_results.append(result)
            results = filtered_results
        
        # Cache for templates and users to avoid repeated lookups
        template_cache = {}
        user_cache = {}
        
        # Enrich results with template and student information
        enriched_reports = []
        for result in results:
            template_id = result.get('template_id')
            user_id = result.get('user_id')
            
            # Get template info (with caching)
            if template_id not in template_cache:
                template = template_model.get_item({'template_id': template_id})
                template_cache[template_id] = template
            else:
                template = template_cache[template_id]
            
            # Get user info (with caching)
            if user_id not in user_cache:
                user = user_model.get_item({'user_id': user_id})
                user_cache[user_id] = user
            else:
                user = user_cache[user_id]
            
            report = {
                'quiz_id': result.get('result_id'),
                'student_name': user.get('name', 'Unknown Student') if user else result.get('student_name', 'Unknown'),
                'student_id': result.get('student_id'),
                'template_title': template.get('title', 'Unknown Template') if template else 'Unknown Template',
                'subject': template.get('subject', 'Unknown') if template else 'Unknown',
                'course': template.get('course', 'Unknown') if template else 'Unknown',
                'score': result.get('total_score', 0),
                'time_taken': calculate_time_taken(result),
                'submitted_at': result.get('completed_at')
            }
            enriched_reports.append(report)
        
        # Sort by submission date (most recent first)
        enriched_reports.sort(key=lambda x: x.get('submitted_at', ''), reverse=True)
        
        # Calculate summary statistics
        total_submissions = len(enriched_reports)
        if total_submissions > 0:
            avg_score = sum(r['score'] for r in enriched_reports) / total_submissions
            pass_count = sum(1 for r in enriched_reports if r['score'] >= 60)
            pass_rate = (pass_count / total_submissions) * 100
        else:
            avg_score = 0
            pass_rate = 0
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'reports': enriched_reports,
                'summary': {
                    'total_submissions': total_submissions,
                    'average_score': round(avg_score, 2),
                    'pass_rate': round(pass_rate, 2)
                },
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