# MSC Evaluate - Pre-deployment Validation Script
# Checks if all prerequisites are met before deployment

$ErrorActionPreference = "Continue"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "MSC Evaluate - Deployment Validation" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$allChecksPassed = $true

# Check 1: AWS CLI
Write-Host "Checking AWS CLI..." -NoNewline
try {
    $awsVersion = aws --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host " OK" -ForegroundColor Green
        Write-Host "  Version: $awsVersion" -ForegroundColor Gray
    } else {
        Write-Host " FAILED" -ForegroundColor Red
        Write-Host "  AWS CLI not found. Install from: https://aws.amazon.com/cli/" -ForegroundColor Yellow
        $allChecksPassed = $false
    }
} catch {
    Write-Host " FAILED" -ForegroundColor Red
    Write-Host "  AWS CLI not found. Install from: https://aws.amazon.com/cli/" -ForegroundColor Yellow
    $allChecksPassed = $false
}

# Check 2: AWS Credentials
Write-Host "Checking AWS Credentials..." -NoNewline
try {
    $identity = aws sts get-caller-identity 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host " OK" -ForegroundColor Green
        $identityJson = $identity | ConvertFrom-Json
        Write-Host "  Account: $($identityJson.Account)" -ForegroundColor Gray
        Write-Host "  User: $($identityJson.Arn)" -ForegroundColor Gray
    } else {
        Write-Host " FAILED" -ForegroundColor Red
        Write-Host "  AWS credentials not configured. Run: aws configure" -ForegroundColor Yellow
        $allChecksPassed = $false
    }
} catch {
    Write-Host " FAILED" -ForegroundColor Red
    Write-Host "  AWS credentials not configured. Run: aws configure" -ForegroundColor Yellow
    $allChecksPassed = $false
}

# Check 3: Node.js
Write-Host "Checking Node.js..." -NoNewline
try {
    $nodeVersion = node --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host " OK" -ForegroundColor Green
        Write-Host "  Version: $nodeVersion" -ForegroundColor Gray
    } else {
        Write-Host " FAILED" -ForegroundColor Red
        Write-Host "  Node.js not found. Install from: https://nodejs.org/" -ForegroundColor Yellow
        $allChecksPassed = $false
    }
} catch {
    Write-Host " FAILED" -ForegroundColor Red
    Write-Host "  Node.js not found. Install from: https://nodejs.org/" -ForegroundColor Yellow
    $allChecksPassed = $false
}

# Check 4: npm
Write-Host "Checking npm..." -NoNewline
try {
    $npmVersion = npm --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host " OK" -ForegroundColor Green
        Write-Host "  Version: $npmVersion" -ForegroundColor Gray
    } else {
        Write-Host " FAILED" -ForegroundColor Red
        Write-Host "  npm not found. Install Node.js from: https://nodejs.org/" -ForegroundColor Yellow
        $allChecksPassed = $false
    }
} catch {
    Write-Host " FAILED" -ForegroundColor Red
    Write-Host "  npm not found. Install Node.js from: https://nodejs.org/" -ForegroundColor Yellow
    $allChecksPassed = $false
}

# Check 5: Project Structure
Write-Host "Checking Project Structure..." -NoNewline
$PROJECT_ROOT = Split-Path -Parent $PSScriptRoot
$requiredPaths = @(
    "$PROJECT_ROOT\frontend\package.json",
    "$PROJECT_ROOT\backend\templates\template_api.py",
    "$PROJECT_ROOT\backend\quiz\take_quiz.py",
    "$PROJECT_ROOT\backend\quiz\submit_quiz.py",
    "$PROJECT_ROOT\cloudformation\deploy-stack.yaml"
)

$missingPaths = @()
foreach ($path in $requiredPaths) {
    if (-not (Test-Path $path)) {
        $missingPaths += $path
    }
}

if ($missingPaths.Count -eq 0) {
    Write-Host " OK" -ForegroundColor Green
} else {
    Write-Host " FAILED" -ForegroundColor Red
    Write-Host "  Missing files:" -ForegroundColor Yellow
    foreach ($path in $missingPaths) {
        Write-Host "    - $path" -ForegroundColor Yellow
    }
    $allChecksPassed = $false
}

# Check 6: Region Availability
Write-Host "Checking Region (ap-south-1)..." -NoNewline
try {
    $regions = aws ec2 describe-regions --query "Regions[?RegionName=='ap-south-1'].RegionName" --output text 2>&1
    if ($regions -eq "ap-south-1") {
        Write-Host " OK" -ForegroundColor Green
    } else {
        Write-Host " WARNING" -ForegroundColor Yellow
        Write-Host "  Region ap-south-1 may not be available in your account" -ForegroundColor Yellow
    }
} catch {
    Write-Host " WARNING" -ForegroundColor Yellow
    Write-Host "  Could not verify region availability" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
if ($allChecksPassed) {
    Write-Host "All Checks Passed!" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "You are ready to deploy. Run:" -ForegroundColor Green
    Write-Host "  .\deploy.ps1" -ForegroundColor Cyan
} else {
    Write-Host "Some Checks Failed" -ForegroundColor Red
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Please fix the issues above before deploying." -ForegroundColor Yellow
}
Write-Host ""
