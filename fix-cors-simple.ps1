#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Simple CORS Fix for API Gateway
.DESCRIPTION
    This script fixes CORS by creating proper MOCK integrations for OPTIONS methods.
#>

param(
    [string]$Region = "ap-south-1",
    [string]$Environment = "dev"
)

Write-Host "Fixing CORS integrations..." -ForegroundColor Green

$apiId = "08owx9a7c1"

# Create temporary JSON files for request templates
$requestTemplate = @'
{
  "application/json": "{\"statusCode\": 200}"
}
'@

$responseParams = @'
{
  "method.response.header.Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
  "method.response.header.Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
  "method.response.header.Access-Control-Allow-Origin": "*"
}
'@

$requestTemplate | Out-File -FilePath "request-template.json" -Encoding utf8
$responseParams | Out-File -FilePath "response-params.json" -Encoding utf8

# List of resource IDs that have OPTIONS methods
$resourceIds = @("1cg50h", "4pmasu", "58aeot", "6ode2g", "a75ubf", "bydc4w", "g3i6pe", "jw3a6e", "mydofr", "ojxug5", "tzcqsm", "ultkaf", "wsjlsc", "xm4w5f", "ynj05e")

$fixedCount = 0

foreach ($resourceId in $resourceIds) {
    Write-Host "Fixing resource: $resourceId" -ForegroundColor Yellow
    
    try {
        # Create MOCK integration
        $result = aws apigateway put-integration --rest-api-id $apiId --resource-id $resourceId --http-method OPTIONS --type MOCK --request-templates file://request-template.json --region $Region 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  MOCK integration created" -ForegroundColor Green
            
            # Create method response (ignore if exists)
            aws apigateway put-method-response --rest-api-id $apiId --resource-id $resourceId --http-method OPTIONS --status-code 200 --response-parameters "method.response.header.Access-Control-Allow-Headers=false,method.response.header.Access-Control-Allow-Methods=false,method.response.header.Access-Control-Allow-Origin=false" --region $Region 2>$null
            
            # Create integration response
            $intResult = aws apigateway put-integration-response --rest-api-id $apiId --resource-id $resourceId --http-method OPTIONS --status-code 200 --response-parameters file://response-params.json --region $Region 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  Integration response created" -ForegroundColor Green
                $fixedCount++
            } else {
                Write-Warning "  Failed to create integration response: $intResult"
            }
        } else {
            Write-Warning "  Failed to create integration: $result"
        }
    } catch {
        Write-Warning "  Error: $($_.Exception.Message)"
    }
}

# Clean up temp files
Remove-Item "request-template.json" -ErrorAction SilentlyContinue
Remove-Item "response-params.json" -ErrorAction SilentlyContinue

# Deploy API
Write-Host "Deploying API..." -ForegroundColor Yellow
$deployResult = aws apigateway create-deployment --rest-api-id $apiId --stage-name $Environment --region $Region 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "API deployed successfully!" -ForegroundColor Green
} else {
    Write-Host "Deployment result: $deployResult" -ForegroundColor Yellow
}

Write-Host "Summary:" -ForegroundColor Green
Write-Host "  Resources processed: $($resourceIds.Count)" -ForegroundColor Cyan
Write-Host "  Successfully fixed: $fixedCount" -ForegroundColor Cyan
Write-Host "  API URL: https://$apiId.execute-api.$Region.amazonaws.com/$Environment" -ForegroundColor Cyan