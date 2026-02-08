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
Write-Host "Region: $Region" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Cyan
Write-Host "S3 Bucket: $BucketName" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Green

# Main deployment process
try {
    $deploymentStart = Get-Date
    
    # Step 0: Create DynamoDB Tables
    if (-not $SkipDatabase) {
        Write-Host "STEP 0: Creating DynamoDB Tables" -ForegroundColor Blue
        Write-Host "===================================" -ForegroundColor Blue
        
        & .\create-dynamodb-tables.ps1 -Region $Region -Environment $Environment
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error "DynamoDB table creation failed"
            exit 1
        }
        
        Write-Host "DynamoDB tables created" -ForegroundColor Green
    } else {
        Write-Host "Skipping DynamoDB table creation" -ForegroundColor Yellow
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
        
        Write-Host "API Gateway deployment completed" -ForegroundColor Green
    } else {
        Write-Host "Skipping API Gateway deployment" -ForegroundColor Yellow
    }
    
    # Step 3: Deploy Frontend
    if (-not $SkipFrontend) {
        Write-Host "STEP 3: Deploying Frontend to S3" -ForegroundColor Blue
        Write-Host "===================================" -ForegroundColor Blue
        
        # Get API URL for frontend
        $apiUrl = ""
        try {
            $apis = aws apigateway get-rest-apis --region $Region | ConvertFrom-Json
            $api = $apis.items | Where-Object { $_.name -eq "msc-evaluate-api-$Environment" }
            if ($api) {
                $apiUrl = "https://$($api.id).execute-api.$Region.amazonaws.com/$Environment"
            }
        } catch {
            Write-Warning "Could not retrieve API URL"
        }
        
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
        
        Write-Host "Frontend deployment completed" -ForegroundColor Green
    } else {
        Write-Host "Skipping frontend deployment" -ForegroundColor Yellow
    }
    
    # Calculate deployment time
    $deploymentEnd = Get-Date
    $deploymentTime = $deploymentEnd - $deploymentStart
    
    # Show summary
    Write-Host "DEPLOYMENT COMPLETED SUCCESSFULLY!" -ForegroundColor Green
    Write-Host "=====================================" -ForegroundColor Green
    Write-Host "Environment: $Environment" -ForegroundColor Cyan
    Write-Host "Region: $Region" -ForegroundColor Cyan
    Write-Host "Deployment Time: $($deploymentTime.ToString('mm\:ss'))" -ForegroundColor Cyan
    Write-Host "=====================================" -ForegroundColor Green
    
} catch {
    Write-Host "DEPLOYMENT FAILED" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Please check the logs above for details." -ForegroundColor Red
    exit 1
}