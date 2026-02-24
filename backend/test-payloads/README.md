# Lambda API Test Payloads

This directory contains test payloads for all Lambda API endpoints.

## Files

- `template-api-payloads.json` - Test payloads for Template API (create, get, list templates)
- `take-quiz-payloads.json` - Test payloads for Take Quiz API
- `submit-quiz-payloads.json` - Test payloads for Submit Quiz API

## How to Use

### Option 1: AWS Lambda Console

1. Go to AWS Lambda Console
2. Select your Lambda function
3. Click "Test" tab
4. Create a new test event
5. Copy the `event` object from the payload file
6. Run the test

### Option 2: AWS CLI

```bash
# Invoke Lambda with payload
aws lambda invoke \
  --function-name your-function-name \
  --payload file://path/to/payload.json \
  response.json

# View response
cat response.json
```

### Option 3: Python Script

```python
import json
import boto3

# Load payload
with open('template-api-payloads.json') as f:
    payloads = json.load(f)

# Get specific test case
event = payloads['CREATE_TEMPLATE']['event']

# Invoke Lambda
lambda_client = boto3.client('lambda')
response = lambda_client.invoke(
    FunctionName='your-function-name',
    Payload=json.dumps(event)
)

# Read response
result = json.loads(response['Payload'].read())
print(json.dumps(result, indent=2))
```

## Test Workflow

### 1. Template API Tests

Run tests in this order:

1. **CREATE_TEMPLATE** - Create a new template and save the returned `template_id`
2. **GET_ALL_TEMPLATES** - Verify template appears in list
3. **GET_TEMPLATE_BY_ID** - Replace `TEMPLATE_ID` with actual ID from step 1
4. **GET_TEMPLATES_BY_SUBJECT** - Test filtering
5. **GET_TEMPLATES_BY_COURSE** - Test filtering
6. **CREATE_TEMPLATE_VALIDATION_ERROR_NO_TITLE** - Test validation
7. **CREATE_TEMPLATE_VALIDATION_ERROR_INSUFFICIENT_OPTIONS** - Test validation

### 2. Take Quiz API Tests

1. Use a valid `template_id` from Template API tests
2. **TAKE_QUIZ_SUCCESS** - Replace `TEMPLATE_ID` with actual ID
3. Verify that `correct_answer` field is NOT present in questions
4. **TAKE_QUIZ_NOT_FOUND** - Test error handling

### 3. Submit Quiz API Tests

1. Use a valid `template_id` from Template API tests
2. Get the quiz structure from Take Quiz API to know question count
3. **SUBMIT_QUIZ_SUCCESS_WITH_SESSION** - Replace `TEMPLATE_ID` and adjust answers array
4. **SUBMIT_QUIZ_PERFECT_SCORE** - Adjust `selected_answer` to match correct answers
5. **SUBMIT_QUIZ_ZERO_SCORE** - Use wrong answers
6. Test validation errors with remaining payloads

## Important Notes

### Template ID Replacement

Many payloads contain `TEMPLATE_ID` placeholder. Replace with actual template ID:

```json
// Before
"template_id": "TEMPLATE_ID"

// After (example)
"template_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

### Answer Array Structure

For submit quiz payloads, ensure the answers array matches your template:

```json
{
  "answers": [
    {"question_index": 0, "selected_answer": 1},  // First question, option index 1
    {"question_index": 1, "selected_answer": 2},  // Second question, option index 2
    {"question_index": 2, "selected_answer": 0}   // Third question, option index 0
  ]
}
```

- `question_index`: 0-based index of the question
- `selected_answer`: 0-based index of the selected option

### Expected Responses

Each payload includes `expected_response` to help verify results:

- `statusCode`: Expected HTTP status code
- `body_contains`: Array of strings that should appear in response body
- `body_should_not_contain`: Array of strings that should NOT appear in response body

## Example: Complete Test Flow

```bash
# 1. Create a template
aws lambda invoke \
  --function-name template-api \
  --payload '{"httpMethod":"POST","path":"/templates","body":"{\"title\":\"Test Quiz\",\"subject\":\"Math\",\"course\":\"Algebra\",\"questions\":[{\"question_text\":\"What is 2+2?\",\"options\":[\"3\",\"4\",\"5\"],\"correct_answer\":1}]}"}' \
  response.json

# Extract template_id from response
TEMPLATE_ID=$(cat response.json | jq -r '.body | fromjson | .template_id')
echo "Template ID: $TEMPLATE_ID"

# 2. Take the quiz
aws lambda invoke \
  --function-name take-quiz \
  --payload "{\"httpMethod\":\"GET\",\"path\":\"/quiz/$TEMPLATE_ID\",\"pathParameters\":{\"templateId\":\"$TEMPLATE_ID\"}}" \
  quiz-response.json

# 3. Submit quiz answers
aws lambda invoke \
  --function-name submit-quiz \
  --payload "{\"httpMethod\":\"POST\",\"path\":\"/quiz/submit\",\"body\":\"{\\\"template_id\\\":\\\"$TEMPLATE_ID\\\",\\\"session_id\\\":\\\"test-123\\\",\\\"answers\\\":[{\\\"question_index\\\":0,\\\"selected_answer\\\":1}]}\"}" \
  submit-response.json
```

## Troubleshooting

### Common Issues

1. **Template not found**: Ensure you're using a valid template_id
2. **All questions must be answered**: Ensure answers array has entries for all questions (0 to n-1)
3. **Invalid question_index**: Ensure question_index values are within valid range
4. **Invalid JSON**: Check that body string is properly escaped JSON

### Debugging Tips

- Check CloudWatch Logs for detailed error messages
- Verify DynamoDB table names match your environment
- Ensure Lambda has proper IAM permissions for DynamoDB access
- Test with simple payloads first, then add complexity
