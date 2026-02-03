import boto3
import hashlib
import uuid
from datetime import datetime

def hash_password(password: str) -> str:
    """Hash password using SHA256 (simplified for demo)"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_test_user():
    """Create a test user in DynamoDB"""
    try:
        dynamodb = boto3.resource('dynamodb')
        table_name = 'msc-evaluate-users-dev'
        table = dynamodb.Table(table_name)
        
        # Create test user
        user_id = str(uuid.uuid4())
        user = {
            'user_id': user_id,
            'email': 'saaimurugan@gmail.com',
            'name': 'Test User',
            'role': 'admin',  # Make this user an admin
            'password_hash': hash_password('Rujula@123'),
            'is_active': True,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        table.put_item(Item=user)
        print(f"Test user created successfully with ID: {user_id}")
        print(f"Email: {user['email']}")
        print(f"Password: Rujula@123")
        print(f"Role: {user['role']}")
        
    except Exception as e:
        print(f"Error creating test user: {e}")

if __name__ == "__main__":
    create_test_user()