import json
import boto3
import jwt
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

def update_user_role(user_id: str, new_role: str) -> Dict:
    """Update user role in DynamoDB"""
    try:
        table_name = 'msc-evaluate-users-dev'
        table = dynamodb.Table(table_name)
        
        response = table.update_item(
            Key={'user_id': user_id},
            UpdateExpression="SET #role = :role, updated_at = :updated_at",
            ExpressionAttributeNames={'#role': 'role'},
            ExpressionAttributeValues={
                ':role': new_role,
                ':updated_at': datetime.utcnow().isoformat()
            },
            ReturnValues="ALL_NEW"
        )
        return response['Attributes']
    except Exception as e:
        print(f"Error updating user role: {e}")
        raise e

def log_admin_action(admin_id, action, details):
    """Log admin actions for audit trail"""
    try:
        table_name = 'msc-evaluate-admin-logs-dev'
        table = dynamodb.Table(table_name)
        
        log_entry = {
            'log_id': str(uuid.uuid4()),
            'admin_id': admin_id,
            'action': action,
            'details': details,
            'timestamp': datetime.utcnow().isoformat()
        }
        table.put_item(Item=log_entry)
    except Exception as e:
        print(f"Error logging admin action: {e}")
        pass  # Don't fail the main operation if logging fails

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
    
    try:
        # Get user ID from path parameters
        user_id = event['pathParameters']['userId']
        
        body = json.loads(event['body'])
        new_role = body.get('role')
        
        if not new_role or new_role not in ['student', 'tutor', 'admin']:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Valid role is required (student, tutor, admin)'})
            }
        
        # Check if user exists
        user = get_user_by_id(user_id)
        if not user:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'User not found'})
            }
        
        # Update user role
        updated_user = update_user_role(user_id, new_role)
        
        # Log the action
        log_admin_action(
            user_data['user_id'], 
            'update_user_role', 
            f"Changed role of {user['email']} from {user['role']} to {new_role}"
        )
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'message': 'User role updated successfully',
                'user': {
                    'user_id': updated_user['user_id'],
                    'email': updated_user['email'],
                    'name': updated_user['name'],
                    'role': updated_user['role']
                }
            })
        }
        
    except Exception as e:
        print(f"Update user role error: {e}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Internal server error'})
        }