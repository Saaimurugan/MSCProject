# Deployment Checklist

## Pre-Deployment

- [ ] AWS CLI installed and configured
- [ ] Node.js and npm installed
- [ ] AWS credentials configured (`aws configure`)
- [ ] Verified AWS account has necessary permissions
- [ ] Run validation script: `.\validate.ps1`

## Deployment Steps

- [ ] Navigate to cloudformation folder: `cd D:\MSCProject\MSCProject\cloudformation`
- [ ] Run deployment script: `.\deploy.ps1`
- [ ] Wait for CloudFormation stack creation (~5-10 minutes)
- [ ] Wait for Lambda functions deployment
- [ ] Wait for frontend build and S3 upload
- [ ] Note the Frontend URL and API URL from output

## Post-Deployment Verification

- [ ] Open Frontend URL in browser
- [ ] Verify frontend loads without errors
- [ ] Check browser console for any errors
- [ ] Test API endpoints:
  - [ ] POST /templates (create a test template)
  - [ ] GET /templates (list templates)
  - [ ] GET /templates/{id}/quiz (get quiz)
  - [ ] POST /submit (submit quiz answers)

## Test API with curl

```powershell
# Get API URL from deployment output
$API_URL = "https://{api-id}.execute-api.ap-south-1.amazonaws.com/dev"

# Test GET /templates
curl "$API_URL/templates"

# Test POST /templates
curl -X POST "$API_URL/templates" `
  -H "Content-Type: application/json" `
  -d '{
    "title": "Test Quiz",
    "subject": "Math",
    "course": "Algebra",
    "questions": [
      {
        "question_text": "What is 2+2?",
        "options": ["3", "4", "5"],
        "correct_answer": 1
      }
    ]
  }'
```

## Monitoring

- [ ] Check CloudWatch Logs for Lambda functions
- [ ] Monitor DynamoDB tables for data
- [ ] Check S3 bucket for frontend files
- [ ] Verify API Gateway metrics

## CloudWatch Log Groups

```
/aws/lambda/msc-evaluate-template-api-dev
/aws/lambda/msc-evaluate-take-quiz-dev
/aws/lambda/msc-evaluate-submit-quiz-dev
```

## Common Issues

### Issue: CloudFormation stack fails
**Solution**: Check stack events in AWS Console or run:
```powershell
aws cloudformation describe-stack-events --stack-name msc-evaluate-stack-dev --region ap-south-1
```

### Issue: Frontend shows API errors
**Solution**: 
1. Check `.env` file has correct API URL
2. Verify CORS headers in Lambda responses
3. Check browser network tab for failed requests

### Issue: Lambda function errors
**Solution**: Check CloudWatch Logs:
```powershell
aws logs tail /aws/lambda/msc-evaluate-template-api-dev --follow --region ap-south-1
```

### Issue: DynamoDB access denied
**Solution**: Verify Lambda execution role has DynamoDB permissions

## Rollback

If deployment fails or you need to start over:

```powershell
.\cleanup.ps1
```

Then redeploy:
```powershell
.\deploy.ps1
```

## Production Considerations

Before going to production:

- [ ] Change CORS from `*` to specific domain
- [ ] Add AWS Cognito for authentication
- [ ] Add API Gateway API keys or IAM authorization
- [ ] Enable CloudWatch alarms for errors
- [ ] Set up CloudFront for S3 static website
- [ ] Enable S3 versioning
- [ ] Configure DynamoDB backups
- [ ] Set up proper logging and monitoring
- [ ] Review and minimize IAM permissions
- [ ] Enable AWS WAF for API Gateway
- [ ] Set up proper error handling and retry logic
- [ ] Configure rate limiting on API Gateway
- [ ] Add input validation and sanitization
- [ ] Set up CI/CD pipeline for automated deployments

## Support Resources

- [AWS CloudFormation Documentation](https://docs.aws.amazon.com/cloudformation/)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [API Gateway Documentation](https://docs.aws.amazon.com/apigateway/)
- [DynamoDB Documentation](https://docs.aws.amazon.com/dynamodb/)
- [S3 Static Website Hosting](https://docs.aws.amazon.com/AmazonS3/latest/userguide/WebsiteHosting.html)
