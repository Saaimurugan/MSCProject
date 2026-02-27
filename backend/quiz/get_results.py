import json
import boto3
from decimal import Decimal

# DynamoDB setup
dynamodb = boto3.resource('dynamodb')

# Helper function to convert Decimal to int/float for JSON serialization
def decimal_to_number(obj):
    if isinstance(obj, list):
        return [decimal_to_number(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: decimal_to_number(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    else:
        return obj

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
        results_table_name = 'msc-evaluate-quiz-results-dev'
        templates_table_name = 'msc-evaluate-templates-dev'
        results_table = dynamodb.Table(results_table_name)
        templates_table = dynamodb.Table(templates_table_name)
        
        # Get query parameters for filtering
        query_params = event.get('queryStringParameters') or {}
        student_name = query_params.get('student_name')
        course = query_params.get('course')
        subject = query_params.get('subject')
        
        # Scan with optional filters
        filter_parts = []
        expression_values = {}
        
        if student_name:
            filter_parts.append('contains(student_name, :student_name)')
            expression_values[':student_name'] = student_name
            
        if course:
            filter_parts.append('course = :course')
            expression_values[':course'] = course
            
        if subject:
            filter_parts.append('subject = :subject')
            expression_values[':subject'] = subject
        
        # Execute scan
        if filter_parts:
            filter_expression = ' AND '.join(filter_parts)
            response = results_table.scan(
                FilterExpression=filter_expression,
                ExpressionAttributeValues=expression_values
            )
        else:
            response = results_table.scan()
        
        results = response.get('Items', [])
        
        # Enrich results with template questions
        for result in results:
            template_id = result.get('template_id')
            if template_id:
                try:
                    template_response = templates_table.get_item(Key={'template_id': template_id})
                    template = template_response.get('Item')
                    if template:
                        result['questions'] = template.get('questions', [])
                except Exception as e:
                    print(f"Error fetching template {template_id}: {e}")
                    result['questions'] = []
        
        # Convert Decimal types to int/float for JSON serialization
        results = decimal_to_number(results)
        
        # Sort by completed_at descending (most recent first)
        results.sort(key=lambda x: x.get('completed_at', ''), reverse=True)
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'results': results,
                'count': len(results)
            })
        }
        
    except Exception as e:
        print(f"Get results error: {e}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }
