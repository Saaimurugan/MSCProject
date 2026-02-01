import jwt
import boto3
import json
from datetime import datetime, timedelta
from typing import Dict, Optional

# JWT Configuration
import os
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-jwt-secret-key')  # Get from environment
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

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

def require_auth(roles: list = None):
    """Decorator to require authentication and optionally specific roles"""
    def decorator(func):
        def wrapper(event, context):
            token = extract_token_from_event(event)
            if not token:
                return {
                    'statusCode': 401,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'No token provided'})
                }
            
            user_data = verify_jwt_token(token)
            if not user_data:
                return {
                    'statusCode': 401,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Invalid or expired token'})
                }
            
            if roles and user_data.get('role') not in roles:
                return {
                    'statusCode': 403,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Insufficient permissions'})
                }
            
            # Add user data to event for use in the function
            event['user'] = user_data
            return func(event, context)
        return wrapper
    return decorator

def hash_password(password: str) -> str:
    """Hash password using bcrypt (simplified for demo)"""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == hashed