import json
import boto3
from datetime import datetime
from typing import Dict, Optional
import uuid

# DynamoDB and Lambda setup
dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

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
    
    def save_result(self, template_id, session_id, answers, evaluations, average_score, total_questions):
        result_id = str(uuid.uuid4())
        result = {
            'result_id': result_id,
            'session_id': session_id,
            'template_id': template_id,
            'answers': answers,
            'evaluations': evaluations,
            'average_score': average_score,
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

def evaluate_answer(user_answer, example_answer, pdf_data=None):
    """Call MSC_Evaluate Lambda to evaluate an answer"""
    try:
        # If no example answer provided, return a default evaluation
        if not example_answer:
            return {
                'score': 'N/A',
                'evaluation': 'No example answer provided for comparison',
                'justification': 'Cannot evaluate without reference answer',
                'suggessions': 'Please provide an example answer in the template'
            }
        
        payload = {
            'user_answer': user_answer,
            'example_answer': example_answer
        }
        
        if pdf_data:
            payload['pdf_data'] = pdf_data
        
        response = lambda_client.invoke(
            FunctionName='msc-evaluate-function-dev',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        response_payload = json.loads(response['Payload'].read())
        
        if response_payload.get('statusCode') == 200:
            # Parse the evaluation response
            evaluation_text = response_payload.get('body', '{}')
            try:
                # Try to parse as JSON
                evaluation = json.loads(evaluation_text)
            except:
                # If not JSON, return as text
                evaluation = {
                    'score': 'N/A',
                    'evaluation': evaluation_text,
                    'justification': '',
                    'suggessions': ''
                }
            return evaluation
        else:
            return {
                'score': 'Error',
                'evaluation': 'Failed to evaluate answer',
                'justification': response_payload.get('body', 'Unknown error'),
                'suggessions': ''
            }
    except Exception as e:
        print(f"Evaluation error: {str(e)}")
        return {
            'score': 'Error',
            'evaluation': 'Failed to evaluate answer',
            'justification': str(e),
            'suggessions': ''
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
        answers = body.get('answers', [])  # List of {question_index, answer_text, pdf_data, pdf_filename}
        
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
        
        # Get template to access example answers
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
        
        # Evaluate each answer using MSC_Evaluate Lambda
        evaluations = []
        total_score = 0
        
        for answer in answers:
            question_index = answer.get('question_index')
            answer_text = answer.get('answer_text', '')
            pdf_data = answer.get('pdf_data')
            
            if question_index < 0 or question_index >= total_questions:
                return {
                    'statusCode': 400,
                    'headers': get_cors_headers(),
                    'body': json.dumps({'error': f'Invalid question_index: {question_index}'})
                }
            
            question = questions[question_index]
            example_answer = question.get('example_answer', '')
            
            # Call MSC_Evaluate to get evaluation
            evaluation = evaluate_answer(answer_text, example_answer, pdf_data)
            
            # Extract numeric score
            score_str = evaluation.get('score', '0')
            try:
                # Try to extract number from score string
                score_value = float(''.join(filter(lambda x: x.isdigit() or x == '.', str(score_str))))
            except:
                score_value = 0
            
            total_score += score_value
            
            evaluations.append({
                'question_index': question_index,
                'score': evaluation.get('score'),
                'evaluation': evaluation.get('evaluation'),
                'justification': evaluation.get('justification'),
                'suggessions': evaluation.get('suggessions'),
                'user_answer': answer_text if answer_text else f"PDF: {answer.get('pdf_filename', 'uploaded')}"
            })
        
        # Calculate average score
        average_score = (total_score / total_questions) if total_questions > 0 else 0
        
        # Save results to database
        quiz_result_model = QuizResult()
        result = quiz_result_model.save_result(
            session_id=session_id,
            template_id=template_id,
            answers=answers,
            evaluations=evaluations,
            average_score=average_score,
            total_questions=total_questions
        )
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'result_id': result['result_id'],
                'session_id': session_id,
                'average_score': average_score,
                'total_questions': total_questions,
                'evaluations': evaluations
            })
        }
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {str(e)}")
        return {
            'statusCode': 400,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Invalid JSON in request body'})
        }
    except Exception as e:
        print(f"Quiz submit error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }