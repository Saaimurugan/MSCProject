#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Fix CORS OPTIONS Method Integrations for API Gateway
.DESCRIPTION
    This script fixes missing MOCK integrations for OPTIONS methods used for CORS.
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

Write-Host "Fixing CORS OPTIONS Method Integrations" -ForegroundColor Green
Write-Host "Region: $Region" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Cyan

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

# Get all resources with OPTIONS methods
$resources = aws apigateway get-resources --rest-api-id $apiId --region $Region | ConvertFrom-Json

$optionsResources = @()
foreach ($resource in $resources.items) {
    if ($resource.resourceMethods -and $resource.resourceMethods.OPTIONS) {
        $optionsResources += @{
            ResourceId = $resource.id
            Path = $resource.pathPart
        }
    }
}

Write-Host "Found $($optionsResources.Count) resources with OPTIONS methods" -ForegroundColor Cyan

# Function to create CORS integration for OPTIONS method
function New-CORSIntegration {
    param(
        [string]$ApiId,
        [string]$ResourceId,
        [string]$Path
    )
    
    Write-Host "Fixing OPTIONS integration for: $Path (Resource: $ResourceId)" -ForegroundColor Yellow
    
    try {
        # Check if integration already exists
        try {
            $existingIntegration = aws apigateway get-integration --rest-api-id $ApiId --resource-id $ResourceId --http-method OPTIONS --region $Region 2>$null | ConvertFrom-Json
            if ($existingIntegration -and $existingIntegration.type -eq "MOCK") {
                Write-Host "  MOCK integration already exists" -ForegroundColor Green
                return $true
            }
        } catch {
            # Integration doesn't exist, we'll create it
        }
        
        # Create MOCK integration for OPTIONS
        $requestTemplates = '{"application/json": "{\"statusCode\": 200}"}'
        $result = aws apigateway put-integration --rest-api-id $ApiId --resource-id $ResourceId --http-method OPTIONS --type MOCK --request-templates $requestTemplates --region $Region 2>&1
        
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Failed to create MOCK integration: $result"
            return $false
        }
        
        # Create method response for OPTIONS (if not exists)
        try {
            aws apigateway put-method-response --rest-api-id $ApiId --resource-id $ResourceId --http-method OPTIONS --status-code 200 --response-parameters "method.response.header.Access-Control-Allow-Headers=false,method.response.header.Access-Control-Allow-Methods=false,method.response.header.Access-Control-Allow-Origin=false" --region $Region 2>$null | Out-Null
        } catch {
            # Method response might already exist
        }
        
        # Create integration response for OPTIONS
        $responseParams = '{"method.response.header.Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token", "method.response.header.Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS", "method.response.header.Access-Control-Allow-Origin": "*"}'
        $intResult = aws apigateway put-integration-response --rest-api-id $ApiId --resource-id $ResourceId --http-method OPTIONS --status-code 200 --response-parameters $responseParams --region $Region 2>&1
        
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Failed to create integration response: $intResult"
            return $false
        }
        
        Write-Host "  CORS integration created successfully" -ForegroundColor Green
        return $true
        
    } catch {
        Write-Warning "Failed to create CORS integration: $($_.Exception.Message)"
        return $false
    }
}

# Fix CORS integrations
$fixedCount = 0
foreach ($resource in $optionsResources) {
    if (New-CORSIntegration -ApiId $apiId -ResourceId $resource.ResourceId -Path $resource.Path) {
        $fixedCount++
    }
}

# Deploy the API to make changes active
Write-Host "Deploying API to $Environment stage..." -ForegroundColor Yellow
try {
    $deployResult = aws apigateway create-deployment --rest-api-id $apiId --stage-name $Environment --region $Region 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "API deployed successfully" -ForegroundColor Green
    } else {
        Write-Warning "Deployment had issues: $deployResult"
    }
} catch {
    Write-Warning "Failed to deploy API: $($_.Exception.Message)"
}

# Summary
Write-Host "CORS Integration Fix Summary:" -ForegroundColor Green
Write-Host "Total OPTIONS methods: $($optionsResources.Count)" -ForegroundColor Cyan
Write-Host "Fixed/Verified: $fixedCount" -ForegroundColor Cyan
Write-Host "API URL: https://$apiId.execute-api.$Region.amazonaws.com/$Environment" -ForegroundColor Cyan

if ($fixedCount -eq $optionsResources.Count) {
    Write-Host "All CORS integrations are now properly configured!" -ForegroundColor Green
} else {
    Write-Warning "Some CORS integrations may still need attention."
}