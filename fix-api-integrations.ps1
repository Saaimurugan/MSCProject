#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Fix API Gateway Integrations for MSC Evaluate
.DESCRIPTION
    This script fixes missing integrations in the API Gateway by properly connecting methods to Lambda functions.
.PARAMETER Region
    AWS region (default: ap-south-1)
.PARAMETER Environment
    Environment name (default: dev)
#>

param(
    [string]$Region = "ap-south-1",
    [string]$Environment = "dev"
)

# Set error action preference
$ErrorActionPreference = "Stop"

Write-Host "Fixing API Gateway Integrations" -ForegroundColor Green
Write-Host "Region: $Region" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Cyan

# Get AWS account ID
$accountId = (aws sts get-caller-identity | ConvertFrom-Json).Account
Write-Host "Account ID: $accountId" -ForegroundColor Cyan

# Get API Gateway ID
$apiName = "msc-evaluate-api-$Environment"
$apis = aws apigateway get-rest-apis --region $Region | ConvertFrom-Json
$api = $apis.items | Where-Object { $_.name -eq $apiName }

if (-not $api) {
    Write-Error "API Gateway not found: $apiName"
    exit 1
}

$apiId = $api.id
Write-Host "API ID: $apiId" -ForegroundColor Cyan

# Define endpoints and their Lambda functions
$endpoints = @(
    @{ Path = "/auth/login"; Method = "POST"; Lambda = "msc-evaluate-auth-login-$Environment" },
    @{ Path = "/auth/signup"; Method = "POST"; Lambda = "msc-evaluate-auth-signup-$Environment" },
    @{ Path = "/admin/users"; Method = "GET"; Lambda = "msc-evaluate-admin-get-users-$Environment" },
    @{ Path = "/admin/users"; Method = "POST"; Lambda = "msc-evaluate-admin-create-user-$Environment" },
    @{ Path = "/admin/users/{userId}"; Method = "DELETE"; Lambda = "msc-evaluate-admin-delete-user-$Environment" },
    @{ Path = "/admin/users/{userId}/role"; Method = "PUT"; Lambda = "msc-evaluate-admin-update-user-role-$Environment" },
    @{ Path = "/admin/usage-logs"; Method = "GET"; Lambda = "msc-evaluate-admin-get-usage-logs-$Environment" },
    @{ Path = "/profile"; Method = "GET"; Lambda = "msc-evaluate-profile-get-profile-$Environment" },
    @{ Path = "/profile"; Method = "PUT"; Lambda = "msc-evaluate-profile-update-profile-$Environment" },
    @{ Path = "/profile/password"; Method = "PUT"; Lambda = "msc-evaluate-profile-change-password-$Environment" },
    @{ Path = "/templates"; Method = "GET"; Lambda = "msc-evaluate-templates-get-templates-$Environment" },
    @{ Path = "/templates"; Method = "POST"; Lambda = "msc-evaluate-templates-create-template-$Environment" },
    @{ Path = "/quiz/take"; Method = "POST"; Lambda = "msc-evaluate-quiz-take-quiz-$Environment" },
    @{ Path = "/quiz/submit"; Method = "POST"; Lambda = "msc-evaluate-quiz-submit-quiz-$Environment" },
    @{ Path = "/reports"; Method = "GET"; Lambda = "msc-evaluate-reports-get-all-reports-$Environment" },
    @{ Path = "/reports/user/{userId}"; Method = "GET"; Lambda = "msc-evaluate-reports-get-user-reports-$Environment" },
    @{ Path = "/reports/template/{templateId}"; Method = "GET"; Lambda = "msc-evaluate-reports-get-template-reports-$Environment" },
    @{ Path = "/ai/evaluate"; Method = "POST"; Lambda = "msc-evaluate-ai-scorer-$Environment" }
)

# Get all resources
$resources = aws apigateway get-resources --rest-api-id $apiId --region $Region | ConvertFrom-Json

# Function to find resource by path
function Find-ResourceByPath {
    param([string]$Path)
    
    foreach ($resource in $resources.items) {
        if ($resource.pathPart -and $Path.EndsWith($resource.pathPart)) {
            # Check if this is the right resource by building the full path
            $fullPath = ""
            $currentResource = $resource
            $pathParts = @()
            
            while ($currentResource.pathPart) {
                $pathParts = @($currentResource.pathPart) + $pathParts
                $parentResource = $resources.items | Where-Object { $_.id -eq $currentResource.parentId }
                $currentResource = $parentResource
                if (-not $currentResource) { break }
            }
            
            $fullPath = "/" + ($pathParts -join "/")
            if ($fullPath -eq $Path -or ($Path.Contains("{") -and $fullPath.Replace("{userId}", "{userId}").Replace("{templateId}", "{templateId}") -eq $Path)) {
                return $resource.id
            }
        }
    }
    return $null
}

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

# Function to create integration
function New-Integration {
    param(
        [string]$ApiId,
        [string]$ResourceId,
        [string]$HttpMethod,
        [string]$LambdaFunction
    )
    
    Write-Host "Creating integration: $HttpMethod $LambdaFunction" -ForegroundColor Yellow
    
    # Check if Lambda function exists
    if (-not (Test-LambdaFunction -FunctionName $LambdaFunction)) {
        Write-Warning "Lambda function not found: $LambdaFunction"
        return $false
    }
    
    try {
        # Create integration
        $lambdaArn = "arn:aws:lambda:${Region}:${accountId}:function:${LambdaFunction}"
        $integrationUri = "arn:aws:apigateway:${Region}:lambda:path/2015-03-31/functions/${lambdaArn}/invocations"
        
        Write-Host "  Lambda ARN: $lambdaArn" -ForegroundColor Gray
        Write-Host "  Integration URI: $integrationUri" -ForegroundColor Gray
        
        # Create the integration
        $result = aws apigateway put-integration --rest-api-id $ApiId --resource-id $ResourceId --http-method $HttpMethod --type AWS_PROXY --integration-http-method POST --uri $integrationUri --region $Region 2>&1
        
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Failed to create integration: $result"
            return $false
        }
        
        # Add Lambda permission
        $statementId = "apigateway-$ApiId-$ResourceId-$HttpMethod-$(Get-Random)"
        $sourceArn = "arn:aws:execute-api:${Region}:${accountId}:${ApiId}/*/*"
        
        $permResult = aws lambda add-permission --function-name $LambdaFunction --statement-id $statementId --action lambda:InvokeFunction --principal apigateway.amazonaws.com --source-arn $sourceArn --region $Region 2>&1
        
        if ($LASTEXITCODE -ne 0 -and $permResult -notlike "*ResourceConflictException*") {
            Write-Warning "Failed to add Lambda permission: $permResult"
        }
        
        Write-Host "  Integration created successfully" -ForegroundColor Green
        return $true
        
    } catch {
        Write-Warning "Failed to create integration: $($_.Exception.Message)"
        return $false
    }
}

# Fix integrations for each endpoint
$fixedCount = 0
$totalCount = 0

foreach ($endpoint in $endpoints) {
    $totalCount++
    Write-Host "Processing: $($endpoint.Method) $($endpoint.Path)" -ForegroundColor Cyan
    
    # Find the resource
    $resourceId = Find-ResourceByPath -Path $endpoint.Path
    
    if (-not $resourceId) {
        Write-Warning "Resource not found for path: $($endpoint.Path)"
        continue
    }
    
    Write-Host "  Resource ID: $resourceId" -ForegroundColor Gray
    
    # Check if integration already exists
    try {
        $integration = aws apigateway get-integration --rest-api-id $apiId --resource-id $resourceId --http-method $endpoint.Method --region $Region 2>$null | ConvertFrom-Json
        if ($integration -and $integration.type -eq "AWS_PROXY") {
            Write-Host "  Integration already exists and is correct" -ForegroundColor Green
            $fixedCount++
            continue
        }
    } catch {
        # Integration doesn't exist, we'll create it
    }
    
    # Create the integration
    if (New-Integration -ApiId $apiId -ResourceId $resourceId -HttpMethod $endpoint.Method -LambdaFunction $endpoint.Lambda) {
        $fixedCount++
    }
}

# Deploy the API to make changes active
Write-Host "Deploying API to $Environment stage..." -ForegroundColor Yellow
try {
    aws apigateway create-deployment --rest-api-id $apiId --stage-name $Environment --region $Region | Out-Null
    Write-Host "API deployed successfully" -ForegroundColor Green
} catch {
    Write-Warning "Failed to deploy API: $($_.Exception.Message)"
}

# Summary
Write-Host "Integration Fix Summary:" -ForegroundColor Green
Write-Host "Total endpoints: $totalCount" -ForegroundColor Cyan
Write-Host "Fixed/Verified: $fixedCount" -ForegroundColor Cyan
Write-Host "API URL: https://$apiId.execute-api.$Region.amazonaws.com/$Environment" -ForegroundColor Cyan

if ($fixedCount -eq $totalCount) {
    Write-Host "All integrations are now properly configured!" -ForegroundColor Green
} else {
    Write-Warning "Some integrations may still need attention. Check the logs above."
}