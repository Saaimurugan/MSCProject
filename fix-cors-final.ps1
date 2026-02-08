#!/usr/bin/env pwsh
param(
    [string]$Region = "ap-south-1",
    [string]$Environment = "dev"
)

Write-Host "Fixing CORS integrations for API Gateway..." -ForegroundColor Green

$apiId = "08owx9a7c1"

# Resource IDs with OPTIONS methods
$resourceIds = @("1cg50h", "4pmasu", "58aeot", "6ode2g", "a75ubf", "bydc4w", "g3i6pe", "jw3a6e", "mydofr", "ojxug5", "tzcqsm", "ultkaf", "wsjlsc", "xm4w5f", "ynj05e")

$fixedCount = 0

foreach ($resourceId in $resourceIds) {
    Write-Host "Fixing OPTIONS for resource: $resourceId" -ForegroundColor Yellow
    
    try {
        # Create basic MOCK integration
        $result = aws apigateway put-integration --rest-api-id $apiId --resource-id $resourceId --http-method OPTIONS --type MOCK --region $Region 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  MOCK integration created" -ForegroundColor Green
            
            # Create method response
            aws apigateway put-method-response --rest-api-id $apiId --resource-id $resourceId --http-method OPTIONS --status-code 200 --response-parameters "method.response.header.Access-Control-Allow-Headers=false,method.response.header.Access-Control-Allow-Methods=false,method.response.header.Access-Control-Allow-Origin=false" --region $Region 2>$null
            
            # Create integration response with CORS headers
            aws apigateway put-integration-response --rest-api-id $apiId --resource-id $resourceId --http-method OPTIONS --status-code 200 --response-parameters '{"method.response.header.Access-Control-Allow-Headers":"Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token","method.response.header.Access-Control-Allow-Methods":"GET,POST,PUT,DELETE,OPTIONS","method.response.header.Access-Control-Allow-Origin":"*"}' --region $Region 2>$null
            
            $fixedCount++
        } else {
            Write-Warning "  Failed: $result"
        }
    } catch {
        Write-Warning "  Error: $($_.Exception.Message)"
    }
}

# Deploy API
Write-Host "Deploying API to $Environment stage..." -ForegroundColor Yellow
$deployResult = aws apigateway create-deployment --rest-api-id $apiId --stage-name $Environment --region $Region 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "API deployed successfully!" -ForegroundColor Green
    Write-Host "API URL: https://$apiId.execute-api.$Region.amazonaws.com/$Environment" -ForegroundColor Cyan
} else {
    Write-Host "Deployment had issues but may still work: $deployResult" -ForegroundColor Yellow
}

Write-Host "CORS Fix Summary:" -ForegroundColor Green
Write-Host "  Total OPTIONS methods: $($resourceIds.Count)" -ForegroundColor Cyan
Write-Host "  Successfully fixed: $fixedCount" -ForegroundColor Cyan