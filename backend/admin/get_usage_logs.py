import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.db_models import BaseModel
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
        # Get usage logs from multiple sources
        logs = []
        
        # Get admin action logs
        admin_logs = get_admin_logs()
        logs.extend(admin_logs)
        
        # Get user activity logs (login, quiz submissions, etc.)
        activity_logs = get_activity_logs()
        logs.extend(activity_logs)
        
        # Sort by timestamp (most recent first)
        logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Limit to last 100 entries
        logs = logs[:100]
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'logs': logs,
                'count': len(logs)
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)})
        }

def get_admin_logs():
    """Get admin action logs"""
    try:
        log_model = BaseModel('msc-evaluate-admin-logs-dev')
        response = log_model.table.scan()
        admin_logs = response.get('Items', [])
        
        # Format admin logs
        formatted_logs = []
        for log in admin_logs:
            formatted_logs.append({
                'user_name': 'Admin User',  # Could join with user table for actual name
                'action': log.get('action', 'unknown'),
                'resource': log.get('details', ''),
                'timestamp': log.get('timestamp'),
                'ip_address': 'N/A'  # Could be added to logging
            })
        
        return formatted_logs
    except:
        return []

def get_activity_logs():
    """Get user activity logs (simulated - in production would come from CloudWatch or separate logging)"""
    try:
        # This would typically come from CloudWatch logs, API Gateway logs, or a separate logging table
        # For demo purposes, we'll create some sample logs
        from datetime import datetime, timedelta
        import random
        
        sample_logs = []
        users = ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown']
        actions = ['login', 'logout', 'quiz_submit', 'template_view']
        
        for i in range(20):
            log_time = datetime.utcnow() - timedelta(hours=random.randint(1, 72))
            sample_logs.append({
                'user_name': random.choice(users),
                'action': random.choice(actions),
                'resource': f'Resource {random.randint(1, 10)}',
                'timestamp': log_time.isoformat(),
                'ip_address': f'192.168.1.{random.randint(1, 255)}'
            })
        
        return sample_logs
    except:
        return []