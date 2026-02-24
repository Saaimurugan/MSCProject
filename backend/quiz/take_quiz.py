import json
import boto3
from typing import Dict, Optional

# DynamoDB setup
dynamodb = boto3.resource('dynamodb')

def get_template_by_id(template_id: str) -> Optional[Dict]:
    """Get template by ID from DynamoDB"""
    try:
        table_name = 'msc-evaluate-templates-dev'
        table = dynamodb.Table(table_name)
        
        response = table.get_item(Key={'template_id': template_id})
        return response.get('Item')
    except Exception as e:
        print(f"Error getting template: {e}")
        return None

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
        # Get template ID from path parameters
        template_id = event['pathParameters']['templateId']
        
        # Get template from database
        template = get_template_by_id(template_id)
        if not template:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Template not found'})
            }
        
        # Remove correct answers from questions before sending to client
        questions_without_answers = []
        for question in template.get('questions', []):
            question_copy = {
                'question_text': question['question_text'],
                'options': question['options']
                # Intentionally omit 'correct_answer' field
            }
            questions_without_answers.append(question_copy)
        
        # Return template data for quiz taking
        quiz_data = {
            'template_id': template['template_id'],
            'title': template['title'],
            'subject': template['subject'],
            'course': template['course'],
            'questions': questions_without_answers,
            'time_limit': template.get('time_limit', 3600),  # Default 1 hour
            'instructions': template.get('instructions', 'Answer all questions to the best of your ability.')
        }
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({'quiz': quiz_data})
        }
        
    except Exception as e:
        print(f"Take quiz error: {e}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Internal server error'})
        }