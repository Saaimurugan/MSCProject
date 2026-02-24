import json
import boto3
import uuid
from datetime import datetime
from typing import Dict, Optional

# DynamoDB setup
dynamodb = boto3.resource('dynamodb')

# Database Models
class Template:
    def __init__(self):
        table_name = 'msc-evaluate-templates-dev'
        self.table = dynamodb.Table(table_name)
    
    def get_item(self, key):
        response = self.table.get_item(Key=key)
        return response.get('Item')

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
        template_model = Template()
        template = template_model.get_item({'template_id': template_id})
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