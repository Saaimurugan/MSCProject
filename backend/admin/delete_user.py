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

@require_auth(roles=['admin'])
def lambda_handler(event, context):
    # Handle OPTIONS request for CORS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': ''
        }
    
    try:
        # Get user ID from path parameters
        user_id = event['pathParameters']['userId']
        
        user_model = User()
        
        # Check if user exists
        user = user_model.get_item({'user_id': user_id})
        if not user:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'User not found'})
            }
        
        # Prevent admin from deleting themselves
        if user_id == event['user']['user_id']:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Cannot delete your own account'})
            }
        
        # Soft delete - mark as inactive instead of actual deletion
        user_model.update_item(
            {'user_id': user_id},
            {'is_active': False}
        )
        
        # Log the action
        log_admin_action(
            event['user']['user_id'], 
            'delete_user', 
            f"Deleted user: {user['email']}"
        )
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'message': 'User deleted successfully'
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)})
        }

def log_admin_action(admin_id, action, details):
    """Log admin actions for audit trail"""
    try:
        from shared.db_models import BaseModel
        import uuid
        from datetime import datetime
        
        log_model = BaseModel('msc-evaluate-admin-logs-dev')
        log_entry = {
            'log_id': str(uuid.uuid4()),
            'admin_id': admin_id,
            'action': action,
            'details': details,
            'timestamp': datetime.utcnow().isoformat()
        }
        log_model.create_item(log_entry)
    except:
        pass  # Don't fail the main operation if logging fails