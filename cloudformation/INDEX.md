# MSC Evaluate - Deployment Package Index

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [File Guide](#file-guide)
3. [Deployment Process](#deployment-process)
4. [Architecture](#architecture)
5. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### For First-Time Users

1. **Read First**: [START-HERE.txt](START-HERE.txt) - Simple text overview
2. **Understand**: [DEPLOYMENT-SUMMARY.md](DEPLOYMENT-SUMMARY.md) - Complete details
3. **Validate**: Run `.\validate.ps1` - Check prerequisites
4. **Deploy**: Run `.\deploy.ps1` - Deploy everything

### For Experienced Users

```powershell
cd D:\MSCProject\MSCProject\cloudformation
.\deploy.ps1
```

---

## 📁 File Guide

### 🎯 Start Here

| File | Purpose | When to Use |
|------|---------|-------------|
| **START-HERE.txt** | Simple overview in plain text | First time setup |
| **DEPLOYMENT-SUMMARY.md** | Complete deployment guide | Understanding the system |
| **QUICK-START.md** | Quick reference commands | Daily operations |

### 🔧 Deployment Scripts

| File | Purpose | Platform |
|------|---------|----------|
| **deploy.ps1** | Main deployment script | Windows PowerShell |
| **deploy.sh** | Main deployment script | Linux/Mac/WSL |
| **deploy.cmd** | Quick launcher | Windows CMD |
| **deploy-stack.yaml** | CloudFormation template | AWS Infrastructure |

### 🛠️ Utility Scripts

| File | Purpose | When to Use |
|------|---------|-------------|
| **validate.ps1** | Check prerequisites | Before deployment |
| **cleanup.ps1** | Remove all resources | Cleanup/Reset |

### 📚 Documentation

| File | Purpose | Best For |
|------|---------|----------|
| **README.md** | Detailed deployment guide | Troubleshooting |
| **DEPLOYMENT-CHECKLIST.md** | Step-by-step checklist | Following process |
| **INDEX.md** | This file - Navigation | Finding information |

---

## 🔄 Deployment Process

### Step 1: Validate Prerequisites

```powershell
.\validate.ps1
```

**Checks:**
- ✓ AWS CLI installed
- ✓ AWS credentials configured
- ✓ Node.js and npm installed
- ✓ Project structure intact
- ✓ Region availability

### Step 2: Deploy Infrastructure

```powershell
.\deploy.ps1
```

**Actions:**
1. Creates CloudFormation stack (~5 min)
2. Deploys Lambda functions (~1 min)
3. Builds React frontend (~2 min)
4. Uploads to S3 (~1 min)

**Total Time:** ~10 minutes

### Step 3: Verify Deployment

**Outputs:**
- Frontend URL: `http://msc-evaluate-frontend-dev.s3-website.ap-south-1.amazonaws.com`
- API URL: `https://{api-id}.execute-api.ap-south-1.amazonaws.com/dev`

**Test:**
1. Open Frontend URL in browser
2. Create a test quiz template
3. Take the quiz
4. Submit answers

---

## 🏗️ Architecture

### AWS Resources Created

```
┌─────────────────────────────────────────────────────────────┐
│                     MSC Evaluate Stack                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐         ┌─────────────────────────────┐  │
│  │   Frontend   │         │       API Gateway           │  │
│  │   (S3 Web)   │────────▶│   (REST API + CORS)         │  │
│  └──────────────┘         └─────────────────────────────┘  │
│                                      │                       │
│                                      ▼                       │
│                           ┌──────────────────────┐          │
│                           │  Lambda Functions    │          │
│                           ├──────────────────────┤          │
│                           │ • Template API       │          │
│                           │ • Take Quiz          │          │
│                           │ • Submit Quiz        │          │
│                           └──────────────────────┘          │
│                                      │                       │
│                                      ▼                       │
│                           ┌──────────────────────┐          │
│                           │  DynamoDB Tables     │          │
│                           ├──────────────────────┤          │
│                           │ • Templates          │          │
│                           │ • Quiz Results       │          │
│                           └──────────────────────┘          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Component Details

#### Frontend (S3)
- **Type**: Static website hosting
- **Access**: Public read
- **CORS**: Enabled for API calls
- **Caching**: Optimized headers

#### API Gateway
- **Type**: REST API
- **Endpoint**: Regional (ap-south-1)
- **CORS**: `Access-Control-Allow-Origin: *`
- **Integration**: Lambda Proxy

#### Lambda Functions
1. **Template API** (`template_api.py`)
   - POST /templates - Create template
   - GET /templates - List templates
   - GET /templates/{id} - Get template

2. **Take Quiz** (`take_quiz.py`)
   - GET /templates/{id}/quiz - Get quiz without answers

3. **Submit Quiz** (`submit_quiz.py`)
   - POST /submit - Evaluate and store results

#### DynamoDB Tables
1. **Templates Table**
   - Key: template_id (String)
   - Attributes: title, subject, course, questions

2. **Quiz Results Table**
   - Key: result_id (String)
   - GSI: session_id-index
   - Attributes: answers, score, timestamps

---

## 🔍 Troubleshooting

### Common Issues

#### 1. Deployment Fails

**Symptom**: CloudFormation stack creation fails

**Solutions:**
```powershell
# Check stack events
aws cloudformation describe-stack-events --stack-name msc-evaluate-stack-dev --region ap-south-1

# Check AWS credentials
aws sts get-caller-identity

# Verify permissions
aws iam get-user
```

#### 2. Frontend Not Loading

**Symptom**: S3 website URL returns error

**Solutions:**
- Check S3 bucket policy allows public read
- Verify static website hosting is enabled
- Check `.env` file has correct API URL
- Clear browser cache

#### 3. API Returns CORS Errors

**Symptom**: Browser console shows CORS errors

**Solutions:**
- Verify Lambda functions return CORS headers
- Check API Gateway OPTIONS methods
- Test API directly with curl (bypasses CORS)

```powershell
# Test without CORS
curl https://{api-id}.execute-api.ap-south-1.amazonaws.com/dev/templates
```

#### 4. Lambda Function Errors

**Symptom**: API returns 500 errors

**Solutions:**
```powershell
# View Lambda logs
aws logs tail /aws/lambda/msc-evaluate-template-api-dev --follow --region ap-south-1

# Check function configuration
aws lambda get-function --function-name msc-evaluate-template-api-dev --region ap-south-1
```

#### 5. DynamoDB Access Denied

**Symptom**: Lambda can't read/write DynamoDB

**Solutions:**
- Check Lambda execution role has DynamoDB permissions
- Verify table names match in code
- Check IAM policy attached to Lambda role

### Getting Help

1. **Check Logs**: CloudWatch Logs for Lambda functions
2. **Stack Events**: CloudFormation console for infrastructure issues
3. **API Testing**: Use curl or Postman to test endpoints
4. **AWS Console**: Visual inspection of resources

---

## 📊 Monitoring

### CloudWatch Log Groups

```
/aws/lambda/msc-evaluate-template-api-dev
/aws/lambda/msc-evaluate-take-quiz-dev
/aws/lambda/msc-evaluate-submit-quiz-dev
```

### View Logs

```powershell
# Tail logs in real-time
aws logs tail /aws/lambda/msc-evaluate-template-api-dev --follow --region ap-south-1

# Get recent errors
aws logs filter-log-events --log-group-name /aws/lambda/msc-evaluate-template-api-dev --filter-pattern "ERROR" --region ap-south-1
```

### Metrics to Monitor

- Lambda invocations
- Lambda errors
- API Gateway 4xx/5xx errors
- DynamoDB read/write capacity
- S3 bucket requests

---

## 🔄 Common Operations

### Update Frontend Only

```powershell
cd ..\frontend
npm run build
aws s3 sync build/ s3://msc-evaluate-frontend-dev/ --region ap-south-1 --delete
```

### Update Lambda Only

```powershell
cd ..\backend\templates
Compress-Archive -Path template_api.py -DestinationPath lambda.zip -Force
aws lambda update-function-code --function-name msc-evaluate-template-api-dev --zip-file fileb://lambda.zip --region ap-south-1
```

### View Stack Status

```powershell
aws cloudformation describe-stacks --stack-name msc-evaluate-stack-dev --region ap-south-1
```

### Delete Everything

```powershell
.\cleanup.ps1
```

---

## 💰 Cost Management

### Free Tier Limits

- **S3**: 5GB storage, 20,000 GET requests
- **Lambda**: 1M requests, 400,000 GB-seconds
- **API Gateway**: 1M requests
- **DynamoDB**: 25GB storage, 25 read/write units

### Cost Optimization

1. Use DynamoDB on-demand pricing
2. Set S3 lifecycle policies
3. Enable Lambda reserved concurrency
4. Monitor CloudWatch metrics
5. Delete unused resources

---

## 🔒 Security Checklist

### Current Configuration (Development)

- ⚠️ CORS set to `*`
- ⚠️ No authentication
- ⚠️ S3 bucket publicly readable
- ⚠️ No rate limiting

### Production Recommendations

- ✅ Add AWS Cognito authentication
- ✅ Restrict CORS to specific domains
- ✅ Add API Gateway API keys
- ✅ Enable CloudFront with HTTPS
- ✅ Add WAF for DDoS protection
- ✅ Enable DynamoDB encryption
- ✅ Set up CloudTrail logging
- ✅ Configure rate limiting

---

## 📞 Support Resources

### Documentation Files

- [START-HERE.txt](START-HERE.txt) - Quick overview
- [DEPLOYMENT-SUMMARY.md](DEPLOYMENT-SUMMARY.md) - Complete guide
- [README.md](README.md) - Detailed documentation
- [QUICK-START.md](QUICK-START.md) - Quick reference
- [DEPLOYMENT-CHECKLIST.md](DEPLOYMENT-CHECKLIST.md) - Step-by-step

### AWS Documentation

- [CloudFormation](https://docs.aws.amazon.com/cloudformation/)
- [Lambda](https://docs.aws.amazon.com/lambda/)
- [API Gateway](https://docs.aws.amazon.com/apigateway/)
- [DynamoDB](https://docs.aws.amazon.com/dynamodb/)
- [S3](https://docs.aws.amazon.com/s3/)

---

## ✅ Success Criteria

Your deployment is successful when:

- ✓ CloudFormation stack status is CREATE_COMPLETE
- ✓ All Lambda functions are active
- ✓ API Gateway returns 200 responses
- ✓ Frontend loads without errors
- ✓ Can create quiz templates
- ✓ Can take and submit quizzes
- ✓ Data appears in DynamoDB tables

---

**Last Updated**: February 25, 2026  
**Version**: 1.0  
**Region**: ap-south-1 (Mumbai)  
**Environment**: dev
