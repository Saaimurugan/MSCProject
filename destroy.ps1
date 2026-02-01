# MSC Evaluate Destruction Script for Windows PowerShell
param(
    [string]$Environment = "dev",
    [string]$ProjectName = "msc-evaluate",
    [string]$Region = "us-east-1",
    [switch]$Force = $false
)

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Cyan"

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Confirm-Destruction {
    if (-not $Force) {
        Write-ColorOutput "⚠️  WARNING: This will destroy all resources for environment '$Environment'" $Red
        Write-ColorOutput "This includes:" $Yellow
        Write-ColorOutput "  - All DynamoDB tables and data" $Yellow
        Write-ColorOutput "  - All Lambda functions" $Yellow
        Write-ColorOutput "  - API Gateway" $Yellow
        Write-ColorOutput "  - S3 bucket and website content" $Yellow
        Write-ColorOutput "  - CloudFront distribution" $Yellow
        
        $confirmation = Read-Host "Type 'DELETE' to confirm destruction"
        if ($confirmation -ne "DELETE") {
            Write-ColorOutput "❌ Destruction cancelled" $Green
            exit 0
        }
    }
}

function Empty-S3-Bucket {
    param([string]$BucketName)
    
    if ([string]::IsNullOrEmpty($BucketName)) {
        return
    }
    
    Write-ColorOutput "🗑️ Emptying S3 bucket: $BucketName" $Yellow
    
    try {
        # Check if bucket exists
        aws s3api head-bucket --bucket $BucketName --region $Region 2>$null
        if ($LASTEXITCODE -eq 0) {
            # Empty the bucket
            aws s3 rm "s3://$BucketName" --recursive --region $Region
            Write-ColorOutput "✅ S3 bucket emptied successfully" $Green
        } else {
            Write-ColorOutput "ℹ️ S3 bucket does not exist or already empty" $Blue
        }
    } catch {
        Write-ColorOutput "⚠️ Could not empty S3 bucket: $_" $Yellow
    }
}

function Get-S3BucketName {
    param([string]$StackName)
    
    try {
        $outputs = aws cloudformation describe-stacks `
            --stack-name $StackName `
            --region $Region `
            --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" `
            --output text 2>$null
        
        if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrEmpty($outputs)) {
            return $outputs.Trim()
        }
    } catch {
        Write-ColorOutput "ℹ️ Could not retrieve S3 bucket name from stack" $Blue
    }
    
    return $null
}

function Delete-CloudFormation-Stack {
    param([string]$StackName)
    
    Write-ColorOutput "🗑️ Deleting CloudFormation stack: $StackName" $Yellow
    
    try {
        # Check if stack exists
        aws cloudformation describe-stacks --stack-name $StackName --region $Region 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-ColorOutput "ℹ️ Stack '$StackName' does not exist" $Blue
            return
        }
        
        # Delete the stack
        aws cloudformation delete-stack --stack-name $StackName --region $Region
        
        Write-ColorOutput "⏳ Waiting for stack deletion to complete..." $Blue
        aws cloudformation wait stack-delete-complete --stack-name $StackName --region $Region
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ Stack deleted successfully" $Green
        } else {
            Write-ColorOutput "⚠️ Stack deletion may have failed or timed out" $Yellow
        }
    } catch {
        Write-ColorOutput "❌ Failed to delete stack: $_" $Red
    }
}

function Show-Destruction-Summary {
    Write-ColorOutput "`n🎯 Destruction Summary:" $Blue
    Write-ColorOutput "=" * 40 $Blue
    Write-ColorOutput "  Environment: $Environment" $Yellow
    Write-ColorOutput "  Region: $Region" $Yellow
    Write-ColorOutput "  Project: $ProjectName" $Yellow
    Write-ColorOutput "`n✅ All resources have been destroyed!" $Green
    Write-ColorOutput "=" * 40 $Blue
}

# Main execution
try {
    Write-ColorOutput "🗑️ MSC Evaluate Destruction Script" $Red
    Write-ColorOutput "Environment: $Environment | Region: $Region" $Yellow
    
    Confirm-Destruction
    
    $stackName = "$ProjectName-infrastructure-$Environment"
    
    # Get S3 bucket name before deleting stack
    $bucketName = Get-S3BucketName -StackName $stackName
    
    # Empty S3 bucket first (required before stack deletion)
    if ($bucketName) {
        Empty-S3-Bucket -BucketName $bucketName
    }
    
    # Delete CloudFormation stack
    Delete-CloudFormation-Stack -StackName $stackName
    
    Show-Destruction-Summary
    
} catch {
    Write-ColorOutput "❌ Destruction failed: $_" $Red
    exit 1
}

Write-ColorOutput "`n✅ Destruction script completed!" $Green