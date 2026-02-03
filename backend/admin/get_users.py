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
        
        # Check if user is admin
        if user_data.get('role') != 'admin':
            return {
                'statusCode': 403,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Insufficient permissions'})
            }
        
        # Get all users from DynamoDB
        table_name = 'msc-evaluate-users-dev'
        table = dynamodb.Table(table_name)
        
        response = table.scan()
        users = response.get('Items', [])
        
        # Remove sensitive information
        safe_users = []
        for user in users:
            safe_user = {
                'user_id': user.get('user_id'),
                'email': user.get('email'),
                'name': user.get('name'),
                'role': user.get('role'),
                'is_active': user.get('is_active'),
                'created_at': user.get('created_at')
            }
            safe_users.append(safe_user)
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'users': safe_users,
                'count': len(safe_users)
            })
        }
        
    except Exception as e:
        print(f"Get users error: {e}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Internal server error'})
        }