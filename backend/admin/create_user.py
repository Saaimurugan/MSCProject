import json
import boto3
import jwt
import hashlib
import uuid
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

def hash_password(password: str) -> str:
    """Hash password using SHA256 (simplified for demo)"""
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_by_email(email: str) -> Optional[Dict]:
    """Get user by email from DynamoDB"""
    try:
        table_name = 'msc-evaluate-users-dev'
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

def create_user(email: str, name: str, password: str, role: str = 'student') -> Dict:
    """Create a new user in DynamoDB"""
    try:
        table_name = 'msc-evaluate-users-dev'
        table = dynamodb.Table(table_name)
        
        user_id = str(uuid.uuid4())
        user = {
            'user_id': user_id,
            'email': email,
            'name': name,
            'role': role,
            'password_hash': hash_password(password),
            'is_active': True,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        table.put_item(Item=user)
        return user
    except Exception as e:
        print(f"Error creating user: {e}")
        raise e

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
        
        body = json.loads(event['body'])
        email = body.get('email')
        name = body.get('name')
        password = body.get('password')
        role = body.get('role', 'student')
        
        if not email or not name or not password:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Email, name, and password are required'})
            }
        
        # Check if user already exists
        existing_user = get_user_by_email(email)
        if existing_user:
            return {
                'statusCode': 409,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'User with this email already exists'})
            }
        
        # Create new user
        user = create_user(email, name, password, role)
        
        return {
            'statusCode': 201,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'message': 'User created successfully',
                'user': {
                    'user_id': user['user_id'],
                    'email': user['email'],
                    'name': user['name'],
                    'role': user['role']
                }
            })
        }
        
    except Exception as e:
        print(f"Create user error: {e}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Internal server error'})
        }