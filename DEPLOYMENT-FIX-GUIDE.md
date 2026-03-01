# Deployment Fix Guide - User Management

## Problem
The user CRUD Lambda function hasn't been deployed yet, causing 404 errors when trying to access `/users` endpoint.

## Solution

### Step 1: Deploy User CRUD Lambda Function

Run the user deployment script from the `cloudformation` directory:

```powershell
cd cloudformation
.\deploy-users.ps1 -Environment "dev" -Region "ap-south-1"
```

This script will:
- Package the `user_crud.py` Lambda function
- Deploy it to AWS Lambda (`msc-evaluate-user-crud-dev`)
- Initialize default users in DynamoDB

### Step 2: Verify Deployment

After deployment, verify the Lambda function exists:

```powershell
aws lambda get-function --function-name msc-evaluate-user-crud-dev --region ap-south-1
```

### Step 3: Test the API

Test the users endpoint:

```powershell
# Test GET /users (should require admin role)
curl https://48c11a5co1.execute-api.ap-south-1.amazonaws.com/dev/users

# Test login
curl -X POST https://48c11a5co1.execute-api.ap-south-1.amazonaws.com/dev/users/login `
  -H "Content-Type: application/json" `
  -d '{"username":"admin","password":"admin123"}'
```

### Step 4: Verify Frontend

1. Open the application: https://aiassessment.in/login
2. Login with default credentials:
   - Admin: `admin` / `admin123`
   - Tutor: `tutor` / `tutor123`
   - Student: `student` / `student123`

3. Navigate to User Management (admin only)
4. You should see the three default users

## Default Users Created

The deployment script automatically creates these users in DynamoDB:

| Username | Password | Role | Email |
|----------|----------|------|-------|
| admin | admin123 | admin | admin@example.com |
| tutor | tutor123 | tutor | tutor@example.com |
| student | student123 | student | student@example.com |

## Features Implemented

### User Management (Admin Only)
- ✅ List all users with role filtering
- ✅ Create new users
- ✅ Edit existing users
- ✅ Delete users
- ✅ Activate/deactivate users

### Authentication
- ✅ Login with username/password
- ✅ Role-based access control
- ✅ Session management with localStorage

### Backend (DynamoDB + Lambda)
- ✅ User CRUD operations
- ✅ Password authentication (plain text - should be hashed in production)
- ✅ Role validation (admin, tutor, student)
- ✅ Admin-only endpoints protection

## Security Notes

⚠️ **Important for Production:**
1. Passwords are stored in plain text - implement bcrypt/argon2 hashing
2. Add JWT tokens for session management
3. Implement rate limiting on login endpoint
4. Add password complexity requirements
5. Enable CloudWatch logging for audit trails

## Troubleshooting

### Issue: 404 on /users endpoint
**Solution:** Run the deploy-users.ps1 script

### Issue: 403 Forbidden on user operations
**Solution:** Ensure you're logged in as admin. The frontend sends `X-User-Role` header.

### Issue: Users not showing in User Management
**Solution:** Run init_users.py manually:
```powershell
cd backend/users
python init_users.py msc-evaluate-users-dev
```

### Issue: CORS errors
**Solution:** The Lambda function already includes CORS headers. Clear browser cache and retry.

## Next Steps

1. ✅ Deploy user CRUD Lambda
2. ✅ Initialize default users
3. Test login functionality
4. Test user management (create, edit, delete)
5. Implement password hashing (recommended)
6. Add JWT authentication (recommended)
