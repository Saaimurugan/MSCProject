import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.db_models import Template

def get_cors_headers():
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS'
    }

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        title = body.get('title', '').strip()
        subject = body.get('subject', '').strip()
        course = body.get('course', '').strip()
        questions = body.get('questions', [])
        
        # Validate non-empty title, subject, course
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
            
            # Validate minimum 2 options
            if not options or len(options) < 2:
                return {
                    'statusCode': 400,
                    'headers': get_cors_headers(),
                    'body': json.dumps({'error': 'Validation Error', 'message': f'Question {i+1} must have at least 2 answer options'})
                }
            
            # Validate correct answer is required and valid
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