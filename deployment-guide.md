# MSC Evaluate - Deployment Guide

## Architecture Overview
- **Frontend**: React app hosted on S3 with CloudFront
- **Backend**: Lambda functions with API Gateway
- **Database**: DynamoDB tables
- **Authentication**: JWT tokens
- **AI Scoring**: AWS Bedrock (Nova model)

## Prerequisites
- AWS CLI configured with appropriate permissions
- Node.js 18+ for React development
- Python 3.9+ for Lambda functions

## Deployment Steps

### 1. Deploy DynamoDB Tables
```bash
aws cloudformation deploy \
  --template-file infrastructure/dynamodb-tables.yaml \
  --stack-name msc-evaluate-db \
  --region us-east-1
```

### 2. Create Lambda Deployment Packages
```bash
# Create deployment packages for each Lambda function
cd backend

# Auth functions
zip -r auth-login.zip auth/login.py shared/
zip -r auth-signup.zip auth/signup.py shared/

# Template functions  
zip -r templates-create.zip templates/create_template.py shared/
zip -r templates-get.zip templates/get_templates.py shared/

# Quiz functions
zip -r quiz-take.zip quiz/take_quiz.py shared/
zip -r quiz-submit.zip quiz/submit_quiz.py shared/
```

### 3. Deploy Lambda Functions
```bash
# Create Lambda functions (example for login function)
aws lambda create-function \
  --function-name msc-evaluate-auth-login \
  --runtime python3.9 \
  --role arn:aws:iam::YOUR-ACCOUNT:role/lambda-execution-role \
  --handler login.lambda_handler \
  --zip-file fileb://auth-login.zip \
  --timeout 30 \
  --memory-size 256

# Repeat for all functions...
```

### 4. Create API Gateway
```bash
# Create REST API
aws apigateway create-rest-api \
  --name msc-evaluate-api \
  --description "MSC Evaluate API"

# Configure resources and methods
# /auth/login (POST)
# /auth/signup (POST)
# /templates (GET, POST)
# /templates/{id} (GET, PUT, DELETE)
# /quiz/{templateId} (GET)
# /quiz/submit (POST)
```

### 5. Build and Deploy React Frontend
```bash
cd frontend

# Install dependencies
npm install

# Set environment variables
echo "REACT_APP_API_URL=https://your-api-gateway-url.amazonaws.com/dev" > .env

# Build for production
npm run build

# Deploy to S3
aws s3 sync build/ s3://your-frontend-bucket --delete

# Configure CloudFront distribution for the S3 bucket
```

### 6. Configure IAM Roles

#### Lambda Execution Role
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Scan",
        "dynamodb:Query"
      ],
      "Resource": [
        "arn:aws:dynamodb:us-east-1:*:table/msc-users",
        "arn:aws:dynamodb:us-east-1:*:table/msc-templates",
        "arn:aws:dynamodb:us-east-1:*:table/msc-quiz-results",
        "arn:aws:dynamodb:us-east-1:*:table/msc-users/index/*",
        "arn:aws:dynamodb:us-east-1:*:table/msc-templates/index/*",
        "arn:aws:dynamodb:us-east-1:*:table/msc-quiz-results/index/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-micro-v1:0"
    }
  ]
}
```

## Environment Variables

### Lambda Functions
- `JWT_SECRET`: Secret key for JWT token signing
- `DYNAMODB_REGION`: AWS region for DynamoDB (us-east-1)

### React App
- `REACT_APP_API_URL`: API Gateway endpoint URL

## Testing the Deployment

### 1. Test Authentication
```bash
# Test signup
curl -X POST https://your-api-url/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123","name":"Test User","role":"student"}'

# Test login
curl -X POST https://your-api-url/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

### 2. Test Template Creation (Admin/Tutor)
```bash
curl -X POST https://your-api-url/templates \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR-JWT-TOKEN" \
  -d '{
    "title": "Sample Quiz",
    "subject": "Computer Science",
    "course": "MSC-101",
    "questions": [
      {
        "question": "What is Machine Learning?",
        "example_answer": "Machine learning is a subset of AI..."
      }
    ]
  }'
```

## Security Considerations

1. **JWT Secret**: Store in AWS Secrets Manager in production
2. **CORS**: Configure API Gateway CORS for your frontend domain
3. **Rate Limiting**: Implement API Gateway throttling
4. **Input Validation**: Add comprehensive input validation
5. **HTTPS**: Ensure all communications use HTTPS
6. **Database**: Enable encryption at rest for DynamoDB

## Monitoring and Logging

1. **CloudWatch**: Monitor Lambda function logs and metrics
2. **X-Ray**: Enable tracing for debugging
3. **API Gateway**: Monitor API usage and errors
4. **DynamoDB**: Monitor read/write capacity and throttling

## Cost Optimization

1. **Lambda**: Use appropriate memory allocation
2. **DynamoDB**: Use on-demand billing for variable workloads
3. **S3**: Use appropriate storage class for static assets
4. **CloudFront**: Cache static assets effectively