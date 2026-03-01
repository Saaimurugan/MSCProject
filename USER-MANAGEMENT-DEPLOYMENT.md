# User Management System - Deployment Guide

This guide explains how to deploy the new user management system with database-backed authentication.

## Overview

The user management system includes:
- DynamoDB Users table for storing user data
- Backend Lambda function for user CRUD operations
- Admin-only access control for user management
- Database-backed authentication (replacing hardcoded credentials)
- Frontend user management interface

## Architecture Changes

### Backend
1. New DynamoDB table: `msc-evaluate-users-{environment}`
2. New Lambda function: `msc-evaluate-user-crud-{environment}`
3. New API endpoints:
   - `POST /users/login` - User authentication (public)
   - `GET /users` - List all users (admin only)
   - `GET /users/{user_id}` - Get user details (admin only)
   - `POST /users` - Create new user (admin only)
   - `PUT /users/{user_id}` - Update user (admin only)
   - `DELETE /users/{user_id}` - Delete user (admin only)

### Frontend
1. Updated Login component to use backend API
2. New UserManagement component for admin user CRUD
3. Updated Dashboard with "Users" link for admins
4. API service with authentication interceptor

## Deployment Steps

### 1. Deploy Infrastructure

The CloudFormation template has been updated to include the Users table and Lambda function.

```bash
# Windows
cd cloudformation
.\deploy.ps1 -Environment "dev"

# Linux/macOS
cd cloudformation
./deploy.sh --environment dev
```

This will create:
- DynamoDB Users table
- Lambda function for user CRUD
- API Gateway endpoints for user management

### 2. Package and Deploy Lambda Function

```bash
cd backend/users
zip user_crud.zip user_crud.py

# Update Lambda function
aws lambda update-function-code \
  --function-name msc-evaluate-user-crud-dev \
  --zip-file fileb://user_crud.zip \
  --region us-east-1
```

### 3. Initialize Default Users

Run the initialization script to create default users:

```bash
cd backend/users
python init_users.py msc-evaluate-users-dev
```

This creates three default users:
- **admin** / admin123 (Admin role)
- **tutor** / tutor123 (Tutor role)
- **student** / student123 (Student role)

### 4. Update Frontend Environment

Get the API Gateway URL from CloudFormation outputs:

```bash
aws cloudformation describe-stacks \
  --stack-name msc-evaluate-infrastructure-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
  --output text
```

Update `frontend/.env`:
```
REACT_APP_API_URL=https://your-api-id.execute-api.us-east-1.amazonaws.com/dev
```

### 5. Build and Deploy Frontend

```bash
cd frontend
npm install
npm run build

# Deploy to S3
aws s3 sync build/ s3://msc-evaluate-frontend-dev --delete
```

## Testing

### 1. Test Login API

```bash
curl -X POST https://your-api-url/dev/users/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

Expected response:
```json
{
  "message": "Login successful",
  "user": {
    "user_id": "...",
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin",
    "full_name": "System Administrator",
    "is_active": true
  }
}
```

### 2. Test User Management (Admin Only)

```bash
# List all users
curl -X GET https://your-api-url/dev/users \
  -H "X-User-Role: admin"

# Create a new user
curl -X POST https://your-api-url/dev/users \
  -H "Content-Type: application/json" \
  -H "X-User-Role: admin" \
  -d '{
    "username": "newstudent",
    "password": "password123",
    "email": "newstudent@example.com",
    "role": "student",
    "full_name": "New Student",
    "is_active": true
  }'
```

### 3. Test Frontend

1. Navigate to your frontend URL
2. Login with admin credentials: `admin` / `admin123`
3. Click "Users" button in the dashboard
4. Test creating, editing, and deleting users

## User Roles and Permissions

### Admin
- Full access to all features
- Can manage users (create, edit, delete)
- Can create/edit templates
- Can view all results
- Can take quizzes

### Tutor
- Can create/edit templates
- Can view student reports
- Can take quizzes
- Cannot manage users

### Student
- Can take quizzes
- Can view personal results
- Cannot create templates
- Cannot manage users

## Security Considerations

### Current Implementation (Development)
⚠️ The current implementation is suitable for development/demo purposes:
- Passwords stored in plain text
- Simple header-based authentication
- No rate limiting

### Production Recommendations

1. **Password Security**
   ```python
   import bcrypt
   
   # Hash password on creation/update
   hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
   
   # Verify password on login
   if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
       # Login successful
   ```

2. **JWT Authentication**
   - Implement proper JWT token generation on login
   - Use AWS Cognito or custom JWT implementation
   - Include token in Authorization header
   - Validate token on each request

3. **API Gateway Authorization**
   - Use AWS IAM or Lambda authorizers
   - Implement request signing
   - Add API keys for additional security

4. **Rate Limiting**
   - Add rate limiting on login endpoint
   - Use AWS WAF for DDoS protection
   - Implement account lockout after failed attempts

5. **Input Validation**
   - Add comprehensive input validation
   - Sanitize all user inputs
   - Use parameterized queries

6. **Audit Logging**
   - Log all user management operations
   - Track login attempts
   - Monitor for suspicious activity

## Troubleshooting

### Login fails with "Unable to connect to server"
- Check API Gateway URL in frontend/.env
- Verify CORS configuration in Lambda function
- Check browser console for errors

### "Forbidden: Admin access required" error
- Verify user role is set correctly in localStorage
- Check X-User-Role header is being sent
- Ensure user has admin role in database

### Users table not found
- Verify CloudFormation stack deployed successfully
- Check DynamoDB table exists in AWS console
- Verify USERS_TABLE environment variable in Lambda

### Lambda function timeout
- Check CloudWatch logs for errors
- Verify DynamoDB table permissions
- Increase Lambda timeout if needed

## Rollback

If you need to rollback to the previous hardcoded authentication:

1. Revert Login.js to use hardcoded credentials
2. Remove user management routes from App.js
3. Remove Users button from Dashboard
4. Keep the infrastructure (it won't affect existing functionality)

## Next Steps

1. Implement proper password hashing (bcrypt)
2. Add JWT token authentication
3. Implement password reset functionality
4. Add email verification
5. Implement audit logging
6. Add user profile management
7. Implement role-based permissions at API level

## Support

For issues or questions:
1. Check CloudWatch logs for Lambda errors
2. Review API Gateway execution logs
3. Check browser console for frontend errors
4. Verify DynamoDB table data

## Default Credentials

After initialization, use these credentials:

| Username | Password    | Role    |
|----------|-------------|---------|
| admin    | admin123    | admin   |
| tutor    | tutor123    | tutor   |
| student  | student123  | student |

⚠️ **Important**: Change these default passwords in production!
