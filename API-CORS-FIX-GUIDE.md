# API CORS and Network Errors - Fix Guide

## Current Issues
Based on the browser console errors:
1. CORS errors on `/users` endpoint
2. 404 error on `/dashboard` endpoint (doesn't exist - this is expected)
3. Network errors on `/templates` endpoint

## Root Cause
The Lambda functions may not be deployed with the latest code, or the API Gateway needs to be redeployed.

## Solution Steps

### Step 1: Verify API Gateway Deployment
```powershell
# Check if the stack is deployed
aws cloudformation describe-stacks --stack-name msc-evaluate-stack-dev --region ap-south-1

# Get the API Gateway ID
aws cloudformation describe-stack-resources --stack-name msc-evaluate-stack-dev --region ap-south-1 --query "StackResources[?ResourceType=='AWS::ApiGateway::RestApi'].PhysicalResourceId" --output text
```

### Step 2: Update Lambda Functions
The Lambda functions need to be updated with the actual code (they currently have placeholder code).

```powershell
# Navigate to backend directory
cd backend

# Update User CRUD Lambda
cd users
Compress-Archive -Path user_crud.py -DestinationPath user_crud.zip -Force
aws lambda update-function-code --function-name msc-evaluate-user-crud-dev --zip-file fileb://user_crud.zip --region ap-south-1
cd ..

# Update Template API Lambda
cd templates
Compress-Archive -Path template_api.py -DestinationPath template_api.zip -Force
aws lambda update-function-code --function-name msc-evaluate-template-api-dev --zip-file fileb://template_api.zip --region ap-south-1
cd ..

# Update Quiz Lambdas
cd quiz
Compress-Archive -Path take_quiz.py -DestinationPath take_quiz.zip -Force
aws lambda update-function-code --function-name msc-evaluate-take-quiz-dev --zip-file fileb://take_quiz.zip --region ap-south-1

Compress-Archive -Path submit_quiz.py -DestinationPath submit_quiz.zip -Force
aws lambda update-function-code --function-name msc-evaluate-submit-quiz-dev --zip-file fileb://submit_quiz.zip --region ap-south-1

Compress-Archive -Path get_results.py -DestinationPath get_results.zip -Force
aws lambda update-function-code --function-name msc-evaluate-get-results-dev --zip-file fileb://get_results.zip --region ap-south-1

Compress-Archive -Path delete_result.py -DestinationPath delete_result.zip -Force
aws lambda update-function-code --function-name msc-evaluate-delete-result-dev --zip-file fileb://delete_result.zip --region ap-south-1
cd ..

# Update MSC Evaluate Lambda
cd MSC_Evaluate
Compress-Archive -Path lambda_function.py -DestinationPath deployment.zip -Force
aws lambda update-function-code --function-name msc-evaluate-function-dev --zip-file fileb://deployment.zip --region ap-south-1
cd ..
```

### Step 3: Redeploy API Gateway
After updating Lambda functions, create a new API Gateway deployment:

```powershell
# Get API Gateway ID
$API_ID = aws cloudformation describe-stack-resources --stack-name msc-evaluate-stack-dev --region ap-south-1 --query "StackResources[?ResourceType=='AWS::ApiGateway::RestApi'].PhysicalResourceId" --output text

# Create new deployment
aws apigateway create-deployment --rest-api-id $API_ID --stage-name dev --region ap-south-1
```

### Step 4: Test the Endpoints
```powershell
# Test login endpoint
$API_URL = "https://48c11a5co1.execute-api.ap-south-1.amazonaws.com/dev"

# Test login
Invoke-RestMethod -Uri "$API_URL/users/login" -Method POST -Body '{"username":"admin","password":"admin123"}' -ContentType "application/json"

# Test templates (should work without auth)
Invoke-RestMethod -Uri "$API_URL/templates" -Method GET
```

### Step 5: Clear Browser Cache
After deploying:
1. Open browser DevTools (F12)
2. Right-click the refresh button
3. Select "Empty Cache and Hard Reload"
4. Or use Ctrl+Shift+Delete to clear cache

## Quick Fix Script
Run this PowerShell script to update all Lambda functions at once:

```powershell
# Save this as update-lambdas.ps1
$region = "ap-south-1"
$env = "dev"

Write-Host "Updating Lambda functions..." -ForegroundColor Green

# User CRUD
Write-Host "Updating user-crud..." -ForegroundColor Yellow
cd backend/users
Compress-Archive -Path user_crud.py -DestinationPath user_crud.zip -Force
aws lambda update-function-code --function-name "msc-evaluate-user-crud-$env" --zip-file fileb://user_crud.zip --region $region
cd ../..

# Template API
Write-Host "Updating template-api..." -ForegroundColor Yellow
cd backend/templates
Compress-Archive -Path template_api.py -DestinationPath template_api.zip -Force
aws lambda update-function-code --function-name "msc-evaluate-template-api-$env" --zip-file fileb://template_api.zip --region $region
cd ../..

Write-Host "Lambda functions updated!" -ForegroundColor Green
Write-Host "Now redeploying API Gateway..." -ForegroundColor Green

# Redeploy API Gateway
$API_ID = aws cloudformation describe-stack-resources --stack-name "msc-evaluate-stack-$env" --region $region --query "StackResources[?ResourceType=='AWS::ApiGateway::RestApi'].PhysicalResourceId" --output text
aws apigateway create-deployment --rest-api-id $API_ID --stage-name $env --region $region

Write-Host "Done! Clear your browser cache and try again." -ForegroundColor Green
```

## Alternative: Use the Deployment Script
The existing deployment script should handle this:

```powershell
cd cloudformation
.\deploy.ps1
```

## Verification Checklist
- [ ] Lambda functions updated with actual code (not placeholders)
- [ ] API Gateway redeployed
- [ ] Browser cache cleared
- [ ] Login endpoint returns 200 OK
- [ ] Templates endpoint returns data
- [ ] No CORS errors in console

## Common Issues

### Issue: Still getting CORS errors
**Solution**: Make sure the Lambda functions are returning CORS headers in ALL responses, including errors.

### Issue: 404 errors
**Solution**: The API Gateway routes might not be properly configured. Check the CloudFormation stack.

### Issue: Network errors
**Solution**: Lambda functions might be timing out or throwing errors. Check CloudWatch Logs:
```powershell
aws logs tail /aws/lambda/msc-evaluate-user-crud-dev --follow --region ap-south-1
```

## Next Steps
After fixing the API issues:
1. Test login with admin/admin123
2. Verify templates load on dashboard
3. Test creating a new template
4. Test taking a quiz
