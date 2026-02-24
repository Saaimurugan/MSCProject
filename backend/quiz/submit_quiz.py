import json
import boto3
from datetime import datetime
from typing import Dict, Optional
import uuid

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

class QuizResult:
    def __init__(self):
        table_name = 'msc-evaluate-quiz-results-dev'
        self.table = dynamodb.Table(table_name)
    
    def save_result(self, template_id, session_id, answers, total_score, correct_count, total_questions):
        result_id = str(uuid.uuid4())
        result = {
            'result_id': result_id,
            'session_id': session_id,
            'template_id': template_id,
            'answers': answers,
            'total_score': total_score,
            'correct_count': correct_count,
            'total_questions': total_questions,
            'completed_at': datetime.utcnow().isoformat(),
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        self.table.put_item(Item=result)
        return result

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
        body = json.loads(event['body'])
        template_id = body.get('template_id')
        session_id = body.get('session_id')
        answers = body.get('answers', [])  # List of {question_index, selected_answer}
        
        # Validate required fields
        if not template_id:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Template ID is required'})
            }
        
        if not answers:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Answers are required'})
            }
        
        # Generate session_id if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Get template to access correct answers
        template_model = Template()
        template = template_model.get_item({'template_id': template_id})
        
        if not template:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Template not found'})
            }
        
        questions = template.get('questions', [])
        total_questions = len(questions)
        
        # Validate all questions are answered
        answered_indices = {answer.get('question_index') for answer in answers}
        expected_indices = set(range(total_questions))
        
        if answered_indices != expected_indices:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'error': 'All questions must be answered',
                    'expected_questions': total_questions,
                    'answered_questions': len(answered_indices)
                })
            }
        
        # Calculate score and build detailed results
        correct_count = 0
        detailed_results = []
        
        for answer in answers:
            question_index = answer.get('question_index')
            selected_answer = answer.get('selected_answer')
            
            if question_index < 0 or question_index >= total_questions:
                return {
                    'statusCode': 400,
                    'headers': get_cors_headers(),
                    'body': json.dumps({'error': f'Invalid question_index: {question_index}'})
                }
            
            question = questions[question_index]
            correct_answer = question.get('correct_answer')
            
            is_correct = (selected_answer == correct_answer)
            if is_correct:
                correct_count += 1
            
            detailed_results.append({
                'question_index': question_index,
                'is_correct': is_correct,
                'selected_answer': selected_answer,
                'correct_answer': correct_answer
            })
        
        # Calculate percentage score
        total_score = (correct_count / total_questions * 100) if total_questions > 0 else 0
        
        # Save results to database
        quiz_result_model = QuizResult()
        result = quiz_result_model.save_result(
            session_id=session_id,
            template_id=template_id,
            answers=answers,
            total_score=total_score,
            correct_count=correct_count,
            total_questions=total_questions
        )
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'result_id': result['result_id'],
                'session_id': session_id,
                'total_score': total_score,
                'correct_count': correct_count,
                'total_questions': total_questions,
                'detailed_results': detailed_results
            })
        }
        
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Invalid JSON in request body'})
        }
    except Exception as e:
        print(f"Quiz submit error: {e}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Internal server error'})
        }