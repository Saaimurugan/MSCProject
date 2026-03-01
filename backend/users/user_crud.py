import json
import boto3
import os
import uuid
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
users_table = dynamodb.Table(os.environ.get('USERS_TABLE', 'msc-evaluate-users-dev'))

def decimal_default(obj):
    """Helper to serialize Decimal objects"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def verify_admin(event):
    """Verify that the request is from an admin user"""
    headers = event.get('headers', {})
    # Check for user role in headers (set by frontend after login)
    user_role = headers.get('X-User-Role', headers.get('x-user-role', ''))
    
    if user_role != 'admin':
        return False, {
            'statusCode': 403,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-User-Role',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
            },
            'body': json.dumps({'error': 'Forbidden: Admin access required'})
        }
    return True, None

def lambda_handler(event, context):
    """
    Handle user CRUD operations
    Routes:
    - GET /users - List all users (Admin only)
    - GET /users/{user_id} - Get user by ID (Admin only)
    - POST /users - Create new user (Admin only)
    - PUT /users/{user_id} - Update user (Admin only)
    - DELETE /users/{user_id} - Delete user (Admin only)
    - POST /users/login - Login (Public)
    """
    
    http_method = event.get('httpMethod', '')
    path = event.get('path', '')
    path_params = event.get('pathParameters', {})
    
    # Login endpoint is public
    if http_method == 'POST' and '/login' in path:
        return handle_login(event)
    
    # All other endpoints require admin access
    is_admin, error_response = verify_admin(event)
    if not is_admin:
        return error_response
    
    try:
        if http_method == 'GET':
            if path_params and 'user_id' in path_params:
                return get_user(path_params['user_id'])
            else:
                return list_users(event)
        
        elif http_method == 'POST':
            return create_user(event)
        
        elif http_method == 'PUT':
            if path_params and 'user_id' in path_params:
                return update_user(path_params['user_id'], event)
            else:
                return error_response(400, 'User ID required')
        
        elif http_method == 'DELETE':
            if path_params and 'user_id' in path_params:
                return delete_user(path_params['user_id'])
            else:
                return error_response(400, 'User ID required')
        
        else:
            return error_response(405, 'Method not allowed')
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return error_response(500, f'Internal server error: {str(e)}')

def handle_login(event):
    """Handle user login"""
    try:
        body = json.loads(event.get('body', '{}'))
        username = body.get('username', '').strip().lower()
        password = body.get('password', '')
        
        if not username or not password:
            return error_response(400, 'Username and password required')
        
        # Query user by username
        response = users_table.scan(
            FilterExpression='username = :username',
            ExpressionAttributeValues={':username': username}
        )
        
        users = response.get('Items', [])
        
        if not users:
            return error_response(401, 'Invalid username or password')
        
        user = users[0]
        
        # Check if user is active
        if not user.get('is_active', True):
            return error_response(403, 'Account is disabled')
        
        # Verify password (in production, use proper password hashing)
        if user.get('password') != password:
            return error_response(401, 'Invalid username or password')
        
        # Return user info (excluding password)
        user_info = {
            'user_id': user['user_id'],
            'username': user['username'],
            'email': user.get('email', ''),
            'role': user['role'],
            'full_name': user.get('full_name', ''),
            'is_active': user.get('is_active', True)
        }
        
        return {
            'statusCode': 200,
            'headers': cors_headers(),
            'body': json.dumps({
                'message': 'Login successful',
                'user': user_info
            }, default=decimal_default)
        }
    
    except Exception as e:
        print(f"Login error: {str(e)}")
        return error_response(500, f'Login failed: {str(e)}')

def list_users(event):
    """List all users with optional filtering"""
    try:
        query_params = event.get('queryStringParameters', {}) or {}
        role = query_params.get('role')
        is_active = query_params.get('is_active')
        
        # Scan with optional filters
        scan_kwargs = {}
        filter_expressions = []
        expression_values = {}
        
        if role:
            filter_expressions.append('role = :role')
            expression_values[':role'] = role
        
        if is_active is not None:
            filter_expressions.append('is_active = :is_active')
            expression_values[':is_active'] = is_active.lower() == 'true'
        
        if filter_expressions:
            scan_kwargs['FilterExpression'] = ' AND '.join(filter_expressions)
            scan_kwargs['ExpressionAttributeValues'] = expression_values
        
        response = users_table.scan(**scan_kwargs)
        users = response.get('Items', [])
        
        # Remove passwords from response
        for user in users:
            user.pop('password', None)
        
        return {
            'statusCode': 200,
            'headers': cors_headers(),
            'body': json.dumps({
                'users': users,
                'count': len(users)
            }, default=decimal_default)
        }
    
    except Exception as e:
        print(f"List users error: {str(e)}")
        return error_response(500, f'Failed to list users: {str(e)}')

def get_user(user_id):
    """Get a specific user by ID"""
    try:
        response = users_table.get_item(Key={'user_id': user_id})
        
        if 'Item' not in response:
            return error_response(404, 'User not found')
        
        user = response['Item']
        user.pop('password', None)  # Remove password
        
        return {
            'statusCode': 200,
            'headers': cors_headers(),
            'body': json.dumps(user, default=decimal_default)
        }
    
    except Exception as e:
        print(f"Get user error: {str(e)}")
        return error_response(500, f'Failed to get user: {str(e)}')

def create_user(event):
    """Create a new user"""
    try:
        body = json.loads(event.get('body', '{}'))
        
        # Validate required fields
        required_fields = ['username', 'password', 'email', 'role']
        for field in required_fields:
            if not body.get(field):
                return error_response(400, f'Missing required field: {field}')
        
        username = body['username'].strip().lower()
        
        # Check if username already exists
        existing = users_table.scan(
            FilterExpression='username = :username',
            ExpressionAttributeValues={':username': username}
        )
        
        if existing.get('Items'):
            return error_response(409, 'Username already exists')
        
        # Validate role
        valid_roles = ['admin', 'tutor', 'student']
        if body['role'] not in valid_roles:
            return error_response(400, f'Invalid role. Must be one of: {", ".join(valid_roles)}')
        
        # Create user
        user_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        user = {
            'user_id': user_id,
            'username': username,
            'password': body['password'],  # In production, hash this!
            'email': body['email'].strip().lower(),
            'role': body['role'],
            'full_name': body.get('full_name', ''),
            'is_active': body.get('is_active', True),
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        users_table.put_item(Item=user)
        
        # Remove password from response
        user.pop('password')
        
        return {
            'statusCode': 201,
            'headers': cors_headers(),
            'body': json.dumps({
                'message': 'User created successfully',
                'user': user
            }, default=decimal_default)
        }
    
    except Exception as e:
        print(f"Create user error: {str(e)}")
        return error_response(500, f'Failed to create user: {str(e)}')

def update_user(user_id, event):
    """Update an existing user"""
    try:
        # Check if user exists
        response = users_table.get_item(Key={'user_id': user_id})
        if 'Item' not in response:
            return error_response(404, 'User not found')
        
        body = json.loads(event.get('body', '{}'))
        
        # Build update expression
        update_parts = []
        expression_values = {}
        expression_names = {}
        
        # Updatable fields
        if 'email' in body:
            update_parts.append('#email = :email')
            expression_values[':email'] = body['email'].strip().lower()
            expression_names['#email'] = 'email'
        
        if 'password' in body:
            update_parts.append('#password = :password')
            expression_values[':password'] = body['password']  # Hash in production!
            expression_names['#password'] = 'password'
        
        if 'role' in body:
            valid_roles = ['admin', 'tutor', 'student']
            if body['role'] not in valid_roles:
                return error_response(400, f'Invalid role. Must be one of: {", ".join(valid_roles)}')
            update_parts.append('#role = :role')
            expression_values[':role'] = body['role']
            expression_names['#role'] = 'role'
        
        if 'full_name' in body:
            update_parts.append('full_name = :full_name')
            expression_values[':full_name'] = body['full_name']
        
        if 'is_active' in body:
            update_parts.append('is_active = :is_active')
            expression_values[':is_active'] = body['is_active']
        
        if not update_parts:
            return error_response(400, 'No fields to update')
        
        # Add updated_at timestamp
        update_parts.append('updated_at = :updated_at')
        expression_values[':updated_at'] = datetime.utcnow().isoformat()
        
        update_expression = 'SET ' + ', '.join(update_parts)
        
        # Update user
        update_kwargs = {
            'Key': {'user_id': user_id},
            'UpdateExpression': update_expression,
            'ExpressionAttributeValues': expression_values,
            'ReturnValues': 'ALL_NEW'
        }
        
        if expression_names:
            update_kwargs['ExpressionAttributeNames'] = expression_names
        
        response = users_table.update_item(**update_kwargs)
        
        user = response['Attributes']
        user.pop('password', None)  # Remove password
        
        return {
            'statusCode': 200,
            'headers': cors_headers(),
            'body': json.dumps({
                'message': 'User updated successfully',
                'user': user
            }, default=decimal_default)
        }
    
    except Exception as e:
        print(f"Update user error: {str(e)}")
        return error_response(500, f'Failed to update user: {str(e)}')

def delete_user(user_id):
    """Delete a user"""
    try:
        # Check if user exists
        response = users_table.get_item(Key={'user_id': user_id})
        if 'Item' not in response:
            return error_response(404, 'User not found')
        
        # Delete user
        users_table.delete_item(Key={'user_id': user_id})
        
        return {
            'statusCode': 200,
            'headers': cors_headers(),
            'body': json.dumps({
                'message': 'User deleted successfully',
                'user_id': user_id
            })
        }
    
    except Exception as e:
        print(f"Delete user error: {str(e)}")
        return error_response(500, f'Failed to delete user: {str(e)}')

def cors_headers():
    """Return CORS headers"""
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-User-Role',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    }

def error_response(status_code, message):
    """Return error response"""
    return {
        'statusCode': status_code,
        'headers': cors_headers(),
        'body': json.dumps({'error': message})
    }
