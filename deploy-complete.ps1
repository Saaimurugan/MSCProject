#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Complete MSC Evaluate Application Deployment with Infrastructure
.DESCRIPTION
    This script deploys the complete MSC Evaluate application including:
    1. DynamoDB tables
    2. Backend Lambda functions
    3. API Gateway with CORS
    4. Frontend to S3 bucket
.PARAMETER Region
    AWS region (default: ap-south-1)
.PARAMETER Environment
    Environment name (default: dev)
.PARAMETER BucketName
    S3 bucket name for frontend (default: msc-evaluate-frontend-dev-127510141)
.PARAMETER JWTSecret
    JWT secret key for authentication
.PARAMETER SkipDatabase
    Skip DynamoDB table creation
.PARAMETER SkipBackend
    Skip backend deployment
.PARAMETER SkipApi
    Skip API Gateway deployment
.PARAMETER SkipFrontend
    Skip frontend deployment
#>

param(
    [string]$Region = "ap-south-1",
    [string]$Environment = "dev",
    [string]$BucketName = "msc-evaluate-frontend-dev-127510141",
    [string]$JWTSecret = "msc-evaluate-jwt-secret-change-in-production-$(Get-Random)",
    [switch]$SkipDatabase,
    [switch]$SkipBackend,
    [switch]$SkipApi,
    [switch]$SkipFrontend
)

# Set error action preference
$ErrorActionPreference = "Stop"

Write-Host "MSC EVALUATE - COMPLETE DEPLOYMENT" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host 'Region: ' $Region -ForegroundColor Cyan
Write-Host 'Environment: ' $Environment -ForegroundColor Cyan
Write-Host 'S3 Bucket: ' $BucketName -ForegroundColor Cyan
Write-Host 'JWT Secret: ' $JWTSecret.Substring(0, 20) '...' -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Green

# Check prerequisites
function Test-Prerequisites {
    Write-Host "`n🔍 Checking prerequisites..." -ForegroundColor Yellow
    
    $errors = @()
    
    # Check AWS CLI
    try {
        $awsVersion = aws --version 2>&1
        Write-Host "✅ AWS CLI: $awsVersion" -ForegroundColor Green
    } catch {
        $errors += "AWS CLI is not installed or not in PATH"
    }
    
    # Check AWS credentials
    try {
        $identity = aws sts get-caller-identity | ConvertFrom-Json
        Write-Host "✅ AWS Account: $($identity.Account)" -ForegroundColor Green
        Write-Host "✅ AWS User: $($identity.Arn)" -ForegroundColor Green
    } catch {
        $errors += "AWS credentials not configured. Please run 'aws configure'"
    }
    
    # Check Node.js (only if not skipping frontend)
    if (-not $SkipFrontend) {
        try {
            $nodeVersion = node --version
            $npmVersion = npm --version
            Write-Host "✅ Node.js: $nodeVersion" -ForegroundColor Green
            Write-Host "✅ npm: $npmVersion" -ForegroundColor Green
        } catch {
            $errors += "Node.js and npm are required for frontend deployment"
        }
    }
    
    # Check Python (only if not skipping backend)
    if (-not $SkipBackend) {
        try {
            $pythonVersion = python --version 2>&1
            $pipVersion = pip --version 2>&1
            Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
            Write-Host "✅ pip: $pipVersion" -ForegroundColor Green
        } catch {
            $errors += "Python and pip are required for backend deployment"
        }
    }
    
    # Check if project structure exists
    $requiredPaths = @("backend", "frontend")
    foreach ($path in $requiredPaths) {
        if (Test-Path $path) {
            Write-Host "✅ Found $path directory" -ForegroundColor Green
        } else {
            $errors += "Required directory not found: $path"
        }
    }
    
    if ($errors.Count -gt 0) {
        Write-Host "`n❌ Prerequisites check failed:" -ForegroundColor Red
        foreach ($error in $errors) {
            Write-Host "  - $error" -ForegroundColor Red
        }
        exit 1
    }
    
    Write-Host "All prerequisites satisfied" -ForegroundColor Green
}

# Function to display deployment summary
function Show-DeploymentSummary {
    param(
        [string]$ApiUrl,
        [string]$WebsiteUrl,
        [int]$TableCount,
        [int]$LambdaCount,
        [int]$EndpointCount,
        [timespan]$DeploymentTime
    )
    
    Write-Host "`n🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!" -ForegroundColor Green
    Write-Host "=====================================" -ForegroundColor Green
    Write-Host "Environment: $Environment" -ForegroundColor Cyan
    Write-Host "Region: $Region" -ForegroundColor Cyan
    Write-Host "Deployment Time: $($DeploymentTime.ToString('mm\:ss'))" -ForegroundColor Cyan
    Write-Host ""
    
    if (-not $SkipDatabase) {
        Write-Host "Database:" -ForegroundColor Blue
        Write-Host "  DynamoDB Tables: $TableCount created" -ForegroundColor White
    }
    
    if (-not $SkipBackend) {
        Write-Host "Backend:" -ForegroundColor Blue
        Write-Host "  Lambda Functions: $LambdaCount deployed" -ForegroundColor White
    }
    
    if (-not $SkipApi) {
        Write-Host "API Gateway:" -ForegroundColor Blue
        Write-Host "  API URL: $ApiUrl" -ForegroundColor White
        Write-Host "  Endpoints: $EndpointCount created" -ForegroundColor White
    }
    
    if (-not $SkipFrontend) {
        Write-Host "Frontend:" -ForegroundColor Blue
        Write-Host "  S3 Bucket: $BucketName" -ForegroundColor White
        Write-Host "  Website URL: $WebsiteUrl" -ForegroundColor White
    }
    
    Write-Host ""
    Write-Host "Security Information:" -ForegroundColor Yellow
    Write-Host "  JWT Secret: $JWTSecret" -ForegroundColor White
    Write-Host "  Default Admin: admin@msc-evaluate.com / Admin123!" -ForegroundColor White
    Write-Host "WARNING: Change default credentials immediately!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Yellow
    Write-Host "  1. Test the application: $WebsiteUrl" -ForegroundColor White
    Write-Host "  2. Login with admin credentials and change password" -ForegroundColor White
    Write-Host "  3. Create quiz templates" -ForegroundColor White
    Write-Host "  4. Set up monitoring and alerts" -ForegroundColor White
    Write-Host "  5. Configure backup policies" -ForegroundColor White
    Write-Host "=====================================" -ForegroundColor Green
}

# Function to create deployment log
function New-DeploymentLog {
    param(
        [string]$LogContent
    )
    
    $logFile = "deployment-log-$Environment-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
    $LogContent | Out-File -FilePath $logFile -Encoding utf8
    Write-Host "Deployment log saved: $logFile" -ForegroundColor Cyan
}

# Main deployment process
try {
    # Check prerequisites
    Test-Prerequisites
    
    $deploymentStart = Get-Date
    $deploymentLog = @()
    $deploymentLog += 'MSC Evaluate Deployment Log'
    $deploymentLog += 'Started: ' + $deploymentStart
    $deploymentLog += 'Region: ' + $Region
    $deploymentLog += 'Environment: ' + $Environment
    $deploymentLog += ''
    
    $apiUrl = ""
    $websiteUrl = ""
    $tableCount = 0
    $lambdaCount = 0
    $endpointCount = 0
    
    # Step 0: Create DynamoDB Tables
    if (-not $SkipDatabase) {
        Write-Host "STEP 0: Creating DynamoDB Tables" -ForegroundColor Blue
        Write-Host "===================================" -ForegroundColor Blue
        
        & .\create-dynamodb-tables.ps1 -Region $Region -Environment $Environment
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error "DynamoDB table creation failed"
            exit 1
        }
        
        $tableCount = 3  # Users, Templates, Quiz Results
        $deploymentLog += 'DynamoDB tables created: ' + $tableCount
        
        Write-Host "✅ DynamoDB tables created" -ForegroundColor Green
    } else {
        Write-Host "Skipping DynamoDB table creation" -ForegroundColor Yellow
        $deploymentLog += 'Skipped DynamoDB table creation'
    }
    
    # Step 1: Deploy Backend Lambda Functions
    if (-not $SkipBackend) {
        Write-Host "STEP 1: Deploying Backend Lambda Functions" -ForegroundColor Blue
        Write-Host "=============================================" -ForegroundColor Blue
        
        & .\deploy-backend.ps1 -Region $Region -Environment $Environment -JWTSecret $JWTSecret
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Backend deployment failed"
            exit 1
        }
        
        $lambdaCount = 18  # Based on the functions defined in deploy-backend.ps1
        $deploymentLog += 'Lambda functions deployed: ' + $lambdaCount
        
        Write-Host "✅ Backend deployment completed" -ForegroundColor Green
    } else {
        Write-Host "Skipping backend deployment" -ForegroundColor Yellow
        $deploymentLog += 'Skipped backend deployment'
    }
    
    # Step 2: Deploy API Gateway
    if (-not $SkipApi) {
        Write-Host "STEP 2: Deploying API Gateway" -ForegroundColor Blue
        Write-Host "================================" -ForegroundColor Blue
        
        & .\deploy-api.ps1 -Region $Region -Environment $Environment -StageName $Environment
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error "API Gateway deployment failed"
            exit 1
        }
        
        # Get API URL
        try {
            $apis = aws apigateway get-rest-apis --region $Region | ConvertFrom-Json
            $api = $apis.items | Where-Object { $_.name -eq "msc-evaluate-api-$Environment" }
            if ($api) {
                $apiUrl = "https://$($api.id).execute-api.$Region.amazonaws.com/$Environment"
                $deploymentLog += 'API Gateway deployed: ' + $apiUrl
            }
        } catch {
            Write-Warning "Could not retrieve API URL"
            $deploymentLog += 'Could not retrieve API URL'
        }
        
        $endpointCount = 18  # Based on the endpoints defined in deploy-api.ps1
        
        Write-Host "✅ API Gateway deployment completed" -ForegroundColor Green
    } else {
        Write-Host "Skipping API Gateway deployment" -ForegroundColor Yellow
        $deploymentLog += 'Skipped API Gateway deployment'
    }
    
    # Step 3: Deploy Frontend
    if (-not $SkipFrontend) {
        Write-Host "STEP 3: Deploying Frontend to S3" -ForegroundColor Blue
        Write-Host "===================================" -ForegroundColor Blue
        
        $frontendArgs = @(
            "-BucketName", $BucketName,
            "-Region", $Region,
            "-Environment", $Environment
        )
        
        if ($apiUrl) {
            $frontendArgs += @("-ApiUrl", $apiUrl)
        }
        
        & .\deploy-frontend.ps1 @frontendArgs
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Frontend deployment failed"
            exit 1
        }
        
        $websiteUrl = "http://$BucketName.s3-website-$Region.amazonaws.com"
        $deploymentLog += 'Frontend deployed: ' + $websiteUrl
        
        Write-Host "✅ Frontend deployment completed" -ForegroundColor Green
    } else {
        Write-Host 'Skipping frontend deployment' -ForegroundColor Yellow
        $deploymentLog += 'Skipped frontend deployment'
    }
    
    # Calculate deployment time
    $deploymentEnd = Get-Date
    $deploymentTime = $deploymentEnd - $deploymentStart
    $deploymentLog += ''
    $deploymentLog += 'Completed: ' + $deploymentEnd
    $deploymentLog += 'Duration: ' + $deploymentTime.ToString('mm\:ss')
    
    # Show summary
    Show-DeploymentSummary -ApiUrl $apiUrl -WebsiteUrl $websiteUrl -TableCount $tableCount -LambdaCount $lambdaCount -EndpointCount $endpointCount -DeploymentTime $deploymentTime
    
    # Create deployment log
    New-DeploymentLog -LogContent ($deploymentLog -join [Environment]::NewLine)
    
} catch {
    Write-Host 'DEPLOYMENT FAILED' -ForegroundColor Red
        Write-Host 'Error: ' $_.Exception.Message -ForegroundColor Red
    Write-Host 'Please check the logs above for details.' -ForegroundColor Red
    
    # Create error log
    $errorLog = @()
    $errorLog += 'MSC Evaluate Deployment FAILED'
    $errorLog += 'Time: ' + (Get-Date)
    $errorLog += 'Error: ' + $_.Exception.Message
    $errorLog += 'Stack Trace: ' + $_.ScriptStackTrace
    
    New-DeploymentLog -LogContent ($errorLog -join [Environment]::NewLine)
    
    exit 1
}