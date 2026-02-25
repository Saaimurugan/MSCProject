import json
import boto3
import uuid
from datetime import datetime
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
    
    def update_template(self, template_id, title, subject, course, questions):
        template = {
            'template_id': template_id,
            'title': title,
            'subject': subject,
            'course': course,
            'questions': questions,
            'is_active': True,
            'updated_at': datetime.utcnow().isoformat()
        }
        # Get existing created_at
        existing = self.get_item({'template_id': template_id})
        if existing:
            template['created_at'] = existing.get('created_at')
        self.table.put_item(Item=template)
        return template
    
    def delete_template(self, template_id):
        self.table.delete_item(Key={'template_id': template_id})

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
            
            if not question_text:
                return {
                    'statusCode': 400,
                    'headers': get_cors_headers(),
                    'body': json.dumps({'error': 'Validation Error', 'message': f'Question {i+1} must have question_text'})
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
        
        # Build filter expression - only filter by is_active if it exists
        filter_parts = []
        expression_values = {}
        
        if subject:
            filter_parts.append('subject = :subject')
            expression_values[':subject'] = subject
            
        if course:
            filter_parts.append('course = :course')
            expression_values[':course'] = course
        
        # Scan with optional filters
        if filter_parts:
            filter_expression = ' AND '.join(filter_parts)
            response = table.scan(
                FilterExpression=filter_expression,
                ExpressionAttributeValues=expression_values
            )
        else:
            response = table.scan()
        
        templates = response.get('Items', [])
        
        # Convert Decimal types to int/float for JSON serialization
        templates = decimal_to_number(templates)
        
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
        
        if not template:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Not Found', 'message': 'Template not found'})
            }
        
        # Convert Decimal types to int/float for JSON serialization
        template = decimal_to_number(template)
        
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

def update_template(event, context):
    """PUT /templates/{template_id} - Update an existing template"""
    try:
        template_id = event.get('pathParameters', {}).get('template_id')
        
        if not template_id:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Bad Request', 'message': 'template_id is required'})
            }
        
        body = json.loads(event['body'])
        title = body.get('title', '').strip()
        subject = body.get('subject', '').strip()
        course = body.get('course', '').strip()
        questions = body.get('questions', [])
        
        # Validate required fields (same as create)
        if not title or not subject or not course or not questions:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Validation Error', 'message': 'All fields are required'})
            }
        
        template_model = Template()
        template = template_model.update_template(
            template_id=template_id,
            title=title,
            subject=subject,
            course=course,
            questions=questions
        )
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'template_id': template['template_id'],
                'message': 'Template updated successfully'
            })
        }
        
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Invalid JSON', 'message': 'Request body must be valid JSON'})
        }
    except Exception as e:
        print(f"Update template error: {e}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Internal Server Error', 'message': 'Unable to process request'})
        }

def delete_template(event, context):
    """DELETE /templates/{template_id} - Delete a template"""
    try:
        template_id = event.get('pathParameters', {}).get('template_id')
        
        if not template_id:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Bad Request', 'message': 'template_id is required'})
            }
        
        template_model = Template()
        template_model.delete_template(template_id)
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'message': 'Template deleted successfully'
            })
        }
        
    except Exception as e:
        print(f"Delete template error: {e}")
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

    elif http_method == 'PUT' and '/templates/' in path:
        return update_template(event, context)

    elif http_method == 'DELETE' and '/templates/' in path:
        return delete_template(event, context)

    else:
        return {
            'statusCode': 404,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Not Found', 'message': 'Route not found'})
        }


