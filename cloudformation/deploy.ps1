# MSC Evaluate Quiz Application - Deployment Script (PowerShell)
# Region: ap-south-1
# This script deploys the complete infrastructure including:
# - S3 Static Website for Frontend
# - Lambda Functions for Backend
# - API Gateway with CORS enabled
# - DynamoDB Tables

$ErrorActionPreference = "Stop"

# Configuration
$REGION = "ap-south-1"
$ENVIRONMENT = "dev"
$STACK_NAME = "msc-evaluate-stack-$ENVIRONMENT"
$PROJECT_ROOT = Split-Path -Parent $PSScriptRoot

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "MSC Evaluate Deployment Script" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Region: $REGION"
Write-Host "Environment: $ENVIRONMENT"
Write-Host "Stack Name: $STACK_NAME"
Write-Host "Project Root: $PROJECT_ROOT"
Write-Host "==========================================" -ForegroundColor Cyan

# Step 1: Create CloudFormation Stack
Write-Host ""
Write-Host "Step 1: Creating/Updating CloudFormation Stack..." -ForegroundColor Yellow
aws cloudformation deploy `
  --template-file "$PROJECT_ROOT\cloudformation\deploy-stack.yaml" `
  --stack-name $STACK_NAME `
  --parameter-overrides Environment=$ENVIRONMENT `
  --capabilities CAPABILITY_NAMED_IAM `
  --region $REGION

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: CloudFormation stack deployment failed" -ForegroundColor Red
    exit 1
}

Write-Host "CloudFormation stack deployed successfully" -ForegroundColor Green

# Step 2: Get Stack Outputs
Write-Host ""
Write-Host "Step 2: Retrieving Stack Outputs..." -ForegroundColor Yellow

$FRONTEND_BUCKET = aws cloudformation describe-stacks `
  --stack-name $STACK_NAME `
  --region $REGION `
  --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" `
  --output text

$API_URL = aws cloudformation describe-stacks `
  --stack-name $STACK_NAME `
  --region $REGION `
  --query "Stacks[0].Outputs[?OutputKey=='ApiGatewayUrl'].OutputValue" `
  --output text

$WEBSITE_URL = aws cloudformation describe-stacks `
  --stack-name $STACK_NAME `
  --region $REGION `
  --query "Stacks[0].Outputs[?OutputKey=='FrontendWebsiteURL'].OutputValue" `
  --output text

$TEMPLATE_FUNCTION_ARN = aws cloudformation describe-stacks `
  --stack-name $STACK_NAME `
  --region $REGION `
  --query "Stacks[0].Outputs[?OutputKey=='TemplateApiFunctionArn'].OutputValue" `
  --output text

$TAKE_QUIZ_FUNCTION_ARN = aws cloudformation describe-stacks `
  --stack-name $STACK_NAME `
  --region $REGION `
  --query "Stacks[0].Outputs[?OutputKey=='TakeQuizFunctionArn'].OutputValue" `
  --output text

$SUBMIT_QUIZ_FUNCTION_ARN = aws cloudformation describe-stacks `
  --stack-name $STACK_NAME `
  --region $REGION `
  --query "Stacks[0].Outputs[?OutputKey=='SubmitQuizFunctionArn'].OutputValue" `
  --output text

$TEMPLATE_FUNCTION = $TEMPLATE_FUNCTION_ARN.Split(':')[-1]
$TAKE_QUIZ_FUNCTION = $TAKE_QUIZ_FUNCTION_ARN.Split(':')[-1]
$SUBMIT_QUIZ_FUNCTION = $SUBMIT_QUIZ_FUNCTION_ARN.Split(':')[-1]

Write-Host "Frontend Bucket: $FRONTEND_BUCKET"
Write-Host "API URL: $API_URL"
Write-Host "Website URL: $WEBSITE_URL"

# Step 3: Package and Deploy Lambda Functions
Write-Host ""
Write-Host "Step 3: Packaging and Deploying Lambda Functions..." -ForegroundColor Yellow

# Create temporary directory for Lambda packages
$TEMP_DIR = New-Item -ItemType Directory -Path "$env:TEMP\msc-lambda-$(Get-Random)" -Force
Write-Host "Using temporary directory: $TEMP_DIR"

# Package Template API Lambda
Write-Host "Packaging Template API Lambda..."
Push-Location "$PROJECT_ROOT\backend\templates"
Compress-Archive -Path "template_api.py" -DestinationPath "$TEMP_DIR\template-api.zip" -Force
aws lambda update-function-code `
  --function-name $TEMPLATE_FUNCTION `
  --zip-file "fileb://$TEMP_DIR\template-api.zip" `
  --region $REGION | Out-Null
Write-Host "Template API Lambda deployed" -ForegroundColor Green
Pop-Location

# Package Take Quiz Lambda
Write-Host "Packaging Take Quiz Lambda..."
Push-Location "$PROJECT_ROOT\backend\quiz"
Compress-Archive -Path "take_quiz.py" -DestinationPath "$TEMP_DIR\take-quiz.zip" -Force
aws lambda update-function-code `
  --function-name $TAKE_QUIZ_FUNCTION `
  --zip-file "fileb://$TEMP_DIR\take-quiz.zip" `
  --region $REGION | Out-Null
Write-Host "Take Quiz Lambda deployed" -ForegroundColor Green

# Package Submit Quiz Lambda
Write-Host "Packaging Submit Quiz Lambda..."
Compress-Archive -Path "submit_quiz.py" -DestinationPath "$TEMP_DIR\submit-quiz.zip" -Force
aws lambda update-function-code `
  --function-name $SUBMIT_QUIZ_FUNCTION `
  --zip-file "fileb://$TEMP_DIR\submit-quiz.zip" `
  --region $REGION | Out-Null
Write-Host "Submit Quiz Lambda deployed" -ForegroundColor Green
Pop-Location

# Cleanup temp directory
Remove-Item -Path $TEMP_DIR -Recurse -Force

# Step 4: Build and Deploy Frontend
Write-Host ""
Write-Host "Step 4: Building and Deploying Frontend..." -ForegroundColor Yellow

# Update frontend .env with API URL
Push-Location "$PROJECT_ROOT\frontend"
"REACT_APP_API_URL=$API_URL" | Out-File -FilePath ".env" -Encoding utf8
Write-Host "Updated frontend .env file" -ForegroundColor Green

# Install dependencies and build
Write-Host "Installing frontend dependencies..."
npm install --silent

Write-Host "Building frontend..."
npm run build

# Deploy to S3
Write-Host "Deploying frontend to S3..."
aws s3 sync build/ "s3://$FRONTEND_BUCKET/" `
  --region $REGION `
  --delete `
  --cache-control "public, max-age=31536000" `
  --exclude "index.html"

# Upload index.html with no-cache
aws s3 cp build/index.html "s3://$FRONTEND_BUCKET/index.html" `
  --region $REGION `
  --cache-control "no-cache, no-store, must-revalidate"

Write-Host "Frontend deployed to S3" -ForegroundColor Green
Pop-Location

# Step 5: Display Deployment Summary
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Frontend URL: $WEBSITE_URL" -ForegroundColor Yellow
Write-Host "API Gateway URL: $API_URL" -ForegroundColor Yellow
Write-Host ""
Write-Host "API Endpoints:"
Write-Host "  POST   $API_URL/templates"
Write-Host "  GET    $API_URL/templates"
Write-Host "  GET    $API_URL/templates/{template_id}/quiz"
Write-Host "  POST   $API_URL/submit"
Write-Host ""
Write-Host "All endpoints have CORS enabled with Access-Control-Allow-Origin: *" -ForegroundColor Green
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
