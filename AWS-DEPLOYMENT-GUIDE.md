# MSC Evaluate - AWS Deployment Guide

## 🚀 Complete Step-by-Step AWS Deployment

This guide will walk you through deploying the MSC Evaluate application on AWS from scratch.

## 📋 Prerequisites

### 1. AWS Account Setup
- Create an AWS account at https://aws.amazon.com
- Ensure you have billing enabled
- Note your AWS Account ID

### 2. Install Required Tools

#### AWS CLI
```bash
# Windows (using installer)
# Download from: https://aws.amazon.com/cli/
# Or using chocolatey:
choco install awscli

# macOS
brew install awscli

# Linux (Ubuntu/Debian)
sudo apt update
sudo apt install awscli

# Verify installation
aws --version
```

#### Node.js (for React frontend)
```bash
# Download from: https://nodejs.org (LTS version)
# Or using package managers:

# Windows (chocolatey)
choco install nodejs

# macOS
brew install node

# Linux
sudo apt install nodejs npm

# Verify installation
node --version
npm --version
```

#### Python (for Lambda functions)
```bash
# Most systems have Python pre-installed
# Verify you have Python 3.9+
python --version
# or
python3 --version
```

### 3. Configure AWS CLI

```bash
# Configure AWS credentials
aws configure

# You'll be prompted for:
# AWS Access Key ID: [Your access key]
# AWS Secret Access Key: [Your secret key]
# Default region name: us-east-1
# Default output format: json
```

#### Getting AWS Credentials
1. Go to AWS Console → IAM → Users
2. Create a new user or select existing user
3. Attach policies:
   - `AdministratorAccess` (for full deployment)
   - Or create custom policy with required permissions
4. Create access keys in Security Credentials tab

## 🎯 Deployment Methods

### Method 1: Automated Deployment (Recommended)

#### Windows PowerShell
```powershell
# 1. Open PowerShell as Administrator
# 2. Navigate to your project directory
cd C:\path\to\msc-evaluate

# 3. Set execution policy (if needed)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 4. Run deployment script
.\deploy.ps1

# With custom options:
.\deploy.ps1 -Environment "prod" -Region "us-west-2" -ProjectName "my-quiz-app"
```

#### Linux/macOS
```bash
# 1. Open terminal
# 2. Navigate to your project directory
cd /path/to/msc-evaluate

# 3. Make script executable
chmod +x deploy.sh

# 4. Run deployment script
./deploy.sh

# With custom options:
./deploy.sh --environment prod --region us-west-2 --project my-quiz-app
```

### Method 2: Manual Step-by-Step Deployment

If you prefer to understand each step or need to customize the deployment:

#### Step 1: Deploy Infrastructure
```bash
# Deploy CloudFormation stack
aws cloudformation deploy \
  --template-file infrastructure/complete-infrastructure.yaml \
  --stack-name msc-evaluate-infrastructure-dev \
  --parameter-overrides \
    ProjectName=msc-evaluate \
    Environment=dev \
    JWTSecret=$(openssl rand -base64 48 | tr -d "=+/" | cut -c1-64) \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1

# Wait for completion (5-10 minutes)
aws cloudformation wait stack-create-complete \
  --stack-name msc-evaluate-infrastructure-dev \
  --region us-east-1
```

#### Step 2: Get Stack Outputs
```bash
# Get important URLs and resource names
aws cloudformation describe-stacks \
  --stack-name msc-evaluate-infrastructure-dev \
  --region us-east-1 \
  --query "Stacks[0].Outputs"
```

#### Step 3: Package and Deploy Lambda Functions
```bash
# Create temporary directory
mkdir temp-lambda-packages
cd temp-lambda-packages

# Package each function
zip -r auth-login.zip ../backend/auth/login.py ../backend/shared/
zip -r auth-signup.zip ../backend/auth/signup.py ../backend/shared/
zip -r templates-get.zip ../backend/templates/get_templates.py ../backend/shared/
zip -r templates-create.zip ../backend/templates/create_template.py ../backend/shared/
zip -r quiz-get.zip ../backend/quiz/take_quiz.py ../backend/shared/
zip -r quiz-submit.zip ../backend/quiz/submit_quiz.py ../backend/shared/

# Update Lambda functions
aws lambda update-function-code \
  --function-name msc-evaluate-auth-login-dev \
  --zip-file fileb://auth-login.zip \
  --region us-east-1

# Repeat for all functions...
```

#### Step 4: Build and Deploy Frontend
```bash
cd ../frontend

# Install dependencies
npm install

# Create environment file with API Gateway URL
echo "REACT_APP_API_URL=https://YOUR-API-GATEWAY-ID.execute-api.us-east-1.amazonaws.com/dev" > .env

# Build for production
npm run build

# Deploy to S3 (replace with your bucket name from stack outputs)
aws s3 sync build/ s3://YOUR-FRONTEND-BUCKET-NAME --delete --region us-east-1
```

## 🔧 Configuration

### Environment Variables

The deployment automatically sets these environment variables for Lambda functions:
- `JWT_SECRET`: Automatically generated secure key
- `USERS_TABLE`: msc-evaluate-users-dev
- `TEMPLATES_TABLE`: msc-evaluate-templates-dev
- `QUIZ_RESULTS_TABLE`: msc-evaluate-quiz-results-dev
- `ENVIRONMENT`: dev (or your specified environment)

### Frontend Configuration

The React app needs the API Gateway URL in `.env`:
```bash
REACT_APP_API_URL=https://your-api-gateway-id.execute-api.us-east-1.amazonaws.com/dev
```

## 🎯 Post-Deployment Steps

### 1. Verify Deployment
```bash
# Test API endpoints
curl -X POST https://your-api-url/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password123","name":"Admin User","role":"admin"}'
```

### 2. Access Your Application
- Frontend URL: `https://your-cloudfront-distribution.cloudfront.net`
- API URL: `https://your-api-gateway.execute-api.us-east-1.amazonaws.com/dev`

### 3. Create First Admin User
1. Go to your frontend URL
2. Click "Sign Up"
3. Create an admin account
4. Start creating quiz templates

## 🔍 Monitoring and Troubleshooting

### CloudWatch Logs
```bash
# View Lambda function logs
aws logs tail /aws/lambda/msc-evaluate-auth-login-dev --follow --region us-east-1

# View API Gateway logs
aws logs tail API-Gateway-Execution-Logs_YOUR-API-ID/dev --follow --region us-east-1
```

### Common Issues and Solutions

#### 1. Lambda Function Errors
```bash
# Check function logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/msc-evaluate" --region us-east-1

# View specific error logs
aws logs filter-log-events \
  --log-group-name "/aws/lambda/msc-evaluate-auth-login-dev" \
  --filter-pattern "ERROR" \
  --region us-east-1
```

#### 2. API Gateway CORS Issues
- Ensure CORS is enabled in API Gateway
- Check that frontend URL is allowed in CORS settings

#### 3. DynamoDB Access Issues
- Verify Lambda execution role has DynamoDB permissions
- Check table names match environment variables

#### 4. Frontend Not Loading
- Verify S3 bucket policy allows public read access
- Check CloudFront distribution status
- Ensure API URL is correctly set in .env

## 💰 Cost Estimation

### Monthly Costs (Approximate)
- **DynamoDB**: $0-25 (depending on usage)
- **Lambda**: $0-10 (first 1M requests free)
- **API Gateway**: $0-15 (first 1M requests free)
- **S3**: $1-5 (storage and requests)
- **CloudFront**: $0-10 (first 1TB free)

**Total estimated cost: $1-65/month** (mostly depends on usage)

## 🗑️ Cleanup

### Automated Cleanup
```bash
# Windows
.\destroy.ps1 -Force

# Linux/macOS
./destroy.sh --force
```

### Manual Cleanup
```bash
# Empty S3 bucket first
aws s3 rm s3://your-frontend-bucket --recursive --region us-east-1

# Delete CloudFormation stack
aws cloudformation delete-stack \
  --stack-name msc-evaluate-infrastructure-dev \
  --region us-east-1

# Wait for deletion
aws cloudformation wait stack-delete-complete \
  --stack-name msc-evaluate-infrastructure-dev \
  --region us-east-1
```

## 🔐 Security Best Practices

### 1. IAM Roles and Policies
- Use least privilege principle
- Separate roles for different environments
- Regular access key rotation

### 2. Environment Separation
```bash
# Deploy to different environments
./deploy.sh --environment staging
./deploy.sh --environment prod
```

### 3. Secrets Management
- Store JWT secrets in AWS Secrets Manager (production)
- Use environment-specific secrets
- Enable secret rotation

### 4. Network Security
- Enable WAF for API Gateway (production)
- Use VPC endpoints for DynamoDB access
- Enable CloudTrail for audit logging

## 📊 Scaling Considerations

### Auto Scaling
- DynamoDB: On-demand billing handles scaling automatically
- Lambda: Concurrent execution limits (default 1000)
- API Gateway: Built-in scaling

### Performance Optimization
- Enable DynamoDB DAX for caching
- Use Lambda provisioned concurrency for consistent performance
- Implement CloudFront caching strategies

## 🆘 Support and Resources

### AWS Documentation
- [Lambda Developer Guide](https://docs.aws.amazon.com/lambda/)
- [DynamoDB Developer Guide](https://docs.aws.amazon.com/dynamodb/)
- [API Gateway Developer Guide](https://docs.aws.amazon.com/apigateway/)

### Troubleshooting Resources
- AWS CloudWatch for monitoring
- AWS X-Ray for distributed tracing
- AWS Support (if you have a support plan)

---

**🎉 Congratulations! Your MSC Evaluate application is now running on AWS!**

Access your application and start creating quizzes for your students.