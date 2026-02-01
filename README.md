# MSC Evaluate - Serverless Quiz Application

A modern, serverless quiz evaluation system built with React frontend, AWS Lambda backend, and DynamoDB database. Features AI-powered answer scoring using AWS Bedrock.

## 🏗️ Architecture

- **Frontend**: React SPA hosted on S3 with CloudFront CDN
- **Backend**: AWS Lambda functions with API Gateway
- **Database**: DynamoDB with GSI for efficient queries
- **Authentication**: JWT-based with role management
- **AI Scoring**: AWS Bedrock Nova model for intelligent answer evaluation

## 🚀 Quick Deployment on AWS

### Super Simple Setup (Recommended)

#### Windows
```powershell
# 1. Open PowerShell as Administrator
# 2. Run the quick start script
.\quick-start.ps1
```

#### Linux/macOS
```bash
# 1. Open terminal
# 2. Run the quick start script
chmod +x quick-start.sh
./quick-start.sh
```

The quick start script will:
- ✅ Check all prerequisites automatically
- ⚙️ Guide you through configuration
- 🚀 Deploy everything to AWS in one command
- 📋 Provide you with access URLs

### Manual Deployment (Advanced)

#### Prerequisites
- AWS CLI configured with appropriate permissions
- Node.js 18+ (for frontend)
- Python 3.9+ (for Lambda functions)

#### Windows
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\deploy.ps1 -Environment "dev" -Region "us-east-1"
```

#### Linux/macOS
```bash
chmod +x deploy.sh
./deploy.sh --environment dev --region us-east-1
```

### Deployment Options

```bash
# Custom environment and region
./deploy.sh -e prod -r us-west-2

# Skip frontend deployment (backend only)
./deploy.sh --skip-frontend

# Custom project name
./deploy.sh -p my-quiz-app

# Custom JWT secret
./deploy.sh -j "your-super-secret-jwt-key-here"
```

## 🎯 Features

### User Roles & Permissions

- **Student**: Take quizzes, view personal results
- **Tutor**: Create/edit templates, view student reports  
- **Admin**: Full system access, user management

### Core Functionality

1. **Authentication System**
   - JWT-based login/signup
   - Role-based access control
   - Secure password handling

2. **Template Management**
   - Create quiz templates with multiple questions
   - Organize by subject and course
   - Admin/Tutor only access

3. **Quiz Taking**
   - Student name/ID collection
   - Progress tracking
   - Auto-save answers

4. **AI-Powered Scoring**
   - AWS Bedrock Nova model integration
   - Intelligent answer evaluation
   - Detailed feedback and suggestions

5. **Results & Reports**
   - Individual quiz results
   - Performance analytics
   - Export capabilities

## 📁 Project Structure

```
msc-evaluate/
├── frontend/                    # React application
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── services/           # API and auth services
│   │   └── App.js             # Main app component
│   └── package.json
├── backend/                     # Lambda functions
│   ├── auth/                   # Authentication functions
│   ├── templates/              # Template management
│   ├── quiz/                   # Quiz operations
│   └── shared/                 # Common utilities
├── infrastructure/             # CloudFormation templates
│   └── complete-infrastructure.yaml
├── deploy.ps1                  # Windows deployment script
├── deploy.sh                   # Linux/macOS deployment script
├── destroy.ps1                 # Windows cleanup script
└── destroy.sh                  # Linux/macOS cleanup script
```

## 🔧 Manual Deployment Steps

If you prefer manual deployment or need to customize the process:

### 1. Deploy Infrastructure

```bash
aws cloudformation deploy \
  --template-file infrastructure/complete-infrastructure.yaml \
  --stack-name msc-evaluate-infrastructure-dev \
  --parameter-overrides \
    ProjectName=msc-evaluate \
    Environment=dev \
    JWTSecret=your-jwt-secret \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

### 2. Package Lambda Functions

```bash
# Create deployment packages
cd backend
zip -r auth-login.zip auth/login.py shared/
zip -r auth-signup.zip auth/signup.py shared/
# ... repeat for other functions
```

### 3. Update Lambda Code

```bash
aws lambda update-function-code \
  --function-name msc-evaluate-auth-login-dev \
  --zip-file fileb://auth-login.zip
```

### 4. Build and Deploy Frontend

```bash
cd frontend
npm install
echo "REACT_APP_API_URL=https://your-api-url" > .env
npm run build
aws s3 sync build/ s3://your-frontend-bucket --delete
```

## 🗑️ Cleanup

To destroy all resources:

### Windows
```powershell
.\destroy.ps1 -Environment "dev" -Force
```

### Linux/macOS
```bash
./destroy.sh --environment dev --force
```

## 🔐 Security Features

- JWT token authentication
- Role-based access control
- HTTPS enforcement via CloudFront
- Input validation and sanitization
- DynamoDB encryption at rest
- Lambda function isolation

## 💰 Cost Optimization

- **DynamoDB**: On-demand billing for variable workloads
- **Lambda**: Pay-per-request with efficient memory allocation
- **S3**: Standard storage with CloudFront caching
- **API Gateway**: REST API with request-based pricing

## 📊 Monitoring

The deployment includes:
- CloudWatch logs for all Lambda functions
- API Gateway request/error metrics
- DynamoDB performance metrics
- CloudFront distribution analytics

## 🔧 Configuration

### Environment Variables

Lambda functions use these environment variables:
- `JWT_SECRET`: Secret key for JWT signing
- `USERS_TABLE`: DynamoDB users table name
- `TEMPLATES_TABLE`: DynamoDB templates table name
- `QUIZ_RESULTS_TABLE`: DynamoDB results table name
- `ENVIRONMENT`: Current environment (dev/staging/prod)

### Frontend Configuration

React app uses:
- `REACT_APP_API_URL`: API Gateway endpoint URL

## 🐛 Troubleshooting

### Common Issues

1. **Lambda timeout errors**: Increase timeout in CloudFormation template
2. **CORS errors**: Check API Gateway CORS configuration
3. **Authentication failures**: Verify JWT secret consistency
4. **DynamoDB throttling**: Consider provisioned capacity for high load

### Logs and Debugging

```bash
# View Lambda logs
aws logs tail /aws/lambda/msc-evaluate-auth-login-dev --follow

# Check API Gateway logs
aws logs tail API-Gateway-Execution-Logs_<api-id>/dev --follow
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review CloudWatch logs
3. Open an issue on GitHub
4. Contact the development team

---

**Happy Quizzing! 📝✨**