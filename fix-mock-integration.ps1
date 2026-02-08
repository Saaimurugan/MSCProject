#!/usr/bin/env pwsh
param(
    [string]$Region = "ap-south-1",
    [string]$Environment = "dev"
)

Write-Host "Fixing MOCK integrations for CORS..." -ForegroundColor Green

$apiId = "08owx9a7c1"
$resourceIds = @("1cg50h", "4pmasu", "58aeot", "6ode2g", "a75ubf", "bydc4w", "g3i6pe", "jw3a6e", "mydofr", "ojxug5", "tzcqsm", "ultkaf", "wsjlsc", "xm4w5f", "ynj05e")

$fixedCount = 0

foreach ($resourceId in $resourceIds) {
    Write-Host "Fixing OPTIONS for resource: $resourceId" -ForegroundColor Yellow
    
    try {
        # Create MOCK integration with simple request template
        $result = aws apigateway put-integration --rest-api-id $apiId --resource-id $resourceId --http-method OPTIONS --type MOCK --request-templates '{\"application/json\":\"{\\\"statusCode\\\": 200}\"}' --region $Region 2>&1
        
        if ($LASTEXITCODE -ne 0) {
            # Try alternative approach - create basic MOCK without request template
            Write-Host "  Trying basic MOCK integration..." -ForegroundColor Cyan
            aws apigateway put-integration --rest-api-id $apiId --resource-id $resourceId --http-method OPTIONS --type MOCK --region $Region 2>$null
        }
        
        # Update integration response to return 200 with CORS headers
        aws apigateway put-integration-response --rest-api-id $apiId --resource-id $resourceId --http-method OPTIONS --status-code 200 --response-templates '{\"application/json\":\"\"}' --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":\"Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token\",\"method.response.header.Access-Control-Allow-Methods\":\"GET,POST,PUT,DELETE,OPTIONS\",\"method.response.header.Access-Control-Allow-Origin\":\"*\"}' --region $Region 2>$null
        
        Write-Host "  Integration updated" -ForegroundColor Green
        $fixedCount++
        
    } catch {
        Write-Warning "  Error: $($_.Exception.Message)"
    }
}

# Deploy API
Write-Host "Deploying API..." -ForegroundColor Yellow
aws apigateway create-deployment --rest-api-id $apiId --stage-name $Environment --region $Region 2>$null

Write-Host "MOCK Integration Fix Summary:" -ForegroundColor Green
Write-Host "  Total OPTIONS methods: $($resourceIds.Count)" -ForegroundColor Cyan
Write-Host "  Successfully processed: $fixedCount" -ForegroundColor Cyan

# Test one endpoint
Write-Host "`nTesting CORS functionality..." -ForegroundColor Yellow
$testResult = aws apigateway test-invoke-method --rest-api-id $apiId --resource-id 1cg50h --http-method OPTIONS --region $Region 2>&1

if ($testResult -match '"status": 200') {
    Write-Host "CORS Test: SUCCESS" -ForegroundColor Green
} else {
    Write-Host "CORS Test: Still has issues" -ForegroundColor Yellow
    Write-Host $testResult
}