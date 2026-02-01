import json
import sys
import os
import boto3
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.db_models import Template, QuizResult
from shared.auth_utils import require_auth

@require_auth()
def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        template_id = body.get('template_id')
        student_name = body.get('student_name')
        student_id = body.get('student_id')
        answers = body.get('answers', [])  # List of {question_id, user_answer}
        
        if not template_id or not student_name or not student_id or not answers:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Template ID, student name, student ID, and answers are required'})
            }
        
        # Get template to access example answers
        template_model = Template()
        template = template_model.get_item({'template_id': template_id})
        
        if not template:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Template not found'})
            }
        
        # Score each answer using Bedrock (reuse existing logic)
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
            
            # Use the same scoring logic as the original Lambda
            prompt = f'''
            You are a professor responsible for comparing a given response with the provided reference answer. Evaluate the response and assign a score.
            User Answer:
            {user_answer}
            Example Answer:
            {example_answer}

            Return only the score, the score should be purly based on the example_answer.
            Explain the evaluation, justify the score and suggession to score more.

            All the above should be provided as the below JSON:
            "score": "<score>",
            "evaluation": "<evaluation>",
            "justification": "<justification>",
            "suggestions": "suggestions"
            '''

            message_list = [{"role": "user", "content": [{"text": prompt}]}]
            system_list = [{"text": "You are a professor responsible for comparing a given response with the provided reference answer. Evaluate the response and assign a score."}]
            inf_params = {"max_new_tokens": 5000, "top_p": 0.9, "top_k": 20, "temperature": 0.9}

            request_body = {
                "schemaVersion": "messages-v1",
                "messages": message_list,
                "system": system_list,
                "inferenceConfig": inf_params,
            }

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
                json_match = response_data.find('{')
                if json_match != -1:
                    json_end = response_data.rfind('}') + 1
                    json_str = response_data[json_match:json_end]
                    score_data = json.loads(json_str)
                else:
                    score_data = {"score": "0", "evaluation": "Error parsing response", "suggestions": ""}
                
                score = int(score_data.get('score', 0))
                total_score += score
                
                scored_answers.append({
                    'question_id': question_id,
                    'question': template['questions'][question_id]['question'],
                    'user_answer': user_answer,
                    'score': score,
                    'evaluation': score_data.get('evaluation', ''),
                    'suggestions': score_data.get('suggestions', '')
                })
                
            except Exception as parse_error:
                scored_answers.append({
                    'question_id': question_id,
                    'question': template['questions'][question_id]['question'],
                    'user_answer': user_answer,
                    'score': 0,
                    'evaluation': f'Error scoring answer: {str(parse_error)}',
                    'suggestions': ''
                })
        
        # Save results to database
        quiz_result_model = QuizResult()
        result = quiz_result_model.save_result(
            user_id=event['user']['user_id'],
            template_id=template_id,
            student_name=student_name,
            student_id=student_id,
            answers=scored_answers,
            total_score=total_score
        )
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'result_id': result['result_id'],
                'total_score': total_score,
                'max_score': len(answers) * 10,
                'answers': scored_answers
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }