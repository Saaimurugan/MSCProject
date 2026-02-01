import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.db_models import User
from shared.auth_utils import generate_jwt_token, verify_password

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        email = body.get('email')
        password = body.get('password')
        
        if not email or not password:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Email and password are required'})
            }
        
        user_model = User()
        user = user_model.get_user_by_email(email)
        
        if not user or not user.get('is_active'):
            return {
                'statusCode': 401,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Invalid credentials'})
            }
        
        # In production, verify hashed password
        # For demo, assuming password is stored as hash
        if not verify_password(password, user.get('password_hash', '')):
            return {
                'statusCode': 401,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Invalid credentials'})
            }
        
        # Generate JWT token
        token = generate_jwt_token(user)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'token': token,
                'user': {
                    'user_id': user['user_id'],
                    'email': user['email'],
                    'name': user['name'],
                    'role': user['role']
                }
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }