# PDF Upload Feature for Quiz Taking

## Overview

Added PDF upload functionality to the quiz taking page, allowing students to submit answers as either text or PDF files. PDFs are processed using text extraction and evaluated using Amazon Bedrock AI.

## Changes Made

### Frontend Changes

#### 1. QuizTaking Component (`frontend/src/components/quiz/QuizTaking.js`)
- Added `pdfFiles` state to track uploaded PDFs per question
- Added `handlePdfUpload()` function with validation (PDF type, 5MB max size)
- Added `removePdf()` function to clear uploaded PDFs
- Updated `handleAnswerChange()` to clear PDF when text is entered
- Updated `submitQuiz()` to convert PDFs to base64 and include in submission
- Added `fileToBase64()` helper function
- Replaced MCQ radio buttons with:
  - Textarea for text answers
  - PDF upload button with file input
  - Visual indicator for uploaded PDFs
  - Example answer display (if available)
- Updated answer validation to check for either text or PDF

#### 2. Quiz CSS (`frontend/src/components/quiz/Quiz.css`)
- Added styles for elaborate answer textarea
- Added PDF upload section styles with divider
- Added uploaded PDF display styles with remove button
- Added example answer hint styles
- Added elaborate answer results styles with evaluation sections

#### 3. QuizResults Component (`frontend/src/components/quiz/QuizResults.js`)
- Updated to display `average_score` instead of `total_score`
- Updated to show `evaluations` instead of `detailed_results`
- Added display for:
  - User's answer (text or PDF filename)
  - Example answer
  - AI evaluation
  - Justification
  - Suggestions for improvement
- Removed correct/incorrect badges (replaced with score badges)

### Backend Changes

#### 1. MSC_Evaluate Lambda (`backend/MSC_Evaluate/lambda_function.py`)
- Added PyPDF2 import for PDF text extraction
- Added `extract_text_from_pdf()` function to extract text from base64 PDFs
- Updated `lambda_handler()` to accept `pdf_data` parameter
- Added PDF processing logic before Bedrock evaluation
- Added validation for missing answers
- Increased timeout to 300 seconds
- Increased memory to 512 MB

#### 2. Submit Quiz Lambda (`backend/quiz/submit_quiz.py`)
- Added Lambda client for invoking MSC_Evaluate function
- Added `evaluate_answer()` function to call MSC_Evaluate
- Updated answer format to include:
  - `answer_text`: Text answer
  - `pdf_data`: Base64 encoded PDF
  - `pdf_filename`: Original filename
- Updated evaluation logic to:
  - Call MSC_Evaluate for each answer
  - Parse evaluation response (score, evaluation, justification, suggestions)
  - Calculate average score across all questions
- Updated database schema to store evaluations instead of correct/incorrect
- Updated response format to include detailed evaluations

#### 3. Requirements (`backend/MSC_Evaluate/requirements.txt`)
- Added PyPDF2>=3.0.0 for PDF text extraction
- Added boto3>=1.26.0

### Infrastructure Changes

#### 1. CloudFormation Template (`cloudformation/deploy-stack.yaml`)
- Added `MSCEvaluateFunction` Lambda resource
- Added IAM permissions for:
  - Lambda invocation (submit_quiz → MSC_Evaluate)
  - Bedrock model access
- Updated Lambda execution role with Bedrock permissions

#### 2. Deployment Script (`cloudformation/deploy.ps1`)
- Added MSC_Evaluate Lambda packaging with PyPDF2 dependencies
- Added pip install step for requirements.txt
- Added deployment step for MSC_Evaluate function

### Documentation

#### 1. Test Payloads (`backend/test-payloads/submit-quiz-payloads.json`)
- Updated with new answer format examples
- Added examples for text answers, PDF answers, and mixed answers
- Removed old MCQ-based examples

#### 2. MSC_Evaluate README (`backend/MSC_Evaluate/README.md`)
- Created comprehensive documentation for the Lambda function
- Documented input/output formats
- Documented deployment process
- Documented PDF processing details

## API Changes

### Submit Quiz Endpoint

**Old Format (MCQ):**
```json
{
  "template_id": "xxx",
  "answers": [
    {
      "question_index": 0,
      "selected_answer": 1
    }
  ]
}
```

**New Format (Elaborate):**
```json
{
  "template_id": "xxx",
  "answers": [
    {
      "question_index": 0,
      "answer_text": "My detailed answer...",
      "pdf_data": null,
      "pdf_filename": null
    },
    {
      "question_index": 1,
      "answer_text": "",
      "pdf_data": "BASE64_ENCODED_PDF",
      "pdf_filename": "answer.pdf"
    }
  ]
}
```

**Old Response:**
```json
{
  "result_id": "xxx",
  "total_score": 85.5,
  "correct_count": 3,
  "total_questions": 4,
  "detailed_results": [...]
}
```

**New Response:**
```json
{
  "result_id": "xxx",
  "average_score": 82.5,
  "total_questions": 2,
  "evaluations": [
    {
      "question_index": 0,
      "score": "85/100",
      "evaluation": "Good understanding...",
      "justification": "The answer covers...",
      "suggessions": "Consider adding...",
      "user_answer": "My detailed answer..."
    }
  ]
}
```

## User Experience

### Quiz Taking Flow

1. Student navigates to quiz
2. For each question:
   - Student can type answer in textarea OR
   - Student can upload PDF (max 5MB)
   - Only one input method allowed per question
   - Example answer shown as reference (if available)
3. Navigation dots show answered questions (green)
4. Submit button validates all questions answered
5. Results page shows:
   - Average score percentage
   - Detailed evaluation for each answer
   - AI-generated feedback and suggestions

### Validation

- PDF files must be application/pdf type
- PDF files must be under 5MB
- All questions must be answered (text or PDF)
- Cannot submit both text and PDF for same question

## Technical Details

### PDF Processing

1. Frontend converts PDF to base64 using FileReader API
2. Base64 data sent to backend in answer payload
3. MSC_Evaluate Lambda decodes base64 to bytes
4. PyPDF2 extracts text from all pages
5. Extracted text evaluated by Bedrock AI

### AI Evaluation

- Model: Amazon Nova Micro (amazon.nova-micro-v1:0)
- Region: us-east-1
- Streaming response for better performance
- Evaluation includes:
  - Numeric score
  - Detailed evaluation text
  - Justification for score
  - Suggestions for improvement

### Performance

- MSC_Evaluate timeout: 300 seconds (5 minutes)
- MSC_Evaluate memory: 512 MB
- Submit Quiz timeout: 30 seconds
- Frontend upload limit: 5MB per PDF

## Deployment

### Prerequisites

- Python 3.11
- pip
- AWS CLI configured
- CloudFormation stack deployed

### Deploy Commands

```powershell
# Update CloudFormation stack
cd cloudformation
aws cloudformation update-stack --stack-name msc-evaluate-stack-dev --template-body file://deploy-stack.yaml --parameters ParameterKey=Environment,ParameterValue=dev --capabilities CAPABILITY_NAMED_IAM --region ap-south-1

# Wait for stack update
aws cloudformation wait stack-update-complete --stack-name msc-evaluate-stack-dev --region ap-south-1

# Deploy MSC_Evaluate Lambda
cd ../backend/MSC_Evaluate
$tempDir = New-Item -ItemType Directory -Path "$env:TEMP\msc-lambda-$(Get-Random)" -Force
$packageDir = New-Item -ItemType Directory -Path "$tempDir\package" -Force
pip install -r requirements.txt -t $packageDir --quiet
Copy-Item lambda_function.py -Destination $packageDir
Push-Location $packageDir
Compress-Archive -Path * -DestinationPath "$tempDir\msc-evaluate.zip" -Force
Pop-Location
aws lambda update-function-code --function-name msc-evaluate-function-dev --zip-file "fileb://$tempDir\msc-evaluate.zip" --region ap-south-1
Remove-Item -Path $tempDir -Recurse -Force

# Deploy Submit Quiz Lambda
cd ../quiz
$tempDir = New-Item -ItemType Directory -Path "$env:TEMP\msc-lambda-$(Get-Random)" -Force
Compress-Archive -Path submit_quiz.py -DestinationPath "$tempDir\submit-quiz.zip" -Force
aws lambda update-function-code --function-name msc-evaluate-submit-quiz-dev --zip-file "fileb://$tempDir\submit-quiz.zip" --region ap-south-1
Remove-Item -Path $tempDir -Recurse -Force

# Build and deploy frontend
cd ../../frontend
npm run build
aws s3 sync build/ s3://msc-evaluate-frontend-dev --delete --region ap-south-1
```

## Testing

### Manual Testing

1. Create a template with elaborate questions
2. Take the quiz
3. Test text answer submission
4. Test PDF answer submission
5. Test mixed text and PDF answers
6. Verify results page shows evaluations
7. Verify AI feedback is displayed

### Test PDFs

Create simple test PDFs with text content to verify extraction works correctly.

## Future Enhancements

- Support for other file formats (DOCX, TXT)
- Image-based answer evaluation
- Plagiarism detection
- Answer comparison across students
- Batch PDF processing
- PDF preview before submission
- Answer history and revisions
