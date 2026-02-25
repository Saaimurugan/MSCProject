#!/bin/bash

# MSC Evaluate Quiz Application - Deployment Script
# Region: ap-south-1
# This script deploys the complete infrastructure including:
# - S3 Static Website for Frontend
# - Lambda Functions for Backend
# - API Gateway with CORS enabled
# - DynamoDB Tables

set -e

# Configuration
REGION="ap-south-1"
ENVIRONMENT="dev"
STACK_NAME="msc-evaluate-stack-${ENVIRONMENT}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=========================================="
echo "MSC Evaluate Deployment Script"
echo "=========================================="
echo "Region: ${REGION}"
echo "Environment: ${ENVIRONMENT}"
echo "Stack Name: ${STACK_NAME}"
echo "Project Root: ${PROJECT_ROOT}"
echo "=========================================="

# Step 1: Create CloudFormation Stack
echo ""
echo "Step 1: Creating/Updating CloudFormation Stack..."
aws cloudformation deploy \
  --template-file "${PROJECT_ROOT}/cloudformation/deploy-stack.yaml" \
  --stack-name "${STACK_NAME}" \
  --parameter-overrides Environment="${ENVIRONMENT}" \
  --capabilities CAPABILITY_NAMED_IAM \
  --region "${REGION}"

if [ $? -ne 0 ]; then
  echo "ERROR: CloudFormation stack deployment failed"
  exit 1
fi

echo "✓ CloudFormation stack deployed successfully"

# Step 2: Get Stack Outputs
echo ""
echo "Step 2: Retrieving Stack Outputs..."
FRONTEND_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" \
  --output text)

API_URL=$(aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --query "Stacks[0].Outputs[?OutputKey=='ApiGatewayUrl'].OutputValue" \
  --output text)

WEBSITE_URL=$(aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendWebsiteURL'].OutputValue" \
  --output text)

TEMPLATE_FUNCTION=$(aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --query "Stacks[0].Outputs[?OutputKey=='TemplateApiFunctionArn'].OutputValue" \
  --output text | awk -F: '{print $NF}')

TAKE_QUIZ_FUNCTION=$(aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --query "Stacks[0].Outputs[?OutputKey=='TakeQuizFunctionArn'].OutputValue" \
  --output text | awk -F: '{print $NF}')

SUBMIT_QUIZ_FUNCTION=$(aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --query "Stacks[0].Outputs[?OutputKey=='SubmitQuizFunctionArn'].OutputValue" \
  --output text | awk -F: '{print $NF}')

echo "Frontend Bucket: ${FRONTEND_BUCKET}"
echo "API URL: ${API_URL}"
echo "Website URL: ${WEBSITE_URL}"

# Step 3: Package and Deploy Lambda Functions
echo ""
echo "Step 3: Packaging and Deploying Lambda Functions..."

# Create temporary directory for Lambda packages
TEMP_DIR=$(mktemp -d)
echo "Using temporary directory: ${TEMP_DIR}"

# Package Template API Lambda
echo "Packaging Template API Lambda..."
cd "${PROJECT_ROOT}/backend/templates"
zip -q "${TEMP_DIR}/template-api.zip" template_api.py
aws lambda update-function-code \
  --function-name "${TEMPLATE_FUNCTION}" \
  --zip-file "fileb://${TEMP_DIR}/template-api.zip" \
  --region "${REGION}" > /dev/null
echo "✓ Template API Lambda deployed"

# Package Take Quiz Lambda
echo "Packaging Take Quiz Lambda..."
cd "${PROJECT_ROOT}/backend/quiz"
zip -q "${TEMP_DIR}/take-quiz.zip" take_quiz.py
aws lambda update-function-code \
  --function-name "${TAKE_QUIZ_FUNCTION}" \
  --zip-file "fileb://${TEMP_DIR}/take-quiz.zip" \
  --region "${REGION}" > /dev/null
echo "✓ Take Quiz Lambda deployed"

# Package Submit Quiz Lambda
echo "Packaging Submit Quiz Lambda..."
zip -q "${TEMP_DIR}/submit-quiz.zip" submit_quiz.py
aws lambda update-function-code \
  --function-name "${SUBMIT_QUIZ_FUNCTION}" \
  --zip-file "fileb://${TEMP_DIR}/submit-quiz.zip" \
  --region "${REGION}" > /dev/null
echo "✓ Submit Quiz Lambda deployed"

# Cleanup temp directory
rm -rf "${TEMP_DIR}"

# Step 4: Build and Deploy Frontend
echo ""
echo "Step 4: Building and Deploying Frontend..."

# Update frontend .env with API URL
cd "${PROJECT_ROOT}/frontend"
echo "REACT_APP_API_URL=${API_URL}" > .env
echo "✓ Updated frontend .env file"

# Install dependencies and build
echo "Installing frontend dependencies..."
npm install --silent

echo "Building frontend..."
npm run build

# Deploy to S3
echo "Deploying frontend to S3..."
aws s3 sync build/ "s3://${FRONTEND_BUCKET}/" \
  --region "${REGION}" \
  --delete \
  --cache-control "public, max-age=31536000" \
  --exclude "index.html"

# Upload index.html with no-cache
aws s3 cp build/index.html "s3://${FRONTEND_BUCKET}/index.html" \
  --region "${REGION}" \
  --cache-control "no-cache, no-store, must-revalidate"

echo "✓ Frontend deployed to S3"

# Step 5: Display Deployment Summary
echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Frontend URL: ${WEBSITE_URL}"
echo "API Gateway URL: ${API_URL}"
echo ""
echo "API Endpoints:"
echo "  POST   ${API_URL}/templates"
echo "  GET    ${API_URL}/templates"
echo "  GET    ${API_URL}/templates/{template_id}/quiz"
echo "  POST   ${API_URL}/submit"
echo ""
echo "All endpoints have CORS enabled with Access-Control-Allow-Origin: *"
echo ""
echo "=========================================="
