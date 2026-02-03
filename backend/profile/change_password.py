import json
import boto3
import jwt
import hashlib
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

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == hashed

def get_user_by_id(user_id: str) -> Optional[Dict]:
    """Get user by ID from DynamoDB"""
    try:
        table_name = 'msc-evaluate-users-dev'
        table = dynamodb.Table(table_name)
        
        response = table.get_item(Key={'user_id': user_id})
        return response.get('Item')
    except Exception as e:
        print(f"Error getting user: {e}")
        return None

def update_user_password(user_id: str, new_password_hash: str) -> bool:
    """Update user password in DynamoDB"""
    try:
        table_name = 'msc-evaluate-users-dev'
        table = dynamodb.Table(table_name)
        
        table.update_item(
            Key={'user_id': user_id},
            UpdateExpression="SET password_hash = :password_hash, updated_at = :updated_at",
            ExpressionAttributeValues={
                ':password_hash': new_password_hash,
                ':updated_at': datetime.utcnow().isoformat()
            }
        )
        return True
    except Exception as e:
        print(f"Error updating password: {e}")
        return False

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
        
        # Parse request body
        body = json.loads(event['body'])
        current_password = body.get('currentPassword')
        new_password = body.get('newPassword')
        
        if not current_password or not new_password:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Current password and new password are required'})
            }
        
        # Get user from database
        user = get_user_by_id(user_data['user_id'])
        if not user:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'User not found'})
            }
        
        # Verify current password
        stored_password_hash = user.get('password_hash', '')
        if not verify_password(current_password, stored_password_hash):
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Current password is incorrect'})
            }
        
        # Update password
        new_password_hash = hash_password(new_password)
        if update_user_password(user_data['user_id'], new_password_hash):
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'message': 'Password changed successfully'
                })
            }
        else:
            return {
                'statusCode': 500,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Failed to update password'})
            }
        
    except Exception as e:
        print(f"Change password error: {e}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Internal server error'})
        }