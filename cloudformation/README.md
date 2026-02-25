# MSC Evaluate - Deployment Guide

This directory contains CloudFormation templates and deployment scripts for the MSC Evaluate Quiz Application.

## Architecture

The deployment creates the following AWS resources:

- **S3 Bucket**: Static website hosting for React frontend
- **Lambda Functions**: Three serverless functions for backend API
  - Template API (create/get templates)
  - Take Quiz (retrieve quiz without answers)
  - Submit Quiz (evaluate and store results)
- **API Gateway**: REST API with CORS enabled (`Access-Control-Allow-Origin: *`)
- **DynamoDB Tables**: 
  - Templates table
  - Quiz Results table with session_id index

## Prerequisites

1. **AWS CLI** installed and configured
   ```bash
   aws configure
   ```
   
2. **Node.js and npm** installed (for frontend build)

3. **AWS Credentials** with permissions to create:
   - CloudFormation stacks
   - S3 buckets
   - Lambda functions
   - API Gateway
   - DynamoDB tables
   - IAM roles

## Deployment

### Region: ap-south-1 (Mumbai)

### Option 1: Using PowerShell (Windows)

```powershell
cd D:\MSCProject\MSCProject\cloudformation
.\deploy.ps1
```

### Option 2: Using Bash (Linux/Mac/WSL)

```bash
cd /d/MSCProject/MSCProject/cloudformation
chmod +x deploy.sh
./deploy.sh
```

## What the Deployment Script Does

1. **Creates CloudFormation Stack**
   - Deploys all infrastructure resources
   - Sets up IAM roles and permissions
   - Configures CORS on API Gateway

2. **Packages Lambda Functions**
   - Zips Python Lambda code
   - Updates Lambda function code

3. **Builds Frontend**
   - Installs npm dependencies
   - Creates production build
   - Updates .env with API Gateway URL

4. **Deploys to S3**
   - Syncs build files to S3 bucket
   - Configures caching headers
   - Enables static website hosting

## Configuration

### Environment Variables

The deployment uses the following defaults:
- **Region**: `ap-south-1`
- **Environment**: `dev`
- **Stack Name**: `msc-evaluate-stack-dev`

To change these, edit the variables at the top of `deploy.ps1` or `deploy.sh`.

### CORS Configuration

All API endpoints are configured with:
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Headers: Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token
Access-Control-Allow-Methods: GET,POST,PUT,DELETE,OPTIONS
```

## API Endpoints

After deployment, you'll have the following endpoints:

```
POST   https://{api-id}.execute-api.ap-south-1.amazonaws.com/dev/templates
GET    https://{api-id}.execute-api.ap-south-1.amazonaws.com/dev/templates
GET    https://{api-id}.execute-api.ap-south-1.amazonaws.com/dev/templates/{template_id}/quiz
POST   https://{api-id}.execute-api.ap-south-1.amazonaws.com/dev/submit
```

## Outputs

After successful deployment, you'll see:

- **Frontend URL**: S3 static website URL
- **API Gateway URL**: Base URL for all API endpoints
- **Lambda Function ARNs**: ARNs for all three Lambda functions

## Updating the Application

### Update Lambda Functions Only

```powershell
# PowerShell
aws lambda update-function-code `
  --function-name msc-evaluate-template-api-dev `
  --zip-file fileb://template-api.zip `
  --region ap-south-1
```

### Update Frontend Only

```powershell
# PowerShell
cd ..\frontend
npm run build
aws s3 sync build/ s3://msc-evaluate-frontend-dev/ --region ap-south-1 --delete
```

### Full Redeployment

Simply run the deployment script again:
```powershell
.\deploy.ps1
```

## Cleanup

To delete all resources:

```powershell
# Empty S3 bucket first
aws s3 rm s3://msc-evaluate-frontend-dev/ --recursive --region ap-south-1

# Delete CloudFormation stack
aws cloudformation delete-stack --stack-name msc-evaluate-stack-dev --region ap-south-1
```

## Troubleshooting

### CloudFormation Stack Fails

Check the CloudFormation console for detailed error messages:
```powershell
aws cloudformation describe-stack-events `
  --stack-name msc-evaluate-stack-dev `
  --region ap-south-1
```

### Lambda Function Errors

View Lambda logs in CloudWatch:
```powershell
aws logs tail /aws/lambda/msc-evaluate-template-api-dev --follow --region ap-south-1
```

### CORS Issues

Ensure:
1. API Gateway has OPTIONS methods configured
2. Lambda functions return CORS headers
3. Frontend is making requests to the correct API URL

### Frontend Not Loading

1. Check S3 bucket policy allows public read
2. Verify static website hosting is enabled
3. Check browser console for errors

## Cost Estimation

With AWS Free Tier:
- **S3**: First 5GB free
- **Lambda**: 1M requests/month free
- **API Gateway**: 1M requests/month free
- **DynamoDB**: 25GB storage free

Expected monthly cost (beyond free tier): $5-20 depending on usage

## Security Notes

- CORS is set to `*` for development. For production, restrict to specific domains.
- No authentication is configured. Add AWS Cognito or API keys for production.
- S3 bucket is publicly readable for static website hosting.
- Lambda functions have minimal IAM permissions (DynamoDB access only).

## Support

For issues or questions, refer to:
- AWS CloudFormation documentation
- AWS Lambda documentation
- API Gateway documentation
