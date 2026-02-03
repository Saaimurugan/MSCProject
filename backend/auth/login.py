import json
import boto3
import jwt
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional
import uuid

import json
import boto3
import jwt
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional
import uuid

# JWT Configuration
JWT_SECRET = 'your-jwt-secret-key-change-in-production'  # Should come from environment
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# DynamoDB setup
dynamodb = boto3.resource('dynamodb')

def generate_jwt_token(user_data: Dict) -> str:
    """Generate JWT token for authenticated user"""
    payload = {
        'user_id': user_data['user_id'],
        'email': user_data['email'],
        'role': user_data['role'],
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def hash_password(password: str) -> str:
    """Hash password using SHA256 (simplified for demo)"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == hashed

def get_user_by_email(email: str) -> Optional[Dict]:
    """Get user by email from DynamoDB"""
    try:
        table_name = 'msc-evaluate-users-dev'  # Should come from environment
        table = dynamodb.Table(table_name)
        
        response = table.scan(
            FilterExpression='email = :email',
            ExpressionAttributeValues={':email': email}
        )
        items = response.get('Items', [])
        return items[0] if items else None
    except Exception as e:
        print(f"Error getting user: {e}")
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
        body = json.loads(event['body'])
        email = body.get('email')
        password = body.get('password')
        
        if not email or not password:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Email and password are required'})
            }
        
        user = get_user_by_email(email)
        
        if not user or not user.get('is_active', True):
            return {
                'statusCode': 401,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Invalid credentials'})
            }
        
        # Verify password
        stored_password_hash = user.get('password_hash', '')
        if not stored_password_hash:
            # For demo purposes, if no hash exists, create one from plain password
            # In production, this should never happen
            if user.get('password') == password:
                # Create hash for future use
                user['password_hash'] = hash_password(password)
            else:
                return {
                    'statusCode': 401,
                    'headers': get_cors_headers(),
                    'body': json.dumps({'error': 'Invalid credentials'})
                }
        elif not verify_password(password, stored_password_hash):
            return {
                'statusCode': 401,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Invalid credentials'})
            }
        
        # Generate JWT token
        token = generate_jwt_token(user)
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'token': token,
                'user': {
                    'user_id': user['user_id'],
                    'email': user['email'],
                    'name': user['name'],
                    'role': user.get('role', 'student')
                }
            })
        }
        
    except Exception as e:
        print(f"Login error: {e}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Internal server error'})
        }