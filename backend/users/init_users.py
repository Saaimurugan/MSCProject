"""
Script to initialize the users table with default users
Run this after deploying the infrastructure
"""
import boto3
import uuid
from datetime import datetime

def init_users(table_name='msc-evaluate-users-dev'):
    """Initialize users table with default users"""
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    
    timestamp = datetime.utcnow().isoformat()
    
    default_users = [
        {
            'user_id': str(uuid.uuid4()),
            'username': 'admin',
            'password': 'admin123',  # In production, hash this!
            'email': 'admin@example.com',
            'role': 'admin',
            'full_name': 'System Administrator',
            'is_active': True,
            'created_at': timestamp,
            'updated_at': timestamp
        },
        {
            'user_id': str(uuid.uuid4()),
            'username': 'student',
            'password': 'student123',
            'email': 'student@example.com',
            'role': 'student',
            'full_name': 'Demo Student',
            'is_active': True,
            'created_at': timestamp,
            'updated_at': timestamp
        },
        {
            'user_id': str(uuid.uuid4()),
            'username': 'tutor',
            'password': 'tutor123',
            'email': 'tutor@example.com',
            'role': 'tutor',
            'full_name': 'Demo Tutor',
            'is_active': True,
            'created_at': timestamp,
            'updated_at': timestamp
        }
    ]
    
    print(f"Initializing users table: {table_name}")
    
    for user in default_users:
        try:
            table.put_item(Item=user)
            print(f"✓ Created user: {user['username']} ({user['role']})")
        except Exception as e:
            print(f"✗ Failed to create user {user['username']}: {str(e)}")
    
    print("\nDefault users created successfully!")
    print("\nLogin credentials:")
    print("  Admin:   admin / admin123")
    print("  Tutor:   tutor / tutor123")
    print("  Student: student / student123")

if __name__ == '__main__':
    import sys
    table_name = sys.argv[1] if len(sys.argv) > 1 else 'msc-evaluate-users-dev'
    init_users(table_name)
