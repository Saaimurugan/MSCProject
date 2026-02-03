import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.db_models import User
from shared.auth_utils import require_auth

def get_cors_headers():
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    }

@require_auth()
def lambda_handler(event, context):
    # Handle OPTIONS request for CORS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': ''
        }
    
    try:
        user_id = event['user']['user_id']
        user_model = User()
        
        # Get user profile
        user = user_model.get_item({'user_id': user_id})
        if not user:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'User not found'})
            }
        
        # Return safe profile data
        profile = {
            'user_id': user.get('user_id'),
            'name': user.get('name'),
            'email': user.get('email'),
            'role': user.get('role'),
            'created_at': user.get('created_at'),
            'updated_at': user.get('updated_at'),
            'last_login': user.get('last_login'),
            'is_active': user.get('is_active')
        }
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'profile': profile
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)})
        }