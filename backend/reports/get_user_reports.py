import json
import boto3
import jwt
from datetime import datetime
from typing import Dict, Optional

# JWT Configuration
JWT_SECRET = 'your-jwt-secret-key-change-in-production'
JWT_ALGORITHM = "HS256"

# DynamoDB setup
dynamodb = boto3.resource('dynamodb')

def verify_jwt_token(token: str) -> Optional[Dict]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def extract_token_from_event(event: Dict) -> Optional[str]:
    """Extract JWT token from Lambda event"""
    headers = event.get('headers', {})
    auth_header = headers.get('Authorization') or headers.get('authorization')
    
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header[7:]  # Remove 'Bearer ' prefix
    return None

def get_user_results(user_id: str) -> list:
    """Get user's quiz results from DynamoDB"""
    try:
        table_name = 'msc-evaluate-quiz-results-dev'
        table = dynamodb.Table(table_name)
        
        response = table.scan(
            FilterExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': user_id}
        )
        return response.get('Items', [])
    except Exception as e:
        print(f"Error getting user results: {e}")
        return []

def get_template_by_id(template_id: str) -> Optional[Dict]:
    """Get template by ID from DynamoDB"""
    try:
        table_name = 'msc-evaluate-templates-dev'
        table = dynamodb.Table(table_name)
        
        response = table.get_item(Key={'template_id': template_id})
        return response.get('Item')
    except Exception as e:
        print(f"Error getting template: {e}")
        return None

def calculate_time_taken(result):
    """Calculate time taken for quiz (in seconds)"""
    # This would be calculated from start_time and end_time if tracked
    # For demo, return a random time between 5-30 minutes
    import random
    return random.randint(300, 1800)  # 5-30 minutes in seconds

def get_cors_headers():
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    }

def lambda_handler(event, context):
    # Handle OPTIONS request for CORS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': ''
        }
    
    try:
        # Verify authentication
        token = extract_token_from_event(event)
        if not token:
            return {
                'statusCode': 401,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'No token provided'})
            }
        
        user_data = verify_jwt_token(token)
        if not user_data:
            return {
                'statusCode': 401,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Invalid or expired token'})
            }
        
        # Get user ID from path parameters
        user_id = event['pathParameters']['userId']
        
        # Check if user is requesting their own reports or is admin/tutor
        if (user_id != user_data['user_id'] and 
            user_data['role'] not in ['admin', 'tutor']):
            return {
                'statusCode': 403,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Access denied'})
            }
        
        # Get user's quiz results
        results = get_user_results(user_id)
        
        # Enrich results with template information
        enriched_reports = []
        for result in results:
            template_id = result.get('template_id')
            template = get_template_by_id(template_id)
            
            report = {
                'quiz_id': result.get('result_id'),
                'template_id': template_id,
                'template_title': template.get('title', 'Unknown Template') if template else 'Unknown Template',
                'subject': template.get('subject', 'Unknown') if template else 'Unknown',
                'course': template.get('course', 'Unknown') if template else 'Unknown',
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
                'reports': enriched_reports,
                'count': len(enriched_reports)
            })
        }
        
    except Exception as e:
        print(f"Get user reports error: {e}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Internal server error'})
        }