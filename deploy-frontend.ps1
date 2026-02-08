#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Deploy MSC Evaluate Frontend to AWS S3
.DESCRIPTION
    This script builds the React frontend and deploys it to the specified S3 bucket.
.PARAMETER BucketName
    S3 bucket name for frontend hosting (default: msc-evaluate-frontend-dev-127510141)
.PARAMETER Region
    AWS region (default: ap-south-1)
.PARAMETER Environment
    Environment name (default: dev)
.PARAMETER ApiUrl
    API Gateway URL for the backend
#>

param(
    [string]$BucketName = "msc-evaluate-frontend-dev-127510141",
    [string]$Region = "ap-south-1",
    [string]$Environment = "dev",
    [string]$ApiUrl = ""
)

# Set error action preference
$ErrorActionPreference = "Stop"

Write-Host "Starting MSC Evaluate Frontend Deployment" -ForegroundColor Green
Write-Host "Bucket: $BucketName" -ForegroundColor Cyan
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
    Write-Host "AWS credentials verified" -ForegroundColor Green
} catch {
    Write-Error "AWS credentials not configured. Please run 'aws configure' first."
    exit 1
}

# Check if Node.js is installed
try {
    node --version | Out-Null
    npm --version | Out-Null
    Write-Host "Node.js and npm verified" -ForegroundColor Green
} catch {
    Write-Error "Node.js and npm are required. Please install Node.js first."
    exit 1
}

# Function to check if S3 bucket exists
function Test-S3Bucket {
    param([string]$Bucket)
    try {
        aws s3api head-bucket --bucket $Bucket --region $Region 2>$null
        return $true
    } catch {
        return $false
    }
}

# Function to create S3 bucket
function New-S3Bucket {
    param([string]$Bucket)
    
    Write-Host "Creating S3 bucket: $Bucket" -ForegroundColor Yellow
    
    try {
        if ($Region -eq "us-east-1") {
            aws s3api create-bucket --bucket $Bucket --region $Region
        } else {
            aws s3api create-bucket --bucket $Bucket --region $Region --create-bucket-configuration LocationConstraint=$Region
        }
        
        # Enable static website hosting
        $websiteConfig = @'
{
    "IndexDocument": {
        "Suffix": "index.html"
    },
    "ErrorDocument": {
        "Key": "index.html"
    }
}
'@
        
        $websiteConfig | Out-File -FilePath "website-config.json" -Encoding utf8
        aws s3api put-bucket-website --bucket $Bucket --website-configuration file://website-config.json
        Remove-Item "website-config.json" -ErrorAction SilentlyContinue
        
        # Set bucket policy for public read access
        $bucketPolicy = @'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::BUCKET_NAME/*"
        }
    ]
}
'@
        
        # Replace placeholder with actual bucket name
        $bucketPolicy = $bucketPolicy.Replace("BUCKET_NAME", $Bucket)
        
        $bucketPolicy | Out-File -FilePath "bucket-policy.json" -Encoding utf8
        aws s3api put-bucket-policy --bucket $Bucket --policy file://bucket-policy.json
        Remove-Item "bucket-policy.json" -ErrorAction SilentlyContinue
        
        # Disable block public access
        aws s3api put-public-access-block --bucket $Bucket --public-access-block-configuration "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"
        
        Write-Host "S3 bucket created and configured: $Bucket" -ForegroundColor Green
        
    } catch {
        Write-Error "Failed to create S3 bucket: $($_.Exception.Message)"
        exit 1
    }
}

# Function to get API Gateway URL
function Get-ApiGatewayUrl {
    if ($ApiUrl) {
        return $ApiUrl
    }
    
    Write-Host "Looking for API Gateway URL..." -ForegroundColor Yellow
    
    try {
        # Try to find the API Gateway by name
        $apiName = "msc-evaluate-api-$Environment"
        $apis = aws apigateway get-rest-apis --region $Region | ConvertFrom-Json
        $api = $apis.items | Where-Object { $_.name -eq $apiName }
        
        if ($api) {
            $apiUrl = "https://$($api.id).execute-api.$Region.amazonaws.com/$Environment"
            Write-Host "Found API Gateway URL: $apiUrl" -ForegroundColor Green
            return $apiUrl
        } else {
            Write-Warning "API Gateway not found. You may need to deploy the API first or provide the URL manually."
            return "https://your-api-gateway-url.execute-api.$Region.amazonaws.com/$Environment"
        }
    } catch {
        Write-Warning "Could not retrieve API Gateway URL automatically."
        return "https://your-api-gateway-url.execute-api.$Region.amazonaws.com/$Environment"
    }
}

# Function to build frontend
function Build-Frontend {
    param([string]$ApiUrl)
    
    Write-Host "Building React frontend..." -ForegroundColor Yellow
    
    # Navigate to frontend directory
    if (-not (Test-Path "frontend")) {
        Write-Error "Frontend directory not found. Please run this script from the project root."
        exit 1
    }
    
    Push-Location "frontend"
    
    try {
        # Install dependencies
        Write-Host "Installing npm dependencies..." -ForegroundColor Yellow
        npm install --silent
        
        # Create .env file with API URL
        Write-Host "Configuring environment variables..." -ForegroundColor Yellow
        $envContent = "REACT_APP_API_URL=$ApiUrl"
        $envContent | Out-File -FilePath ".env" -Encoding utf8
        
        # Build the application
        Write-Host "Building React application..." -ForegroundColor Yellow
        npm run build
        
        if (-not (Test-Path "build")) {
            Write-Error "Build failed - build directory not found"
            exit 1
        }
        
        Write-Host "Frontend build completed" -ForegroundColor Green
        
    } catch {
        Write-Error "Frontend build failed: $($_.Exception.Message)"
        exit 1
    } finally {
        Pop-Location
    }
}

# Function to deploy to S3
function Deploy-ToS3 {
    param([string]$Bucket)
    
    Write-Host "Deploying to S3 bucket: $Bucket" -ForegroundColor Yellow
    
    try {
        # Sync build directory to S3
        aws s3 sync frontend/build/ s3://$Bucket --delete --region $Region
        
        # Set proper content types for specific files
        aws s3 cp s3://$Bucket/index.html s3://$Bucket/index.html --metadata-directive REPLACE --content-type "text/html" --region $Region
        aws s3 cp s3://$Bucket/static/ s3://$Bucket/static/ --recursive --metadata-directive REPLACE --content-type "text/css" --exclude "*" --include "*.css" --region $Region
        aws s3 cp s3://$Bucket/static/ s3://$Bucket/static/ --recursive --metadata-directive REPLACE --content-type "application/javascript" --exclude "*" --include "*.js" --region $Region
        
        Write-Host "Files uploaded to S3" -ForegroundColor Green
        
        # Get website URL
        $websiteUrl = "http://$Bucket.s3-website-$Region.amazonaws.com"
        Write-Host "Website URL: $websiteUrl" -ForegroundColor Cyan
        
        return $websiteUrl
        
    } catch {
        Write-Error "S3 deployment failed: $($_.Exception.Message)"
        exit 1
    }
}

# Function to invalidate CloudFront (if exists)
function Clear-CloudFrontCache {
    param([string]$Bucket)
    
    Write-Host "Checking for CloudFront distribution..." -ForegroundColor Yellow
    
    try {
        $distributions = aws cloudfront list-distributions --region $Region | ConvertFrom-Json
        $distribution = $distributions.DistributionList.Items | Where-Object { 
            $_.Origins.Items[0].DomainName -like "*$Bucket*" 
        }
        
        if ($distribution) {
            Write-Host "Creating CloudFront invalidation..." -ForegroundColor Yellow
            $invalidationId = [System.Guid]::NewGuid().ToString()
            aws cloudfront create-invalidation --distribution-id $distribution.Id --paths "/*" --region $Region | Out-Null
            Write-Host "CloudFront cache invalidated" -ForegroundColor Green
            
            $cloudfrontUrl = "https://$($distribution.DomainName)"
            Write-Host "CloudFront URL: $cloudfrontUrl" -ForegroundColor Cyan
            return $cloudfrontUrl
        } else {
            Write-Host "No CloudFront distribution found for this bucket" -ForegroundColor Blue
            return $null
        }
    } catch {
        Write-Warning "Could not check CloudFront distributions: $($_.Exception.Message)"
        return $null
    }
}

# Main deployment process
try {
    # Get API Gateway URL
    $apiGatewayUrl = Get-ApiGatewayUrl
    Write-Host "API URL: $apiGatewayUrl" -ForegroundColor Cyan
    
    # Check if bucket exists, create if not
    if (-not (Test-S3Bucket -Bucket $BucketName)) {
        New-S3Bucket -Bucket $BucketName
    } else {
        Write-Host "S3 bucket exists: $BucketName" -ForegroundColor Green
    }
    
    # Build frontend
    Build-Frontend -ApiUrl $apiGatewayUrl
    
    # Deploy to S3
    $websiteUrl = Deploy-ToS3 -Bucket $BucketName
    
    # Clear CloudFront cache if exists
    $cloudfrontUrl = Clear-CloudFrontCache -Bucket $BucketName
    
    Write-Host "Frontend deployment completed successfully!" -ForegroundColor Green
    Write-Host "Bucket: $BucketName" -ForegroundColor Cyan
    Write-Host "Region: $Region" -ForegroundColor Cyan
    Write-Host "Website URL: $websiteUrl" -ForegroundColor Cyan
    if ($cloudfrontUrl) {
        Write-Host "CloudFront URL: $cloudfrontUrl" -ForegroundColor Cyan
    }
    Write-Host "API URL: $apiGatewayUrl" -ForegroundColor Cyan
    
} catch {
    Write-Error "Frontend deployment failed: $($_.Exception.Message)"
    exit 1
}