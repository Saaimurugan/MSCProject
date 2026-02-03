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

def update_user_profile(user_id: str, updates: Dict) -> Dict:
    """Update user profile in DynamoDB"""
    try:
        table_name = 'msc-evaluate-users-dev'
        table = dynamodb.Table(table_name)
        
        # Add updated timestamp
        updates['updated_at'] = datetime.utcnow().isoformat()
        
        # Build update expression
        update_expression = "SET " + ", ".join([f"{k} = :{k}" for k in updates.keys()])
        expression_values = {f":{k}": v for k, v in updates.items()}
        
        response = table.update_item(
            Key={'user_id': user_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ReturnValues="ALL_NEW"
        )
        return response['Attributes']
    except Exception as e:
        print(f"Error updating user profile: {e}")
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
        
        # Parse request body
        body = json.loads(event['body'])
        name = body.get('name')
        email = body.get('email')
        
        if not name and not email:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'At least one field (name or email) is required'})
            }
        
        # Prepare updates
        updates = {}
        if name:
            updates['name'] = name
        if email:
            updates['email'] = email
        
        # Update user profile
        updated_user = update_user_profile(user_data['user_id'], updates)
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'message': 'Profile updated successfully',
                'user': {
                    'user_id': updated_user['user_id'],
                    'email': updated_user['email'],
                    'name': updated_user['name'],
                    'role': updated_user['role']
                }
            })
        }
        
    except Exception as e:
        print(f"Update profile error: {e}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Internal server error'})
        }