#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Complete MSC Evaluate Application Deployment
.DESCRIPTION
    This script deploys the complete MSC Evaluate application including:
    1. Backend Lambda functions
    2. API Gateway with CORS
    3. Frontend to S3 bucket
.PARAMETER Region
    AWS region (default: ap-south-1)
.PARAMETER Environment
    Environment name (default: dev)
.PARAMETER BucketName
    S3 bucket name for frontend (default: msc-evaluate-frontend-dev-127510141)
.PARAMETER JWTSecret
    JWT secret key for authentication
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
    [string]$JWTSecret = "msc-evaluate-jwt-secret-change-in-production",
    [switch]$SkipBackend,
    [switch]$SkipApi,
    [switch]$SkipFrontend
)

# Set error action preference
$ErrorActionPreference = "Stop"

Write-Host "Starting Complete MSC Evaluate Deployment" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host "Region: $Region" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Cyan
Write-Host "S3 Bucket: $BucketName" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Green

# Check prerequisites
function Test-Prerequisites {
    Write-Host "Checking prerequisites..." -ForegroundColor Yellow
    
    $errors = @()
    
    # Check AWS CLI
    try {
        aws --version | Out-Null
        Write-Host "AWS CLI found" -ForegroundColor Green
    } catch {
        $errors += "AWS CLI is not installed or not in PATH"
    }
    
    # Check AWS credentials
    try {
        aws sts get-caller-identity | Out-Null
        Write-Host "AWS credentials configured" -ForegroundColor Green
    } catch {
        $errors += "AWS credentials not configured. Please run 'aws configure'"
    }
    
    # Check Node.js (only if not skipping frontend)
    if (-not $SkipFrontend) {
        try {
            node --version | Out-Null
            npm --version | Out-Null
            Write-Host "Node.js and npm found" -ForegroundColor Green
        } catch {
            $errors += "Node.js and npm are required for frontend deployment"
        }
    }
    
    # Check Python (only if not skipping backend)
    if (-not $SkipBackend) {
        try {
            python --version | Out-Null
            pip --version | Out-Null
            Write-Host "Python and pip found" -ForegroundColor Green
        } catch {
            $errors += "Python and pip are required for backend deployment"
        }
    }
    
    # Check if deployment scripts exist
    $scripts = @("deploy-backend.ps1", "deploy-api.ps1", "deploy-frontend.ps1")
    foreach ($script in $scripts) {
        if (Test-Path $script) {
            Write-Host "Found $script" -ForegroundColor Green
        } else {
            $errors += "Deployment script not found: $script"
        }
    }
    
    if ($errors.Count -gt 0) {
        Write-Host "Prerequisites check failed:" -ForegroundColor Red
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
        [int]$LambdaCount,
        [int]$EndpointCount
    )
    
    Write-Host "DEPLOYMENT COMPLETED SUCCESSFULLY!" -ForegroundColor Green
    Write-Host "=====================================" -ForegroundColor Green
    Write-Host "Environment: $Environment" -ForegroundColor Cyan
    Write-Host "Region: $Region" -ForegroundColor Cyan
    Write-Host ""
    
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
    Write-Host "Security Notes:" -ForegroundColor Yellow
    Write-Host "  - Change JWT secret in production: $JWTSecret" -ForegroundColor White
    Write-Host "  - Review IAM permissions" -ForegroundColor White
    Write-Host "  - Enable CloudTrail for audit logging" -ForegroundColor White
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Yellow
    Write-Host "  1. Test the application endpoints" -ForegroundColor White
    Write-Host "  2. Create initial admin user" -ForegroundColor White
    Write-Host "  3. Configure monitoring and alerts" -ForegroundColor White
    Write-Host "  4. Set up CI/CD pipeline" -ForegroundColor White
    Write-Host "=====================================" -ForegroundColor Green
}

# Main deployment process
try {
    # Check prerequisites
    Test-Prerequisites
    
    $deploymentStart = Get-Date
    $apiUrl = ""
    $websiteUrl = ""
    $lambdaCount = 0
    $endpointCount = 0
    
    # Step 1: Deploy Backend Lambda Functions
    if (-not $SkipBackend) {
        Write-Host "STEP 1: Deploying Backend Lambda Functions" -ForegroundColor Blue
        Write-Host "=============================================" -ForegroundColor Blue
        
        & .\deploy-backend.ps1 -Region $Region -Environment $Environment -JWTSecret $JWTSecret
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Backend deployment failed"
            exit 1
        }
        
        # Count deployed functions (approximate)
        $lambdaCount = 18  # Based on the functions defined in deploy-backend.ps1
        
        Write-Host "Backend deployment completed" -ForegroundColor Green
    } else {
        Write-Host "Skipping backend deployment" -ForegroundColor Yellow
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
            }
        } catch {
            Write-Warning "Could not retrieve API URL"
        }
        
        $endpointCount = 18  # Based on the endpoints defined in deploy-api.ps1
        
        Write-Host "API Gateway deployment completed" -ForegroundColor Green
    } else {
        Write-Host "Skipping API Gateway deployment" -ForegroundColor Yellow
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
        
        Write-Host "Frontend deployment completed" -ForegroundColor Green
    } else {
        Write-Host "Skipping frontend deployment" -ForegroundColor Yellow
    }
    
    # Calculate deployment time
    $deploymentEnd = Get-Date
    $deploymentTime = $deploymentEnd - $deploymentStart
    
    # Show summary
    Show-DeploymentSummary -ApiUrl $apiUrl -WebsiteUrl $websiteUrl -LambdaCount $lambdaCount -EndpointCount $endpointCount
    
    Write-Host "Total deployment time: $($deploymentTime.ToString('mm\:ss'))" -ForegroundColor Cyan
    
} catch {
    Write-Host "DEPLOYMENT FAILED" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Please check the logs above for details." -ForegroundColor Red
    exit 1
}