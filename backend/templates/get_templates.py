import json
import boto3
import hashlib
import hmac
import base64
from datetime import datetime
from typing import Dict, Optional

# JWT Configuration
JWT_SECRET = 'your-jwt-secret-key-change-in-production'
JWT_ALGORITHM = "HS256"

# DynamoDB setup
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
    # Log the entire event for debugging
    print(f"Event keys: {event.keys()}")
    print(f"Event: {json.dumps(event, default=str)}")
    
    headers = event.get('headers', {})
    
    # Try different header case variations
    auth_header = (headers.get('Authorization') or 
                   headers.get('authorization') or 
                   headers.get('AUTHORIZATION'))
    
    print(f"Headers received: {headers}")
    print(f"Auth header: {auth_header}")
    
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header[7:]  # Remove 'Bearer ' prefix
    
    # Also check in requestContext.authorizer if using API Gateway authorizer
    request_context = event.get('requestContext', {})
    authorizer = request_context.get('authorizer', {})
    if authorizer.get('token'):
        return authorizer.get('token')
    
    # Check query string parameters as fallback
    query_params = event.get('queryStringParameters', {})
    if query_params and query_params.get('token'):
        return query_params.get('token')
    
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
        # Debug logging - log the entire event
        print(f"Full event: {json.dumps(event)}")
        
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