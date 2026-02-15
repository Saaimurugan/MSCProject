import json
import boto3
import hashlib
import hmac
import base64
import uuid
from datetime import datetime
from typing import Dict, Optional

# JWT Configuration
JWT_SECRET = 'your-jwt-secret-key-change-in-production'
JWT_ALGORITHM = "HS256"

dynamodb = boto3.resource('dynamodb')

def base64url_decode(data):
    """Base64 URL decode with padding"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    # Add padding if needed
    padding = 4 - (len(data) % 4)
    if padding != 4:
        data += b'=' * padding
    return base64.urlsafe_b64decode(data)

def base64url_encode(data):
    """Base64 URL encode without padding"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    elif not isinstance(data, bytes):
        data = str(data).encode('utf-8')
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def verify_jwt_token(token: str) -> Optional[Dict]:
    """Verify and decode JWT token"""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        header_encoded, payload_encoded, signature_encoded = parts
        
        # Verify signature
        message = f"{header_encoded}.{payload_encoded}"
        expected_signature = hmac.new(
            JWT_SECRET.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        expected_signature_encoded = base64url_encode(expected_signature)
        
        if signature_encoded != expected_signature_encoded:
            return None
        
        # Decode payload
        payload_json = base64url_decode(payload_encoded)
        payload = json.loads(payload_json)
        
        # Check expiration
        if 'exp' in payload:
            if payload['exp'] < int(datetime.utcnow().timestamp()):
                return None
        
        return payload
    except Exception as e:
        print(f"JWT verification error: {e}")
        return None

def extract_token_from_event(event: Dict) -> Optional[str]:
    """Extract JWT token from Lambda event"""
    headers = event.get('headers', {})
    
    # Try different header case variations
    auth_header = (headers.get('Authorization') or 
                   headers.get('authorization') or 
                   headers.get('AUTHORIZATION'))
    
    print(f"Headers received: {headers}")  # Debug logging
    print(f"Auth header: {auth_header}")  # Debug logging
    
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header[7:]  # Remove 'Bearer ' prefix
    return None

def get_cors_headers():
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    }

def lambda_handler(event, context):
    # Handle OPTIONS request for CORS
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
        
        # Check if user has permission to create templates (admin or tutor)
        user_role = user_data.get('role', 'student')
        if user_role not in ['admin', 'tutor']:
            return {
                'statusCode': 403,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Insufficient permissions to create templates'})
            }
        
        # Handle both API Gateway and direct invocation formats
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
        
        title = body.get('title')
        subject = body.get('subject')
        course = body.get('course')
        questions = body.get('questions', [])
        
        if not title or not subject or not course or not questions:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Title, subject, course, and questions are required'})
            }
        
        # Validate questions format
        for i, question in enumerate(questions):
            if not question.get('question_text') or not question.get('sample_answer'):
                return {
                    'statusCode': 400,
                    'headers': get_cors_headers(),
                    'body': json.dumps({'error': f'Question {i+1} must have question_text and sample_answer'})
                }
        
        # Create template
        table_name = 'msc-evaluate-templates-dev'
        table = dynamodb.Table(table_name)
        
        template_id = str(uuid.uuid4())
        template = {
            'template_id': template_id,
            'title': title,
            'subject': subject,
            'course': course,
            'questions': questions,
            'question_count': len(questions),
            'created_by': user_data.get('user_id'),
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'is_active': True
        }
        
        table.put_item(Item=template)
        
        return {
            'statusCode': 201,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'template_id': template_id,
                'message': 'Template created successfully'
            })
        }
        
    except Exception as e:
        print(f"Error creating template: {e}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Internal server error'})
        }
