# CORS and Network Errors - Complete Resolution Guide

## Problem Summary
Your AI Assessment application is showing CORS and network errors in the browser console when trying to access the backend API endpoints.

## Error Analysis

### Errors Observed:
1. **CORS Error on `/users`**: Access blocked due to CORS policy
2. **404 Error on `/dashboard`**: Endpoint doesn't exist (expected - no such endpoint defined)
3. **Network Error on `/templates`**: Request failed before completion

### Root Causes:
1. Lambda functions may still have placeholder code from CloudFormation
2. API Gateway might need redeployment
3. Browser cache might be serving old responses

## Quick Fix (Recommended)

### Option 1: Run the Update Script
```powershell
# Run this from the project root directory
.\update-lambdas.ps1
```

This script will:
- Update all Lambda functions with the latest code
- Redeploy the API Gateway
- Verify the deployment

### Option 2: Use the Deployment Script
```powershell
cd cloudformation
.\deploy.ps1
```

This will redeploy the entire stack with updated Lambda code.

## Manual Fix Steps

If you prefer to do it manually:

### Step 1: Update Lambda Functions

```powershell
# User CRUD Lambda
cd backend\users
Compress-Archive -Path user_crud.py -DestinationPath user_crud.zip -Force
aws lambda update-function-code --function-name msc-evaluate-user-crud-dev --zip-file fileb://user_crud.zip --region ap-south-1

# Template API Lambda
cd ..\templates
Compress-Archive -Path template_api.py -DestinationPath template_api.zip -Force
aws lambda update-function-code --function-name msc-evaluate-template-api-dev --zip-file fileb://template_api.zip --region ap-south-1

# Quiz Lambdas
cd ..\quiz
Compress-Archive -Path take_quiz.py -DestinationPath take_quiz.zip -Force
aws lambda update-function-code --function-name msc-evaluate-take-quiz-dev --zip-file fileb://take_quiz.zip --region ap-south-1

Compress-Archive -Path submit_quiz.py -DestinationPath submit_quiz.zip -Force
aws lambda update-function-code --function-name msc-evaluate-submit-quiz-dev --zip-file fileb://submit_quiz.zip --region ap-south-1

Compress-Archive -Path get_results.py -DestinationPath get_results.zip -Force
aws lambda update-function-code --function-name msc-evaluate-get-results-dev --zip-file fileb://get_results.zip --region ap-south-1

Compress-Archive -Path delete_result.py -DestinationPath delete_result.zip -Force
aws lambda update-function-code --function-name msc-evaluate-delete-result-dev --zip-file fileb://delete_result.zip --region ap-south-1

cd ..\..
```

### Step 2: Redeploy API Gateway

```powershell
# Get API Gateway ID
$API_ID = aws cloudformation describe-stack-resources --stack-name msc-evaluate-stack-dev --region ap-south-1 --query "StackResources[?ResourceType=='AWS::ApiGateway::RestApi'].PhysicalResourceId" --output text

# Create new deployment
aws apigateway create-deployment --rest-api-id $API_ID --stage-name dev --region ap-south-1
```

### Step 3: Clear Browser Cache

1. Open DevTools (F12)
2. Right-click the refresh button
3. Select "Empty Cache and Hard Reload"
4. Or press Ctrl+Shift+Delete and clear cache

### Step 4: Test the API

```powershell
# Run the test script
.\test-api.ps1
```

Or test manually:
```powershell
# Test login
Invoke-RestMethod -Uri "https://48c11a5co1.execute-api.ap-south-1.amazonaws.com/dev/users/login" -Method POST -Body '{"username":"admin","password":"admin123"}' -ContentType "application/json"

# Test templates
Invoke-RestMethod -Uri "https://48c11a5co1.execute-api.ap-south-1.amazonaws.com/dev/templates" -Method GET
```

## Verification Checklist

After applying the fix:

- [ ] Run `.\update-lambdas.ps1` successfully
- [ ] Run `.\test-api.ps1` - all tests pass
- [ ] Clear browser cache
- [ ] Refresh the application
- [ ] Login works (admin/admin123)
- [ ] Dashboard loads without errors
- [ ] Templates are visible
- [ ] No CORS errors in console

## Understanding the CORS Configuration

### Backend (Lambda Functions)
All Lambda functions return CORS headers:
```python
def cors_headers():
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-User-Role',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    }
```

### API Gateway
OPTIONS methods are configured for CORS preflight:
- Allows all origins (`*`)
- Allows common headers
- Allows all HTTP methods

### Frontend
The frontend uses the API URL from `.env`:
```
REACT_APP_API_URL=https://48c11a5co1.execute-api.ap-south-1.amazonaws.com/dev
```

## Troubleshooting

### Still Getting CORS Errors?

1. **Check Lambda Logs**:
   ```powershell
   aws logs tail /aws/lambda/msc-evaluate-user-crud-dev --follow --region ap-south-1
   ```

2. **Verify Lambda Code**:
   ```powershell
   aws lambda get-function --function-name msc-evaluate-user-crud-dev --region ap-south-1
   ```

3. **Check API Gateway Configuration**:
   ```powershell
   aws apigateway get-rest-api --rest-api-id <API_ID> --region ap-south-1
   ```

### Getting 404 Errors?

- Verify the endpoint exists in CloudFormation template
- Check API Gateway resources and methods
- Ensure the stage is deployed

### Getting 500 Errors?

- Check CloudWatch Logs for Lambda errors
- Verify DynamoDB tables exist
- Check IAM permissions

## Common Issues and Solutions

### Issue: "Failed to load templates"
**Cause**: Template API Lambda not updated or DynamoDB table empty
**Solution**: 
1. Run `.\update-lambdas.ps1`
2. Create a test template using the admin interface

### Issue: "Login failed"
**Cause**: User CRUD Lambda not updated or users table empty
**Solution**:
1. Run `.\update-lambdas.ps1`
2. Run `.\cloudformation\deploy-users.ps1` to initialize users

### Issue: "Network Error"
**Cause**: Lambda timeout or error
**Solution**: Check CloudWatch Logs for the specific Lambda function

## Next Steps

After resolving the CORS errors:

1. **Test Login**: Use admin/admin123 credentials
2. **Create Template**: Test the template creation flow
3. **Take Quiz**: Test the quiz-taking functionality
4. **View Results**: Test the results viewing feature
5. **User Management**: Test creating/editing users (admin only)

## Additional Resources

- **API Documentation**: See `backend/test-payloads/README.md`
- **Deployment Guide**: See `cloudformation/DEPLOYMENT-CHECKLIST.md`
- **Architecture**: See `cloudformation/ARCHITECTURE-DIAGRAM.txt`

## Support

If issues persist:
1. Check all CloudWatch Logs
2. Verify CloudFormation stack status
3. Ensure AWS credentials are configured
4. Check network connectivity to AWS
