import json
import boto3
from decimal import Decimal

# DynamoDB setup
dynamodb = boto3.resource('dynamodb')

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
        # Get result_id from path parameters
        path_params = event.get('pathParameters') or {}
        result_id = path_params.get('id')
        
        if not result_id:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Result ID is required'})
            }
        
        table_name = 'msc-evaluate-quiz-results-dev'
        table = dynamodb.Table(table_name)
        
        # Check if result exists
        response = table.get_item(Key={'result_id': result_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Result not found'})
            }
        
        # Delete the result
        table.delete_item(Key={'result_id': result_id})
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'message': 'Result deleted successfully',
                'result_id': result_id
            })
        }
        
    except Exception as e:
        print(f"Delete result error: {e}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }
