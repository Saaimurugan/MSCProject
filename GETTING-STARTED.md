# 🚀 Getting Started with MSC Evaluate on AWS

## What You'll Get
A complete serverless quiz application with:
- 📝 AI-powered quiz evaluation using AWS Bedrock
- 👥 Multi-role system (Student, Tutor, Admin)
- 🎯 Template-based quiz creation
- 📊 Results tracking and reporting
- 🔐 Secure JWT authentication

## 🎯 One-Click Deployment

### Step 1: Prerequisites
You need:
- AWS account (free tier eligible)
- Windows PowerShell OR Linux/macOS terminal

### Step 2: Get AWS Credentials
1. Go to [AWS Console](https://console.aws.amazon.com)
2. Navigate to IAM → Users → Create User
3. Attach `AdministratorAccess` policy
4. Create access keys
5. Run `aws configure` and enter your keys

### Step 3: Deploy Everything
#### Windows
```powershell
# Download the project files, then:
.\quick-start.ps1
```

#### Linux/macOS
```bash
# Download the project files, then:
chmod +x quick-start.sh
./quick-start.sh
```

### Step 4: Access Your App
After deployment (10-15 minutes), you'll get:
- 🌐 **Frontend URL**: Your quiz application
- 🔗 **API URL**: Backend services
- 📊 **AWS Console**: Monitor your resources

## 🎓 First Steps After Deployment

### 1. Create Admin Account
- Go to your frontend URL
- Click "Sign Up"
- Create account with role "Admin"

### 2. Create Your First Quiz Template
- Login as admin
- Click "Create Template"
- Add questions with example answers
- Save template

### 3. Students Can Take Quizzes
- Students sign up with role "Student"
- They see available quiz cards on dashboard
- Click card → Enter name/ID → Take quiz
- Get AI-powered scoring and feedback

## 💰 Cost Breakdown
**Monthly costs (estimated):**
- DynamoDB: $0-25
- Lambda: $0-10 (1M requests free)
- API Gateway: $0-15 (1M requests free)
- S3 + CloudFront: $1-15
- **Total: $1-65/month** (depends on usage)

## 🔧 Customization Options

### Different Environments
```bash
# Deploy to staging
./deploy.sh --environment staging

# Deploy to production
./deploy.sh --environment prod
```

### Different AWS Regions
```bash
# Deploy to US West
./deploy.sh --region us-west-2

# Deploy to Europe
./deploy.sh --region eu-west-1
```

### Backend Only (No Frontend)
```bash
# Skip React frontend deployment
./deploy.sh --skip-frontend
```

## 🗑️ Cleanup
When you're done testing:
```bash
# Windows
.\destroy.ps1 -Force

# Linux/macOS
./destroy.sh --force
```

## 🆘 Need Help?

### Common Issues
1. **AWS credentials error**: Run `aws configure`
2. **Permission denied**: Use Administrator/sudo
3. **Node.js not found**: Install from [nodejs.org](https://nodejs.org)
4. **Deployment fails**: Check AWS CloudWatch logs

### Support Resources
- 📖 [Complete Documentation](README.md)
- 🔧 [Detailed AWS Guide](AWS-DEPLOYMENT-GUIDE.md)
- 🐛 [Troubleshooting Guide](deployment-guide.md)

## 🎉 Success!
Once deployed, you have a production-ready quiz application that can:
- Handle thousands of concurrent users
- Scale automatically with demand
- Provide AI-powered answer evaluation
- Support multiple educational institutions

**Start creating quizzes and let AI help evaluate student responses!**