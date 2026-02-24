import json
import boto3
import uuid
from datetime import datetime

# DynamoDB setup
dynamodb = boto3.resource('dynamodb')

# Database Model
class Template:
    def __init__(self):
        table_name = 'msc-evaluate-templates-dev'
        self.table = dynamodb.Table(table_name)
    
    def create_item(self, item):
        item['created_at'] = datetime.utcnow().isoformat()
        item['updated_at'] = datetime.utcnow().isoformat()
        self.table.put_item(Item=item)
        return item
    
    def get_item(self, key):
        response = self.table.get_item(Key=key)
        return response.get('Item')
    
    def create_template(self, title, subject, course, questions):
        template_id = str(uuid.uuid4())
        template = {
            'template_id': template_id,
            'title': title,
            'subject': subject,
            'course': course,
            'questions': questions,
            'is_active': True
        }
        return self.create_item(template)

def get_cors_headers():
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    }

def handle_options(event, context):
    """Handle CORS preflight requests"""
    return {
        'statusCode': 200,
        'headers': get_cors_headers(),
        'body': ''
    }

def create_template(event, context):
    """POST /templates - Create a new template"""
    try:
        body = json.loads(event['body'])
        title = body.get('title', '').strip()
        subject = body.get('subject', '').strip()
        course = body.get('course', '').strip()
        questions = body.get('questions', [])
        
        # Validate required fields
        if not title:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Validation Error', 'message': 'Title is required and cannot be empty'})
            }
        
        if not subject:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Validation Error', 'message': 'Subject is required and cannot be empty'})
            }
        
        if not course:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Validation Error', 'message': 'Course is required and cannot be empty'})
            }
        
        if not questions:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Validation Error', 'message': 'At least one question is required'})
            }
        
        # Validate questions format
        for i, question in enumerate(questions):
            question_text = question.get('question_text', '').strip()
            options = question.get('options', [])
            correct_answer = question.get('correct_answer')
            
            if not question_text:
                return {
                    'statusCode': 400,
                    'headers': get_cors_headers(),
                    'body': json.dumps({'error': 'Validation Error', 'message': f'Question {i+1} must have question_text'})
                }
            
            if not options or len(options) < 2:
                return {
                    'statusCode': 400,
                    'headers': get_cors_headers(),
                    'body': json.dumps({'error': 'Validation Error', 'message': f'Question {i+1} must have at least 2 answer options'})
                }
            
            if correct_answer is None:
                return {
                    'statusCode': 400,
                    'headers': get_cors_headers(),
                    'body': json.dumps({'error': 'Validation Error', 'message': f'Question {i+1} must have a correct answer designated'})
                }
            
            if not isinstance(correct_answer, int) or correct_answer < 0 or correct_answer >= len(options):
                return {
                    'statusCode': 400,
                    'headers': get_cors_headers(),
                    'body': json.dumps({'error': 'Validation Error', 'message': f'Question {i+1} has invalid correct_answer index'})
                }
        
        template_model = Template()
        template = template_model.create_template(
            title=title,
            subject=subject,
            course=course,
            questions=questions
        )
        
        return {
            'statusCode': 201,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'template_id': template['template_id'],
                'message': 'Template created successfully'
            })
        }
        
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Invalid JSON', 'message': 'Request body must be valid JSON'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Internal Server Error', 'message': 'Unable to process request'})
        }

def get_templates(event, context):
    """GET /templates - Get all templates with optional filtering"""
    try:
        query_params = event.get('queryStringParameters') or {}
        subject = query_params.get('subject')
        course = query_params.get('course')
        
        table_name = 'msc-evaluate-templates-dev'
        table = dynamodb.Table(table_name)
        
        # Build filter expression
        filter_expression = 'is_active = :active'
        expression_values = {':active': True}
        
        if subject:
            filter_expression += ' AND subject = :subject'
            expression_values[':subject'] = subject
            
        if course:
            filter_expression += ' AND course = :course'
            expression_values[':course'] = course
        
        response = table.scan(
            FilterExpression=filter_expression,
            ExpressionAttributeValues=expression_values
        )
        
        templates = response.get('Items', [])
        
        # Add question count to each template
        for template in templates:
            template['question_count'] = len(template.get('questions', []))
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'templates': templates,
                'count': len(templates)
            })
        }
        
    except Exception as e:
        print(f"Get templates error: {e}")
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'templates': [],
                'count': 0
            })
        }

def get_template_by_id(event, context):
    """GET /templates/{template_id} - Get a specific template by ID"""
    try:
        template_id = event.get('pathParameters', {}).get('template_id')
        
        if not template_id:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Bad Request', 'message': 'template_id is required'})
            }
        
        template_model = Template()
        template = template_model.get_item({'template_id': template_id})
        
        if not template or not template.get('is_active', True):
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Not Found', 'message': 'Template not found'})
            }
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'template_id': template['template_id'],
                'title': template['title'],
                'subject': template['subject'],
                'course': template['course'],
                'questions': template['questions'],
                'created_at': template.get('created_at'),
                'updated_at': template.get('updated_at')
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Internal Server Error', 'message': 'Unable to process request'})
        }

def lambda_handler(event, context):
    """Main Lambda handler - routes requests based on HTTP method and path"""
    http_method = event.get('httpMethod', '')
    path = event.get('path', '')
    
    # Handle CORS preflight
    if http_method == 'OPTIONS':
        return handle_options(event, context)
    
    # Route based on method and path
    if http_method == 'POST' and path == '/templates':
        return create_template(event, context)
    
    elif http_method == 'GET' and path == '/templates':
        return get_templates(event, context)
    
    elif http_method == 'GET' and '/templates/' in path:
        return get_template_by_id(event, context)
    
    else:
        return {
            'statusCode': 404,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Not Found', 'message': 'Route not found'})
        }
