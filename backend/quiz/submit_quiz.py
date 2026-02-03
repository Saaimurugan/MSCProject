import json
import boto3
import jwt
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional
import uuid

# JWT Configuration
JWT_SECRET = 'your-jwt-secret-key-change-in-production'
JWT_ALGORITHM = "HS256"

# DynamoDB setup
dynamodb = boto3.resource('dynamodb')

def verify_jwt_token(token: str) -> Optional[Dict]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def extract_token_from_event(event: Dict) -> Optional[str]:
    """Extract JWT token from Lambda event"""
    headers = event.get('headers', {})
    auth_header = headers.get('Authorization') or headers.get('authorization')
    
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header[7:]  # Remove 'Bearer ' prefix
    return None

def get_cors_headers():
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    }

def get_template(template_id: str) -> Optional[Dict]:
    """Get template from DynamoDB"""
    try:
        table_name = 'msc-evaluate-templates-dev'
        table = dynamodb.Table(table_name)
        response = table.get_item(Key={'template_id': template_id})
        return response.get('Item')
    except Exception as e:
        print(f"Error getting template: {e}")
        return None

def save_quiz_result(user_id: str, template_id: str, student_name: str, 
                    student_id: str, answers: list, total_score: float) -> Dict:
    """Save quiz result to DynamoDB"""
    try:
        table_name = 'msc-evaluate-quiz-results-dev'
        table = dynamodb.Table(table_name)
        
        result_id = str(uuid.uuid4())
        result = {
            'result_id': result_id,
            'user_id': user_id,
            'template_id': template_id,
            'student_name': student_name,
            'student_id': student_id,
            'answers': answers,
            'total_score': total_score,
            'completed_at': datetime.utcnow().isoformat(),
            'created_at': datetime.utcnow().isoformat()
        }
        
        table.put_item(Item=result)
        return result
    except Exception as e:
        print(f"Error saving quiz result: {e}")
        raise e

def lambda_handler(event, context):
    # Handle OPTIONS request for CORS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': ''
        }
    
    # Verify authentication
    token = extract_token_from_event(event)
    if not token:
        return {
            'statusCode': 401,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'No token provided'})
        }
    
    user_data = verify_jwt_token(token)
    if not user_data:
        return {
            'statusCode': 401,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Invalid or expired token'})
        }
    
    try:
        body = json.loads(event['body'])
        template_id = body.get('template_id')
        student_name = body.get('student_name')
        student_id = body.get('student_id')
        answers = body.get('answers', [])  # List of {question_id, user_answer}
        
        if not template_id or not student_name or not student_id or not answers:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Template ID, student name, student ID, and answers are required'})
            }
        
        # Get template to access example answers
        template = get_template(template_id)
        
        if not template:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Template not found'})
            }
        
        # Score each answer using Bedrock
        client = boto3.client("bedrock-runtime", region_name="us-east-1")
        LITE_MODEL_ID = "amazon.nova-micro-v1:0"
        
        scored_answers = []
        total_score = 0
        
        for answer in answers:
            question_id = answer.get('question_id')
            user_answer = answer.get('user_answer')
            
            if question_id >= len(template['questions']):
                continue
                
            example_answer = template['questions'][question_id]['example_answer']
            
            # Use AI to score the answer
            prompt = f'''
            You are a professor responsible for comparing a given response with the provided reference answer. Evaluate the response and assign a score out of 10.
            
            User Answer:
            {user_answer}
            
            Example Answer:
            {example_answer}

            Return only the score (0-10), evaluation, justification, and suggestions in JSON format:
            {{
                "score": "<score_number>",
                "evaluation": "<evaluation_text>",
                "justification": "<justification_text>",
                "suggestions": "<suggestions_text>"
            }}
            '''

            message_list = [{"role": "user", "content": [{"text": prompt}]}]
            system_list = [{"text": "You are a professor responsible for comparing a given response with the provided reference answer. Evaluate the response and assign a score."}]
            inf_params = {"max_new_tokens": 1000, "top_p": 0.9, "top_k": 20, "temperature": 0.7}

            request_body = {
                "schemaVersion": "messages-v1",
                "messages": message_list,
                "system": system_list,
                "inferenceConfig": inf_params,
            }

            try:
                response = client.invoke_model_with_response_stream(
                    modelId=LITE_MODEL_ID,
                    body=json.dumps(request_body)
                )

                stream = response.get("body")
                response_data = ""
                
                for event_chunk in stream:
                    chunk = event_chunk.get("chunk")
                    if chunk:
                        chunk_json = json.loads(chunk.get("bytes").decode())
                        content_block_delta = chunk_json.get("contentBlockDelta", {}).get("delta", {}).get("text", "")
                        response_data += content_block_delta

                # Parse the AI response
                try:
                    # Extract JSON from response
                    json_start = response_data.find('{')
                    if json_start != -1:
                        json_end = response_data.rfind('}') + 1
                        json_str = response_data[json_start:json_end]
                        score_data = json.loads(json_str)
                    else:
                        score_data = {"score": "5", "evaluation": "Could not parse AI response", "justification": "Default score", "suggestions": ""}
                    
                    score = int(float(score_data.get('score', 5)))  # Default to 5 if parsing fails
                    score = max(0, min(10, score))  # Ensure score is between 0-10
                    total_score += score
                    
                    scored_answers.append({
                        'question_id': question_id,
                        'question': template['questions'][question_id]['question'],
                        'user_answer': user_answer,
                        'score': score,
                        'evaluation': score_data.get('evaluation', ''),
                        'justification': score_data.get('justification', ''),
                        'suggestions': score_data.get('suggestions', '')
                    })
                    
                except Exception as parse_error:
                    print(f"Error parsing AI response: {parse_error}")
                    scored_answers.append({
                        'question_id': question_id,
                        'question': template['questions'][question_id]['question'],
                        'user_answer': user_answer,
                        'score': 5,  # Default score
                        'evaluation': 'Error scoring answer',
                        'justification': f'Parsing error: {str(parse_error)}',
                        'suggestions': 'Please try again'
                    })
                    total_score += 5
                    
            except Exception as bedrock_error:
                print(f"Error calling Bedrock: {bedrock_error}")
                scored_answers.append({
                    'question_id': question_id,
                    'question': template['questions'][question_id]['question'],
                    'user_answer': user_answer,
                    'score': 5,  # Default score
                    'evaluation': 'Error calling AI service',
                    'justification': f'Service error: {str(bedrock_error)}',
                    'suggestions': 'Please try again later'
                })
                total_score += 5
        
        # Calculate percentage score
        max_score = len(answers) * 10
        percentage_score = (total_score / max_score * 100) if max_score > 0 else 0
        
        # Save results to database
        result = save_quiz_result(
            user_id=user_data['user_id'],
            template_id=template_id,
            student_name=student_name,
            student_id=student_id,
            answers=scored_answers,
            total_score=percentage_score
        )
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'result_id': result['result_id'],
                'total_score': percentage_score,
                'raw_score': total_score,
                'max_score': max_score,
                'answers': scored_answers
            })
        }
        
    except Exception as e:
        print(f"Quiz submit error: {e}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Internal server error'})
        }