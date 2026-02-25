# MSC Evaluate Lambda Function

This Lambda function evaluates student answers using Amazon Bedrock (Nova Micro model).

## Features

- Evaluates text answers against example answers
- Extracts text from PDF files and evaluates them
- Returns detailed evaluation with score, justification, and suggestions
- Uses Amazon Bedrock for AI-powered evaluation

## Input Format

```json
{
  "user_answer": "Student's text answer (optional if pdf_data provided)",
  "pdf_data": "Base64 encoded PDF file (optional if user_answer provided)",
  "example_answer": "Reference answer for comparison"
}
```

## Output Format

```json
{
  "statusCode": 200,
  "headers": {
    "Content-Type": "text/html"
  },
  "body": "{\"score\": \"85/100\", \"evaluation\": \"...\", \"justification\": \"...\", \"suggessions\": \"...\"}"
}
```

## Dependencies

- boto3: AWS SDK for Python
- PyPDF2: PDF text extraction library

Install dependencies:
```bash
pip install -r requirements.txt
```

## Deployment

The function is deployed as part of the CloudFormation stack. Dependencies are packaged with the function code.

```powershell
# Package and deploy
$tempDir = New-Item -ItemType Directory -Path "$env:TEMP\msc-lambda-$(Get-Random)" -Force
$packageDir = New-Item -ItemType Directory -Path "$tempDir\package" -Force
pip install -r requirements.txt -t $packageDir --quiet
Copy-Item lambda_function.py -Destination $packageDir
Push-Location $packageDir
Compress-Archive -Path * -DestinationPath "$tempDir\msc-evaluate.zip" -Force
Pop-Location
aws lambda update-function-code --function-name msc-evaluate-function-dev --zip-file "fileb://$tempDir\msc-evaluate.zip" --region ap-south-1
Remove-Item -Path $tempDir -Recurse -Force
```

## Configuration

- Runtime: Python 3.11
- Timeout: 300 seconds (5 minutes)
- Memory: 512 MB
- Region: us-east-1 (for Bedrock access)

## IAM Permissions Required

- bedrock:InvokeModel
- bedrock:InvokeModelWithResponseStream
- logs:CreateLogGroup
- logs:CreateLogStream
- logs:PutLogEvents

## PDF Processing

The function uses PyPDF2 to extract text from uploaded PDF files:

1. Decodes base64 PDF data
2. Extracts text from all pages
3. Passes extracted text to Bedrock for evaluation

Maximum PDF size: 5MB (enforced by frontend)

## Error Handling

- Returns 400 for PDF processing errors
- Returns 400 for missing answers
- Returns 500 for unexpected errors
- All errors include descriptive messages
