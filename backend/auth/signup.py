import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.db_models import User
from shared.auth_utils import generate_jwt_token, hash_password

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        email = body.get('email')
        password = body.get('password')
        name = body.get('name')
        role = body.get('role', 'student')  # Default to student
        
        if not email or not password or not name:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Email, password, and name are required'})
            }
        
        user_model = User()
        
        # Check if user already exists
        existing_user = user_model.get_user_by_email(email)
        if existing_user:
            return {
                'statusCode': 409,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'User already exists'})
            }
        
        # Create new user
        user_data = user_model.create_user(email, name, role)
        
        # In production, hash and store password
        password_hash = hash_password(password)
        user_model.update_item(
            {'user_id': user_data['user_id']},
            {'password_hash': password_hash}
        )
        
        # Generate JWT token
        token = generate_jwt_token(user_data)
        
        return {
            'statusCode': 201,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'token': token,
                'user': {
                    'user_id': user_data['user_id'],
                    'email': user_data['email'],
                    'name': user_data['name'],
                    'role': user_data['role']
                }
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }