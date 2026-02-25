# Quick Start Guide

## Prerequisites Check

Run the validation script first:
```powershell
cd D:\MSCProject\MSCProject\cloudformation
.\validate.ps1
```

## Deploy Everything

### Windows (PowerShell)
```powershell
cd D:\MSCProject\MSCProject\cloudformation
.\deploy.ps1
```

### Windows (CMD)
```cmd
cd D:\MSCProject\MSCProject\cloudformation
deploy.cmd
```

### Linux/Mac/WSL
```bash
cd /d/MSCProject/MSCProject/cloudformation
chmod +x deploy.sh
./deploy.sh
```

## What Gets Deployed

✓ S3 bucket with static website hosting  
✓ 3 Lambda functions (Template API, Take Quiz, Submit Quiz)  
✓ API Gateway with CORS enabled (`*`)  
✓ 2 DynamoDB tables (Templates, Quiz Results)  
✓ IAM roles with minimal permissions  

## After Deployment

You'll get:
- **Frontend URL**: `http://msc-evaluate-frontend-dev.s3-website.ap-south-1.amazonaws.com`
- **API URL**: `https://{api-id}.execute-api.ap-south-1.amazonaws.com/dev`

## API Endpoints

```
POST /templates              - Create a new quiz template
GET  /templates              - List all templates
GET  /templates/{id}/quiz    - Get quiz (without answers)
POST /submit                 - Submit quiz answers
```

All endpoints support CORS with `Access-Control-Allow-Origin: *`

## Update Only Frontend

```powershell
cd ..\frontend
npm run build
aws s3 sync build/ s3://msc-evaluate-frontend-dev/ --region ap-south-1 --delete
```

## Update Only Lambda

```powershell
cd ..\backend\templates
Compress-Archive -Path template_api.py -DestinationPath lambda.zip -Force
aws lambda update-function-code --function-name msc-evaluate-template-api-dev --zip-file fileb://lambda.zip --region ap-south-1
```

## Delete Everything

```powershell
cd D:\MSCProject\MSCProject\cloudformation
.\cleanup.ps1
```

## Troubleshooting

### Deployment fails
```powershell
# Check CloudFormation events
aws cloudformation describe-stack-events --stack-name msc-evaluate-stack-dev --region ap-south-1
```

### Lambda errors
```powershell
# View logs
aws logs tail /aws/lambda/msc-evaluate-template-api-dev --follow --region ap-south-1
```

### Frontend not loading
1. Check S3 bucket policy allows public read
2. Verify `.env` has correct API URL
3. Check browser console for errors

## Cost

With AWS Free Tier: ~$0-5/month  
Without Free Tier: ~$5-20/month (depending on usage)

## Security Notes

⚠️ CORS is set to `*` - suitable for development only  
⚠️ No authentication configured  
⚠️ S3 bucket is publicly readable  

For production, add:
- AWS Cognito for authentication
- Restrict CORS to specific domains
- Add API keys or IAM authorization
