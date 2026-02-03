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

def get_templates(subject: str = None, course: str = None) -> list:
    """Get templates from DynamoDB with optional filtering"""
    try:
        table_name = 'msc-evaluate-templates-dev'
        table = dynamodb.Table(table_name)
        
        # Build filter expression
        filter_expression = 'is_active = :active'
        expression_values = {':active': True}
        
        if subject:
            filter_expression += ' AND subject = :subject'
            expression_values[':subject'] = subject
            
        if course:
            filter_expression += ' AND course = :course'
            expression_values[':course'] = course
        
        response = table.scan(
            FilterExpression=filter_expression,
            ExpressionAttributeValues=expression_values
        )
        
        templates = response.get('Items', [])
        
        # Add question count to each template
        for template in templates:
            template['question_count'] = len(template.get('questions', []))
        
        return templates
    except Exception as e:
        print(f"Error getting templates: {e}")
        return []

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
        
        # Get query parameters
        query_params = event.get('queryStringParameters') or {}
        subject = query_params.get('subject')
        course = query_params.get('course')
        
        # Get templates
        templates = get_templates(subject, course)
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'templates': templates,
                'count': len(templates)
            })
        }
        
    except Exception as e:
        print(f"Get templates error: {e}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Internal server error'})
        }