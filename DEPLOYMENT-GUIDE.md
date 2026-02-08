# MSC Evaluate - AWS Deployment Guide

This guide provides step-by-step instructions for deploying the MSC Evaluate application to AWS in the ap-south-1 region.

## 🚀 Quick Start (Recommended)

For a complete deployment with all components:

```powershell
# Run the complete deployment script
.\deploy-complete.ps1 -Region "ap-south-1" -Environment "dev"
```

This will deploy:
- ✅ DynamoDB tables
- ✅ Lambda functions
- ✅ API Gateway with CORS
- ✅ Frontend to S3 bucket

## 📋 Prerequisites

Before running the deployment scripts, ensure you have:

1. **AWS CLI** installed and configured
   ```powershell
   aws configure
   ```

2. **Node.js 18+** and npm (for frontend)
   ```powershell
   node --version
   npm --version
   ```

3. **Python 3.9+** and pip (for Lambda functions)
   ```powershell
   python --version
   pip --version
   ```

4. **PowerShell** (Windows) or **PowerShell Core** (Linux/macOS)

## 🔧 Individual Component Deployment

### 1. Create DynamoDB Tables

```powershell
.\create-dynamodb-tables.ps1 -Region "ap-south-1" -Environment "dev"
```

Creates:
- `msc-evaluate-users-dev`
- `msc-evaluate-templates-dev`
- `msc-evaluate-quiz-results-dev`

### 2. Deploy Backend Lambda Functions

```powershell
.\deploy-backend.ps1 -Region "ap-south-1" -Environment "dev" -JWTSecret "your-secret-key"
```

Deploys 18 Lambda functions for:
- Authentication (login, signup)
- Admin operations (user management)
- Profile management
- Template management
- Quiz operations
- Reports
- AI scoring

### 3. Deploy API Gateway

```powershell
.\deploy-api.ps1 -Region "ap-south-1" -Environment "dev" -StageName "dev"
```

Creates:
- REST API with 18 endpoints
- CORS enabled for all endpoints
- Lambda integrations
- Deployed to "dev" stage

### 4. Deploy Frontend

```powershell
.\deploy-frontend.ps1 -BucketName "msc-evaluate-frontend-dev-127510141" -Region "ap-south-1" -Environment "dev"
```

- Builds React application
- Uploads to S3 bucket
- Configures static website hosting
- Sets up public access policies

## 🎯 Deployment Options

### Custom Parameters

```powershell
# Custom environment and region
.\deploy-complete.ps1 -Region "us-east-1" -Environment "prod"

# Custom S3 bucket name
.\deploy-complete.ps1 -BucketName "my-custom-bucket-name"

# Custom JWT secret
.\deploy-complete.ps1 -JWTSecret "my-super-secure-jwt-secret"

# Skip specific components
.\deploy-complete.ps1 -SkipFrontend  # Skip frontend deployment
.\deploy-complete.ps1 -SkipBackend   # Skip backend deployment
.\deploy-complete.ps1 -SkipDatabase  # Skip DynamoDB creation
```

### Partial Deployments

```powershell
# Deploy only backend and API
.\deploy-all.ps1 -SkipFrontend

# Deploy only frontend (requires existing API)
.\deploy-frontend.ps1 -ApiUrl "https://your-api-id.execute-api.ap-south-1.amazonaws.com/dev"
```

## 🔐 Security Configuration

### Default Credentials

The deployment creates a default admin user:
- **Email**: `admin@msc-evaluate.com`
- **Password**: `Admin123!`

⚠️ **IMPORTANT**: Change these credentials immediately after deployment!

### JWT Secret

The deployment generates a random JWT secret. For production:

```powershell
.\deploy-complete.ps1 -JWTSecret "your-production-jwt-secret-min-32-chars"
```

## 📊 Post-Deployment

### 1. Verify Deployment

After successful deployment, you'll see:

```
🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!
=====================================
Environment: dev
Region: ap-south-1

🗄️ Database:
  DynamoDB Tables: 3 created

📦 Backend:
  Lambda Functions: 18 deployed

🔗 API Gateway:
  API URL: https://abc123.execute-api.ap-south-1.amazonaws.com/dev
  Endpoints: 18 created

🌐 Frontend:
  S3 Bucket: msc-evaluate-frontend-dev-127510141
  Website URL: http://msc-evaluate-frontend-dev-127510141.s3-website-ap-south-1.amazonaws.com
```

### 2. Test the Application

1. Open the website URL in your browser
2. Login with admin credentials
3. Change the default password
4. Create your first quiz template
5. Test the quiz functionality

### 3. API Endpoints

The following endpoints are available:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | User login |
| POST | `/auth/signup` | User registration |
| GET | `/admin/users` | Get all users (admin) |
| POST | `/admin/users` | Create user (admin) |
| DELETE | `/admin/users/{userId}` | Delete user (admin) |
| PUT | `/admin/users/{userId}/role` | Update user role (admin) |
| GET | `/admin/usage-logs` | Get usage logs (admin) |
| GET | `/profile` | Get user profile |
| PUT | `/profile` | Update user profile |
| PUT | `/profile/password` | Change password |
| GET | `/templates` | Get quiz templates |
| POST | `/templates` | Create quiz template |
| POST | `/quiz/take` | Start quiz |
| POST | `/quiz/submit` | Submit quiz |
| GET | `/reports` | Get all reports |
| GET | `/reports/user/{userId}` | Get user reports |
| GET | `/reports/template/{templateId}` | Get template reports |
| POST | `/ai/evaluate` | AI answer evaluation |

## 🐛 Troubleshooting

### Common Issues

1. **AWS Credentials Error**
   ```
   Solution: Run 'aws configure' and set up your credentials
   ```

2. **Lambda Function Not Found**
   ```
   Solution: Deploy backend first with .\deploy-backend.ps1
   ```

3. **CORS Errors**
   ```
   Solution: API Gateway automatically configures CORS with '*' origin
   ```

4. **S3 Bucket Already Exists**
   ```
   Solution: Use a different bucket name with -BucketName parameter
   ```

5. **DynamoDB Table Already Exists**
   ```
   Solution: The script will skip existing tables automatically
   ```

### Logs and Debugging

- Deployment logs are saved automatically as `deployment-log-{env}-{timestamp}.txt`
- Check CloudWatch logs for Lambda function errors
- Use AWS Console to verify resource creation

### Clean Up

To remove all resources:

```powershell
# Delete S3 bucket contents
aws s3 rm s3://msc-evaluate-frontend-dev-127510141 --recursive

# Delete S3 bucket
aws s3api delete-bucket --bucket msc-evaluate-frontend-dev-127510141 --region ap-south-1

# Delete API Gateway
aws apigateway delete-rest-api --rest-api-id YOUR_API_ID --region ap-south-1

# Delete Lambda functions
aws lambda list-functions --region ap-south-1 | grep msc-evaluate | # Delete each function

# Delete DynamoDB tables
aws dynamodb delete-table --table-name msc-evaluate-users-dev --region ap-south-1
aws dynamodb delete-table --table-name msc-evaluate-templates-dev --region ap-south-1
aws dynamodb delete-table --table-name msc-evaluate-quiz-results-dev --region ap-south-1
```

## 📞 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review deployment logs
3. Check AWS CloudWatch logs
4. Verify AWS permissions and quotas

---

**Happy Deploying! 🚀**