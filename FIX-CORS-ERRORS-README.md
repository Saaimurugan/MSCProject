# Fix CORS Errors - Quick Start Guide

## Problem
Your AI Assessment application shows CORS and network errors when trying to access the backend API.

## Quick Fix (3 Steps)

### Step 1: Check Current Status
```powershell
.\check-deployment-status.ps1
```
This will show you what's deployed and what's missing.

### Step 2: Update Lambda Functions
```powershell
.\update-lambdas.ps1
```
This will update all Lambda functions with the latest code and redeploy the API Gateway.

### Step 3: Test the API
```powershell
.\test-api.ps1
```
This will test all API endpoints to verify they're working.

### Step 4: Clear Browser Cache & Refresh
1. Open your browser
2. Press `Ctrl + Shift + Delete`
3. Clear cached images and files
4. Refresh the application (`Ctrl + F5`)

## Expected Results

After running these scripts, you should see:
- ✓ All Lambda functions updated
- ✓ API Gateway redeployed
- ✓ All API tests passing
- ✓ No CORS errors in browser console
- ✓ Login works with admin/admin123
- ✓ Dashboard loads with templates

## Scripts Overview

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `check-deployment-status.ps1` | Check what's deployed | First step - diagnose issues |
| `update-lambdas.ps1` | Update Lambda code | When Lambda functions need updating |
| `test-api.ps1` | Test API endpoints | Verify API is working |

## Troubleshooting

### If Scripts Fail

1. **AWS CLI not configured**:
   ```powershell
   aws configure
   ```
   Enter your AWS credentials and region (ap-south-1).

2. **Permission denied**:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

3. **Stack not deployed**:
   ```powershell
   cd cloudformation
   .\deploy.ps1
   ```

### If API Tests Fail

1. Check CloudWatch Logs:
   ```powershell
   aws logs tail /aws/lambda/msc-evaluate-user-crud-dev --follow --region ap-south-1
   ```

2. Verify users exist:
   ```powershell
   cd cloudformation
   .\deploy-users.ps1
   ```

3. Check DynamoDB tables:
   ```powershell
   aws dynamodb list-tables --region ap-south-1
   ```

### If Browser Still Shows Errors

1. **Hard refresh**: `Ctrl + Shift + R` or `Ctrl + F5`
2. **Clear all cache**: `Ctrl + Shift + Delete`
3. **Try incognito mode**: `Ctrl + Shift + N`
4. **Check console**: F12 → Console tab for specific errors

## Common Error Messages

### "Access to XMLHttpRequest has been blocked by CORS policy"
**Fix**: Run `.\update-lambdas.ps1` to update Lambda functions with CORS headers.

### "Failed to load templates"
**Fix**: 
1. Run `.\update-lambdas.ps1`
2. Create a test template as admin

### "Login failed"
**Fix**: 
1. Run `.\cloudformation\deploy-users.ps1` to initialize users
2. Use credentials: admin/admin123

### "Network Error"
**Fix**: Check CloudWatch Logs for Lambda errors.

## Detailed Documentation

For more detailed information, see:
- `CORS-ERROR-RESOLUTION.md` - Complete resolution guide
- `API-CORS-FIX-GUIDE.md` - Detailed API fix guide
- `cloudformation/DEPLOYMENT-CHECKLIST.md` - Full deployment guide

## Support Workflow

If issues persist after running all scripts:

1. **Collect Information**:
   ```powershell
   .\check-deployment-status.ps1 > deployment-status.txt
   .\test-api.ps1 > api-test-results.txt
   ```

2. **Check Logs**:
   ```powershell
   aws logs tail /aws/lambda/msc-evaluate-user-crud-dev --region ap-south-1 > lambda-logs.txt
   ```

3. **Verify Stack**:
   ```powershell
   aws cloudformation describe-stacks --stack-name msc-evaluate-stack-dev --region ap-south-1 > stack-info.txt
   ```

4. Review the collected files for specific error messages.

## Success Indicators

You'll know everything is working when:
- ✓ `check-deployment-status.ps1` shows all resources deployed
- ✓ `test-api.ps1` shows all tests passing
- ✓ Browser console has no CORS errors
- ✓ Login page loads without errors
- ✓ Dashboard shows "Welcome to AI Assessment!"
- ✓ Templates load (or show "No templates found" if none exist)
- ✓ Admin can create templates
- ✓ Students can take quizzes

## Next Steps After Fix

Once CORS errors are resolved:

1. **Test Login**: Try all three user types (admin, tutor, student)
2. **Create Template**: As admin, create a test quiz template
3. **Take Quiz**: As student, take the quiz
4. **View Results**: As admin, view quiz results
5. **User Management**: As admin, create/edit users

## Quick Reference

### Default Credentials
- Admin: `admin` / `admin123`
- Tutor: `tutor` / `tutor123`
- Student: `student` / `student123`

### API URL
```
https://48c11a5co1.execute-api.ap-south-1.amazonaws.com/dev
```

### Frontend URL
```
http://msc-evaluate-frontend-dev.s3-website.ap-south-1.amazonaws.com
```

### AWS Region
```
ap-south-1 (Mumbai)
```

## Need More Help?

Check these files in order:
1. This file (FIX-CORS-ERRORS-README.md)
2. CORS-ERROR-RESOLUTION.md
3. API-CORS-FIX-GUIDE.md
4. cloudformation/DEPLOYMENT-CHECKLIST.md
5. cloudformation/README.md
