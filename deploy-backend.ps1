#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Deploy MSC Evaluate Backend Lambda Functions to AWS
.DESCRIPTION
    This script deploys all Lambda functions for the MSC Evaluate application to AWS.
    It checks if functions exist and updates them, or creates new ones if they don't exist.
.PARAMETER Region
    AWS region to deploy to (default: ap-south-1)
.PARAMETER Environment
    Environment name (default: dev)
.PARAMETER JWTSecret
    JWT secret key for authentication
#>

param(
    [string]$Region = "ap-south-1",
    [string]$Environment = "dev",
    [string]$JWTSecret = "msc-evaluate-jwt-secret-change-in-production"
)

# Set error action preference
$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting MSC Evaluate Backend Deployment" -ForegroundColor Green
Write-Host "Region: $Region" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Cyan

# Check if AWS CLI is installed
try {
    aws --version | Out-Null
} catch {
    Write-Error "AWS CLI is not installed or not in PATH. Please install AWS CLI first."
    exit 1
}

# Check AWS credentials
try {
    aws sts get-caller-identity | Out-Null
    Write-Host "✅ AWS credentials verified" -ForegroundColor Green
} catch {
    Write-Error "AWS credentials not configured. Please run 'aws configure' first."
    exit 1
}

# Define Lambda functions configuration
$lambdaFunctions = @(
    @{
        Name = "msc-evaluate-auth-login-$Environment"
        Handler = "login.lambda_handler"
        Runtime = "python3.9"
        Timeout = 30
        Memory = 256
        SourceDir = "backend/auth"
        MainFile = "login.py"
        Description = "User authentication login function"
    },
    @{
        Name = "msc-evaluate-auth-signup-$Environment"
        Handler = "signup.lambda_handler"
        Runtime = "python3.9"
        Timeout = 30
        Memory = 256
        SourceDir = "backend/auth"
        MainFile = "signup.py"
        Description = "User registration signup function"
    },
    @{
        Name = "msc-evaluate-admin-create-user-$Environment"
        Handler = "create_user.lambda_handler"
        Runtime = "python3.9"
        Timeout = 30
        Memory = 256
        SourceDir = "backend/admin"
        MainFile = "create_user.py"
        Description = "Admin function to create users"
    },
    @{
        Name = "msc-evaluate-admin-delete-user-$Environment"
        Handler = "delete_user.lambda_handler"
        Runtime = "python3.9"
        Timeout = 30
        Memory = 256
        SourceDir = "backend/admin"
        MainFile = "delete_user.py"
        Description = "Admin function to delete users"
    },
    @{
        Name = "msc-evaluate-admin-get-users-$Environment"
        Handler = "get_users.lambda_handler"
        Runtime = "python3.9"
        Timeout = 30
        Memory = 256
        SourceDir = "backend/admin"
        MainFile = "get_users.py"
        Description = "Admin function to get all users"
    },
    @{
        Name = "msc-evaluate-admin-get-usage-logs-$Environment"
        Handler = "get_usage_logs.lambda_handler"
        Runtime = "python3.9"
        Timeout = 30
        Memory = 256
        SourceDir = "backend/admin"
        MainFile = "get_usage_logs.py"
        Description = "Admin function to get usage logs"
    },
    @{
        Name = "msc-evaluate-admin-update-user-role-$Environment"
        Handler = "update_user_role.lambda_handler"
        Runtime = "python3.9"
        Timeout = 30
        Memory = 256
        SourceDir = "backend/admin"
        MainFile = "update_user_role.py"
        Description = "Admin function to update user roles"
    },
    @{
        Name = "msc-evaluate-profile-get-profile-$Environment"
        Handler = "get_profile.lambda_handler"
        Runtime = "python3.9"
        Timeout = 30
        Memory = 256
        SourceDir = "backend/profile"
        MainFile = "get_profile.py"
        Description = "Get user profile information"
    },
    @{
        Name = "msc-evaluate-profile-update-profile-$Environment"
        Handler = "update_profile.lambda_handler"
        Runtime = "python3.9"
        Timeout = 30
        Memory = 256
        SourceDir = "backend/profile"
        MainFile = "update_profile.py"
        Description = "Update user profile information"
    },
    @{
        Name = "msc-evaluate-profile-change-password-$Environment"
        Handler = "change_password.lambda_handler"
        Runtime = "python3.9"
        Timeout = 30
        Memory = 256
        SourceDir = "backend/profile"
        MainFile = "change_password.py"
        Description = "Change user password"
    },
    @{
        Name = "msc-evaluate-templates-create-template-$Environment"
        Handler = "create_template.lambda_handler"
        Runtime = "python3.9"
        Timeout = 30
        Memory = 256
        SourceDir = "backend/templates"
        MainFile = "create_template.py"
        Description = "Create quiz templates"
    },
    @{
        Name = "msc-evaluate-templates-get-templates-$Environment"
        Handler = "get_templates.lambda_handler"
        Runtime = "python3.9"
        Timeout = 30
        Memory = 256
        SourceDir = "backend/templates"
        MainFile = "get_templates.py"
        Description = "Get quiz templates"
    },
    @{
        Name = "msc-evaluate-quiz-take-quiz-$Environment"
        Handler = "take_quiz.lambda_handler"
        Runtime = "python3.9"
        Timeout = 30
        Memory = 256
        SourceDir = "backend/quiz"
        MainFile = "take_quiz.py"
        Description = "Take quiz functionality"
    },
    @{
        Name = "msc-evaluate-quiz-submit-quiz-$Environment"
        Handler = "submit_quiz.lambda_handler"
        Runtime = "python3.9"
        Timeout = 60
        Memory = 512
        SourceDir = "backend/quiz"
        MainFile = "submit_quiz.py"
        Description = "Submit quiz and get AI evaluation"
    },
    @{
        Name = "msc-evaluate-reports-get-all-reports-$Environment"
        Handler = "get_all_reports.lambda_handler"
        Runtime = "python3.9"
        Timeout = 30
        Memory = 256
        SourceDir = "backend/reports"
        MainFile = "get_all_reports.py"
        Description = "Get all reports for admin"
    },
    @{
        Name = "msc-evaluate-reports-get-user-reports-$Environment"
        Handler = "get_user_reports.lambda_handler"
        Runtime = "python3.9"
        Timeout = 30
        Memory = 256
        SourceDir = "backend/reports"
        MainFile = "get_user_reports.py"
        Description = "Get user-specific reports"
    },
    @{
        Name = "msc-evaluate-reports-get-template-reports-$Environment"
        Handler = "get_template_reports.lambda_handler"
        Runtime = "python3.9"
        Timeout = 30
        Memory = 256
        SourceDir = "backend/reports"
        MainFile = "get_template_reports.py"
        Description = "Get template-specific reports"
    },
    @{
        Name = "msc-evaluate-ai-scorer-$Environment"
        Handler = "lambda_function.lambda_handler"
        Runtime = "python3.9"
        Timeout = 120
        Memory = 1024
        SourceDir = "backend/MSC_Evaluate"
        MainFile = "lambda_function.py"
        Description = "AI-powered answer scoring using AWS Bedrock"
    }
)

# Environment variables for Lambda functions
$envVars = @{
    "JWT_SECRET" = $JWTSecret
    "USERS_TABLE" = "msc-evaluate-users-$Environment"
    "TEMPLATES_TABLE" = "msc-evaluate-templates-$Environment"
    "QUIZ_RESULTS_TABLE" = "msc-evaluate-quiz-results-$Environment"
    "ENVIRONMENT" = $Environment
}

# IAM Role ARN (will be created if doesn't exist)
$roleName = "msc-evaluate-lambda-role-$Environment"
$roleArn = ""

# Function to check if Lambda function exists
function Test-LambdaFunction {
    param([string]$FunctionName)
    try {
        aws lambda get-function --function-name $FunctionName --region $Region 2>$null | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Function to create IAM role for Lambda
function New-LambdaRole {
    Write-Host "Creating IAM role for Lambda functions..." -ForegroundColor Yellow
    
    # Create trust policy file
    $trustPolicyContent = @'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
'@

    # Create IAM policy file
    $policyContent = @'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem",
                "dynamodb:Scan",
                "dynamodb:Query"
            ],
            "Resource": [
                "arn:aws:dynamodb:*:*:table/msc-evaluate-*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            "Resource": "*"
        }
    ]
}
'@

    try {
        # Check if role exists
        $existingRole = aws iam get-role --role-name $roleName 2>$null | ConvertFrom-Json
        if ($existingRole) {
            Write-Host "IAM role already exists: $roleName" -ForegroundColor Green
            return $existingRole.Role.Arn
        }
    } catch {
        # Role doesn't exist, create it
    }

    # Create role
    $trustPolicyContent | Out-File -FilePath "trust-policy.json" -Encoding utf8
    $role = aws iam create-role --role-name $roleName --assume-role-policy-document file://trust-policy.json | ConvertFrom-Json
    
    # Create and attach policy
    $policyName = "msc-evaluate-lambda-policy-$Environment"
    $policyContent | Out-File -FilePath "lambda-policy.json" -Encoding utf8
    
    $policy = aws iam create-policy --policy-name $policyName --policy-document file://lambda-policy.json 2>$null | ConvertFrom-Json
    if (-not $policy) {
        # Policy might already exist, get it
        $accountId = (aws sts get-caller-identity | ConvertFrom-Json).Account
        $policyArn = "arn:aws:iam::$accountId:policy/$policyName"
    } else {
        $policyArn = $policy.Policy.Arn
    }
    
    aws iam attach-role-policy --role-name $roleName --policy-arn $policyArn
    
    # Clean up temp files
    Remove-Item "trust-policy.json" -ErrorAction SilentlyContinue
    Remove-Item "lambda-policy.json" -ErrorAction SilentlyContinue
    
    # Wait for role to be available
    Write-Host "Waiting for IAM role to be available..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    Write-Host "IAM role created: $roleName" -ForegroundColor Green
    return $role.Role.Arn
}

# Function to create deployment package
function New-DeploymentPackage {
    param(
        [hashtable]$Function
    )
    
    $packageName = "$($Function.Name).zip"
    $tempDir = "temp_$($Function.Name)"
    
    Write-Host "Creating deployment package for $($Function.Name)..." -ForegroundColor Yellow
    
    # Create temp directory
    if (Test-Path $tempDir) {
        Remove-Item $tempDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $tempDir | Out-Null
    
    # Copy main function file
    $mainFilePath = Join-Path $Function.SourceDir $Function.MainFile
    if (Test-Path $mainFilePath) {
        Copy-Item $mainFilePath -Destination $tempDir
    } else {
        Write-Warning "Main file not found: $mainFilePath"
        return $null
    }
    
    # Copy shared utilities
    if (Test-Path "backend/shared") {
        Copy-Item "backend/shared/*" -Destination $tempDir -Recurse
    }
    
    # Copy requirements and install dependencies
    $requirementsPath = Join-Path $Function.SourceDir "requirements.txt"
    if (Test-Path $requirementsPath) {
        Copy-Item $requirementsPath -Destination $tempDir
        
        # Install Python dependencies
        Push-Location $tempDir
        try {
            pip install -r requirements.txt -t . --quiet
        } catch {
            Write-Warning "Failed to install dependencies for $($Function.Name)"
        }
        Pop-Location
    } else {
        # Use global requirements
        if (Test-Path "backend/requirements.txt") {
            Copy-Item "backend/requirements.txt" -Destination $tempDir
            Push-Location $tempDir
            try {
                pip install -r requirements.txt -t . --quiet
            } catch {
                Write-Warning "Failed to install global dependencies for $($Function.Name)"
            }
            Pop-Location
        }
    }
    
    # Create ZIP package
    Push-Location $tempDir
    if (Get-Command "7z" -ErrorAction SilentlyContinue) {
        7z a -tzip "../$packageName" * | Out-Null
    } else {
        Compress-Archive -Path "*" -DestinationPath "../$packageName" -Force
    }
    Pop-Location
    
    # Clean up temp directory
    Remove-Item $tempDir -Recurse -Force
    
    if (Test-Path $packageName) {
        Write-Host "Package created: $packageName" -ForegroundColor Green
        return $packageName
    } else {
        Write-Error "Failed to create package: $packageName"
        return $null
    }
}

# Function to create or update Lambda function
function Deploy-LambdaFunction {
    param(
        [hashtable]$Function,
        [string]$RoleArn,
        [string]$PackagePath
    )
    
    $functionExists = Test-LambdaFunction -FunctionName $Function.Name
    
    # Prepare environment variables
    $envVarsString = ""
    $envVars.GetEnumerator() | ForEach-Object {
        if ($envVarsString) { $envVarsString += "," }
        $envVarsString += "$($_.Key)=$($_.Value)"
    }
    
    if ($functionExists) {
        Write-Host "Updating existing function: $($Function.Name)" -ForegroundColor Yellow
        
        # Update function code
        aws lambda update-function-code `
            --function-name $Function.Name `
            --zip-file "fileb://$PackagePath" `
            --region $Region | Out-Null
        
        # Update function configuration
        aws lambda update-function-configuration `
            --function-name $Function.Name `
            --runtime $Function.Runtime `
            --handler $Function.Handler `
            --timeout $Function.Timeout `
            --memory-size $Function.Memory `
            --environment "Variables={$envVarsString}" `
            --region $Region | Out-Null
            
        Write-Host "Function updated: $($Function.Name)" -ForegroundColor Green
    } else {
        Write-Host "Creating new function: $($Function.Name)" -ForegroundColor Yellow
        
        aws lambda create-function `
            --function-name $Function.Name `
            --runtime $Function.Runtime `
            --role $RoleArn `
            --handler $Function.Handler `
            --zip-file "fileb://$PackagePath" `
            --timeout $Function.Timeout `
            --memory-size $Function.Memory `
            --description $Function.Description `
            --environment "Variables={$envVarsString}" `
            --region $Region | Out-Null
            
        Write-Host "Function created: $($Function.Name)" -ForegroundColor Green
    }
}

# Main deployment process
try {
    # Create IAM role
    $roleArn = New-LambdaRole
    
    # Deploy each Lambda function
    foreach ($function in $lambdaFunctions) {
        Write-Host "Processing function: $($function.Name)" -ForegroundColor Cyan
        
        # Create deployment package
        $packagePath = New-DeploymentPackage -Function $function
        if (-not $packagePath) {
            Write-Warning "Skipping $($function.Name) due to packaging error"
            continue
        }
        
        # Deploy function
        Deploy-LambdaFunction -Function $function -RoleArn $roleArn -PackagePath $packagePath
        
        # Clean up package
        Remove-Item $packagePath -ErrorAction SilentlyContinue
    }
    
    Write-Host "Backend deployment completed successfully!" -ForegroundColor Green
    Write-Host "Region: $Region" -ForegroundColor Cyan
    Write-Host "Environment: $Environment" -ForegroundColor Cyan
    Write-Host "Functions deployed: $($lambdaFunctions.Count)" -ForegroundColor Cyan
    
} catch {
    Write-Error "Deployment failed: $($_.Exception.Message)"
    exit 1
}