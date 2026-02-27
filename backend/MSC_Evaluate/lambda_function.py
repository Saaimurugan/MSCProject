import boto3
import json
from datetime import datetime
import base64
import PyPDF2
from io import BytesIO

def extract_text_from_pdf(pdf_base64):
    """Extract text from base64 encoded PDF"""
    try:
        # Decode base64 to bytes
        pdf_bytes = base64.b64decode(pdf_base64)
        
        # Create a PDF reader object
        pdf_file = BytesIO(pdf_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # Extract text from all pages
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text.strip()
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {str(e)}")

def lambda_handler(event, context):
    try:
        # Initialize Bedrock Runtime client
        client = boto3.client("bedrock-runtime", region_name="us-east-1")

        LITE_MODEL_ID = "amazon.nova-micro-v1:0"

        # Extract data from event
        user_answer = event.get("user_answer", "")
        pdf_data = event.get("pdf_data")
        example_answer = event.get("example_answer", "")

        # If PDF is provided, extract text from it
        if pdf_data:
            try:
                user_answer = extract_text_from_pdf(pdf_data)
            except Exception as e:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': f'PDF processing failed: {str(e)}'})
                }

        # Validate that we have an answer
        if not user_answer:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No answer provided (text or PDF)'})
            }

        # Construct the prompt for evaluation
        prompt = f'''You are an expert professor evaluating student answers. Your task is to compare the student's answer with the reference answer and provide a fair, accurate score.

**Student's Answer:**
{user_answer}

**Reference Answer (Example):**
{example_answer}

**Evaluation Guidelines:**
1. Score from 0-100 based on correctness, completeness, and accuracy
2. If the student's answer matches or closely matches the reference answer, give 90-100
3. If the answer covers most key points but misses some details, give 70-89
4. If the answer is partially correct, give 50-69
5. If the answer is mostly incorrect or incomplete, give below 50

**Required Output Format (JSON):**
{{
    "score": "<numeric score 0-100>",
    "evaluation": "<brief evaluation of the answer>",
    "justification": "<explain why this score was given>",
    "suggessions": "<suggestions for improvement>"
}}

Provide ONLY the JSON output, no additional text.'''

        message_list = [
            {"role": "user", "content": [{"text": prompt}]}
        ]

        system_list = [{"text": "You are an expert professor who evaluates student answers fairly and accurately. You provide scores from 0-100 based on correctness and completeness compared to the reference answer."}]

        inf_params = {"max_new_tokens": 5000, "top_p": 0.9, "top_k": 20, "temperature": 0.3}

        request_body = {
            "schemaVersion": "messages-v1",
            "messages": message_list,
            "system": system_list,
            "inferenceConfig": inf_params,
        }

        # Start time
        start_time = datetime.now()

        response = client.invoke_model_with_response_stream(
            modelId=LITE_MODEL_ID,
            body=json.dumps(request_body)
        )

        request_id = response.get("ResponseMetadata", {}).get("RequestId", "N/A")
        stream = response.get("body")

        if not stream:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': 'No response received.',
                    'request_id': request_id
                })
            }

        response_data = ""
        for event in stream:
            chunk = event.get("chunk")
            if chunk:
                chunk_json = json.loads(chunk.get("bytes").decode())
                content_block_delta = chunk_json.get("contentBlockDelta", {}).get("delta", {}).get("text", "")
                response_data += content_block_delta

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'text/html'},
            'body': response_data
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }