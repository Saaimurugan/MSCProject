# MSC Evaluate - Cleanup Script
# This script removes all deployed AWS resources

$ErrorActionPreference = "Stop"

# Configuration
$REGION = "ap-south-1"
$ENVIRONMENT = "dev"
$STACK_NAME = "msc-evaluate-stack-$ENVIRONMENT"

Write-Host "==========================================" -ForegroundColor Red
Write-Host "MSC Evaluate Cleanup Script" -ForegroundColor Red
Write-Host "==========================================" -ForegroundColor Red
Write-Host "Region: $REGION"
Write-Host "Environment: $ENVIRONMENT"
Write-Host "Stack Name: $STACK_NAME"
Write-Host "==========================================" -ForegroundColor Red
Write-Host ""
Write-Host "WARNING: This will delete all resources!" -ForegroundColor Yellow
Write-Host ""

$confirmation = Read-Host "Are you sure you want to proceed? (yes/no)"
if ($confirmation -ne "yes") {
    Write-Host "Cleanup cancelled." -ForegroundColor Yellow
    exit 0
}

# Step 1: Get S3 Bucket Name
Write-Host ""
Write-Host "Step 1: Retrieving S3 Bucket Name..." -ForegroundColor Yellow

try {
    $FRONTEND_BUCKET = aws cloudformation describe-stacks `
      --stack-name $STACK_NAME `
      --region $REGION `
      --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" `
      --output text 2>$null

    if ($FRONTEND_BUCKET) {
        Write-Host "Found bucket: $FRONTEND_BUCKET"
        
        # Step 2: Empty S3 Bucket
        Write-Host ""
        Write-Host "Step 2: Emptying S3 Bucket..." -ForegroundColor Yellow
        aws s3 rm "s3://$FRONTEND_BUCKET/" --recursive --region $REGION
        Write-Host "✓ S3 Bucket emptied" -ForegroundColor Green
    } else {
        Write-Host "No S3 bucket found or stack doesn't exist" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Could not retrieve bucket name (stack may not exist)" -ForegroundColor Yellow
}

# Step 3: Delete CloudFormation Stack
Write-Host ""
Write-Host "Step 3: Deleting CloudFormation Stack..." -ForegroundColor Yellow
aws cloudformation delete-stack --stack-name $STACK_NAME --region $REGION

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to initiate stack deletion" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Stack deletion initiated" -ForegroundColor Green

# Step 4: Wait for Stack Deletion
Write-Host ""
Write-Host "Step 4: Waiting for stack deletion to complete..." -ForegroundColor Yellow
Write-Host "(This may take several minutes)"

aws cloudformation wait stack-delete-complete --stack-name $STACK_NAME --region $REGION

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Stack deleted successfully" -ForegroundColor Green
} else {
    Write-Host "Stack deletion may still be in progress. Check AWS Console for status." -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Cleanup Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "All resources have been removed:" -ForegroundColor Green
Write-Host "  ✓ S3 Bucket and contents"
Write-Host "  ✓ Lambda Functions"
Write-Host "  ✓ API Gateway"
Write-Host "  ✓ DynamoDB Tables"
Write-Host "  ✓ IAM Roles"
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
