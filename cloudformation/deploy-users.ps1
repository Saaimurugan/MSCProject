# PowerShell script to deploy user management Lambda function
# Usage: .\deploy-users.ps1 -Environment "dev" -Region "us-east-1"

param(
    [Parameter(Mandatory=$false)]
    [string]$Environment = "dev",
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-east-1"
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "User Management Lambda Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$FunctionName = "msc-evaluate-user-crud-$Environment"
$BackendPath = "..\backend\users"
$ZipFile = "user_crud.zip"

# Check if backend directory exists
if (-not (Test-Path $BackendPath)) {
    Write-Host "Error: Backend directory not found: $BackendPath" -ForegroundColor Red
    exit 1
}

# Navigate to backend directory
Push-Location $BackendPath

try {
    Write-Host "1. Packaging Lambda function..." -ForegroundColor Yellow
    
    # Remove old zip if exists
    if (Test-Path $ZipFile) {
        Remove-Item $ZipFile -Force
    }
    
    # Create zip file
    Compress-Archive -Path "user_crud.py" -DestinationPath $ZipFile -Force
    
    Write-Host "   ✓ Package created: $ZipFile" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "2. Deploying to AWS Lambda..." -ForegroundColor Yellow
    
    # Update Lambda function
    aws lambda update-function-code `
        --function-name $FunctionName `
        --zip-file "fileb://$ZipFile" `
        --region $Region
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ Lambda function updated successfully" -ForegroundColor Green
    } else {
        Write-Host "   ✗ Failed to update Lambda function" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "3. Initializing default users..." -ForegroundColor Yellow
    
    $TableName = "msc-evaluate-users-$Environment"
    
    # Check if Python is available
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCmd) {
        $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
    }
    
    if ($pythonCmd) {
        & $pythonCmd.Source init_users.py $TableName
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✓ Default users initialized" -ForegroundColor Green
        } else {
            Write-Host "   ⚠ Failed to initialize users (you can run init_users.py manually)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   ⚠ Python not found. Run 'python init_users.py $TableName' manually" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Deployment Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Function Name: $FunctionName" -ForegroundColor White
    Write-Host "Region: $Region" -ForegroundColor White
    Write-Host ""
    Write-Host "Default Credentials:" -ForegroundColor Yellow
    Write-Host "  Admin:   admin / admin123" -ForegroundColor White
    Write-Host "  Tutor:   tutor / tutor123" -ForegroundColor White
    Write-Host "  Student: student / student123" -ForegroundColor White
    Write-Host ""
    
} finally {
    # Return to original directory
    Pop-Location
}
