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

        # Construct the prompt to generate HTML JD
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
        "suggessions": "suggessions"
        '''

        message_list = [
            {"role": "user", "content": [{"text": prompt}]}
        ]

        system_list = [{"text": "You are a professor responsible for comparing a given response with the provided reference answer. Evaluate the response and assign a score."}]

        inf_params = {"max_new_tokens": 5000, "top_p": 0.9, "top_k": 20, "temperature": 0.9}

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