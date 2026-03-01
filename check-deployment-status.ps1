# Check Deployment Status Script
# This script checks the status of all AWS resources

param(
    [string]$Region = "ap-south-1",
    [string]$Environment = "dev",
    [string]$StackName = "msc-evaluate-stack-dev"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Deployment Status Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

function Check-Resource {
    param(
        [string]$Name,
        [scriptblock]$Check
    )
    
    Write-Host "Checking $Name..." -ForegroundColor Yellow
    try {
        $result = & $Check
        if ($result) {
            Write-Host "  ✓ $Name is available" -ForegroundColor Green
            return $result
        } else {
            Write-Host "  ✗ $Name not found" -ForegroundColor Red
            return $null
        }
    } catch {
        Write-Host "  ✗ Error checking $Name" -ForegroundColor Red
        Write-Host "  $($_.Exception.Message)" -ForegroundColor Gray
        return $null
    }
}

# Check CloudFormation Stack
Write-Host "[1/7] CloudFormation Stack" -ForegroundColor Cyan
$stack = Check-Resource -Name "Stack: $StackName" -Check {
    $stackInfo = aws cloudformation describe-stacks --stack-name $StackName --region $Region 2>$null | ConvertFrom-Json
    if ($stackInfo.Stacks) {
        $status = $stackInfo.Stacks[0].StackStatus
        Write-Host "  Status: $status" -ForegroundColor Cyan
        return $stackInfo.Stacks[0]
    }
    return $null
}
Write-Host ""

# Check API Gateway
Write-Host "[2/7] API Gateway" -ForegroundColor Cyan
$apiGateway = Check-Resource -Name "API Gateway" -Check {
    $apiId = aws cloudformation describe-stack-resources --stack-name $StackName --region $Region --query "StackResources[?ResourceType=='AWS::ApiGateway::RestApi'].PhysicalResourceId" --output text 2>$null
    if ($apiId) {
        Write-Host "  API ID: $apiId" -ForegroundColor Cyan
        $apiUrl = "https://$apiId.execute-api.$Region.amazonaws.com/$Environment"
        Write-Host "  URL: $apiUrl" -ForegroundColor Cyan
        return $apiId
    }
    return $null
}
Write-Host ""

# Check Lambda Functions
Write-Host "[3/7] Lambda Functions" -ForegroundColor Cyan
$lambdaFunctions = @(
    "msc-evaluate-user-crud-$Environment",
    "msc-evaluate-template-api-$Environment",
    "msc-evaluate-take-quiz-$Environment",
    "msc-evaluate-submit-quiz-$Environment",
    "msc-evaluate-get-results-$Environment",
    "msc-evaluate-delete-result-$Environment",
    "msc-evaluate-function-$Environment"
)

$lambdaStatus = @{}
foreach ($funcName in $lambdaFunctions) {
    $status = Check-Resource -Name $funcName -Check {
        $func = aws lambda get-function --function-name $funcName --region $Region 2>$null | ConvertFrom-Json
        if ($func) {
            $lastModified = $func.Configuration.LastModified
            Write-Host "  Last Modified: $lastModified" -ForegroundColor Cyan
            return $func
        }
        return $null
    }
    $lambdaStatus[$funcName] = $status -ne $null
}
Write-Host ""

# Check DynamoDB Tables
Write-Host "[4/7] DynamoDB Tables" -ForegroundColor Cyan
$tables = @(
    "msc-evaluate-users-$Environment",
    "msc-evaluate-templates-$Environment",
    "msc-evaluate-quiz-results-$Environment"
)

$tableStatus = @{}
foreach ($tableName in $tables) {
    $status = Check-Resource -Name $tableName -Check {
        $table = aws dynamodb describe-table --table-name $tableName --region $Region 2>$null | ConvertFrom-Json
        if ($table) {
            $itemCount = $table.Table.ItemCount
            Write-Host "  Item Count: $itemCount" -ForegroundColor Cyan
            return $table
        }
        return $null
    }
    $tableStatus[$tableName] = $status -ne $null
}
Write-Host ""

# Check S3 Bucket
Write-Host "[5/7] S3 Frontend Bucket" -ForegroundColor Cyan
$bucket = Check-Resource -Name "Frontend Bucket" -Check {
    $bucketName = "msc-evaluate-frontend-$Environment"
    $bucketInfo = aws s3api head-bucket --bucket $bucketName --region $Region 2>$null
    if ($?) {
        Write-Host "  Bucket: $bucketName" -ForegroundColor Cyan
        $websiteUrl = "http://$bucketName.s3-website.$Region.amazonaws.com"
        Write-Host "  Website URL: $websiteUrl" -ForegroundColor Cyan
        return $bucketName
    }
    return $null
}
Write-Host ""

# Check IAM Role
Write-Host "[6/7] IAM Lambda Execution Role" -ForegroundColor Cyan
$role = Check-Resource -Name "Lambda Execution Role" -Check {
    $roleName = "msc-evaluate-lambda-role-$Environment"
    $roleInfo = aws iam get-role --role-name $roleName 2>$null | ConvertFrom-Json
    if ($roleInfo) {
        Write-Host "  Role: $roleName" -ForegroundColor Cyan
        return $roleInfo
    }
    return $null
}
Write-Host ""

# Test API Endpoints
Write-Host "[7/7] API Endpoint Tests" -ForegroundColor Cyan
if ($apiGateway) {
    $apiUrl = "https://$apiGateway.execute-api.$Region.amazonaws.com/$Environment"
    
    # Test login endpoint
    Write-Host "Testing login endpoint..." -ForegroundColor Yellow
    try {
        $loginBody = @{
            username = "admin"
            password = "admin123"
        } | ConvertTo-Json
        
        $response = Invoke-WebRequest -Uri "$apiUrl/users/login" -Method POST -Body $loginBody -ContentType "application/json" -UseBasicParsing 2>$null
        if ($response.StatusCode -eq 200) {
            Write-Host "  ✓ Login endpoint working" -ForegroundColor Green
        }
    } catch {
        Write-Host "  ✗ Login endpoint failed" -ForegroundColor Red
        Write-Host "  Status: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Gray
    }
    
    # Test templates endpoint
    Write-Host "Testing templates endpoint..." -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "$apiUrl/templates" -Method GET -UseBasicParsing 2>$null
        if ($response.StatusCode -eq 200) {
            Write-Host "  ✓ Templates endpoint working" -ForegroundColor Green
        }
    } catch {
        Write-Host "  ✗ Templates endpoint failed" -ForegroundColor Red
        Write-Host "  Status: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Gray
    }
} else {
    Write-Host "  ⚠ Skipping API tests (API Gateway not found)" -ForegroundColor Yellow
}
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$allGood = $true

if ($stack) {
    Write-Host "✓ CloudFormation Stack: Deployed" -ForegroundColor Green
} else {
    Write-Host "✗ CloudFormation Stack: Not Found" -ForegroundColor Red
    $allGood = $false
}

if ($apiGateway) {
    Write-Host "✓ API Gateway: Configured" -ForegroundColor Green
} else {
    Write-Host "✗ API Gateway: Not Found" -ForegroundColor Red
    $allGood = $false
}

$lambdaCount = ($lambdaStatus.Values | Where-Object { $_ -eq $true }).Count
Write-Host "✓ Lambda Functions: $lambdaCount/$($lambdaFunctions.Count) found" -ForegroundColor $(if ($lambdaCount -eq $lambdaFunctions.Count) { "Green" } else { "Yellow" })
if ($lambdaCount -ne $lambdaFunctions.Count) { $allGood = $false }

$tableCount = ($tableStatus.Values | Where-Object { $_ -eq $true }).Count
Write-Host "✓ DynamoDB Tables: $tableCount/$($tables.Count) found" -ForegroundColor $(if ($tableCount -eq $tables.Count) { "Green" } else { "Yellow" })
if ($tableCount -ne $tables.Count) { $allGood = $false }

if ($bucket) {
    Write-Host "✓ S3 Bucket: Configured" -ForegroundColor Green
} else {
    Write-Host "✗ S3 Bucket: Not Found" -ForegroundColor Red
    $allGood = $false
}

Write-Host ""

if ($allGood) {
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  ✓ All Resources Deployed!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Your deployment looks good!" -ForegroundColor Green
    Write-Host ""
    Write-Host "If you're still experiencing issues:" -ForegroundColor Yellow
    Write-Host "1. Run .\update-lambdas.ps1 to update Lambda code" -ForegroundColor White
    Write-Host "2. Run .\test-api.ps1 to test API endpoints" -ForegroundColor White
    Write-Host "3. Clear browser cache and refresh" -ForegroundColor White
} else {
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "  ⚠ Some Resources Missing" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Some resources are not deployed correctly." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To fix this:" -ForegroundColor Yellow
    Write-Host "1. Run .\cloudformation\deploy.ps1 to deploy the stack" -ForegroundColor White
    Write-Host "2. Run .\cloudformation\deploy-users.ps1 to initialize users" -ForegroundColor White
    Write-Host "3. Run .\update-lambdas.ps1 to update Lambda code" -ForegroundColor White
}
Write-Host ""
