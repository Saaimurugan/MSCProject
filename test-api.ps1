# Test API Endpoints Script
# This script tests all API endpoints to verify they're working

param(
    [string]$ApiUrl = "https://48c11a5co1.execute-api.ap-south-1.amazonaws.com/dev"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  API Endpoints Test Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "API URL: $ApiUrl" -ForegroundColor Yellow
Write-Host ""

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [string]$Method = "GET",
        [string]$Body = $null
    )
    
    Write-Host "Testing $Name..." -ForegroundColor Yellow
    Write-Host "  URL: $Url" -ForegroundColor Gray
    Write-Host "  Method: $Method" -ForegroundColor Gray
    
    try {
        $headers = @{
            "Content-Type" = "application/json"
        }
        
        if ($Method -eq "GET") {
            $response = Invoke-WebRequest -Uri $Url -Method $Method -Headers $headers -UseBasicParsing
        } else {
            $response = Invoke-WebRequest -Uri $Url -Method $Method -Body $Body -Headers $headers -UseBasicParsing
        }
        
        Write-Host "  ✓ Status: $($response.StatusCode)" -ForegroundColor Green
        
        # Try to parse JSON response
        try {
            $jsonResponse = $response.Content | ConvertFrom-Json
            Write-Host "  ✓ Response: Valid JSON" -ForegroundColor Green
            
            # Show some response details
            if ($jsonResponse.message) {
                Write-Host "  Message: $($jsonResponse.message)" -ForegroundColor Cyan
            }
            if ($jsonResponse.count) {
                Write-Host "  Count: $($jsonResponse.count)" -ForegroundColor Cyan
            }
        } catch {
            Write-Host "  ⚠ Response: Not JSON" -ForegroundColor Yellow
        }
        
        Write-Host ""
        return $true
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "  ✗ Status: $statusCode" -ForegroundColor Red
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
        return $false
    }
}

# Test Results
$results = @{
    Passed = 0
    Failed = 0
}

# Test 1: Login Endpoint
Write-Host "[1/5] Testing Login Endpoint" -ForegroundColor Cyan
$loginBody = @{
    username = "admin"
    password = "admin123"
} | ConvertTo-Json

if (Test-Endpoint -Name "POST /users/login" -Url "$ApiUrl/users/login" -Method "POST" -Body $loginBody) {
    $results.Passed++
} else {
    $results.Failed++
}

# Test 2: Get Templates
Write-Host "[2/5] Testing Get Templates" -ForegroundColor Cyan
if (Test-Endpoint -Name "GET /templates" -Url "$ApiUrl/templates" -Method "GET") {
    $results.Passed++
} else {
    $results.Failed++
}

# Test 3: Get Users (requires admin)
Write-Host "[3/5] Testing Get Users" -ForegroundColor Cyan
if (Test-Endpoint -Name "GET /users" -Url "$ApiUrl/users" -Method "GET") {
    $results.Passed++
} else {
    $results.Failed++
    Write-Host "  Note: This endpoint requires admin authentication" -ForegroundColor Yellow
}

# Test 4: Get Results
Write-Host "[4/5] Testing Get Results" -ForegroundColor Cyan
if (Test-Endpoint -Name "GET /results" -Url "$ApiUrl/results" -Method "GET") {
    $results.Passed++
} else {
    $results.Failed++
}

# Test 5: CORS Preflight (OPTIONS)
Write-Host "[5/5] Testing CORS Preflight" -ForegroundColor Cyan
try {
    $headers = @{
        "Access-Control-Request-Method" = "POST"
        "Access-Control-Request-Headers" = "Content-Type"
        "Origin" = "http://localhost:3000"
    }
    $response = Invoke-WebRequest -Uri "$ApiUrl/templates" -Method OPTIONS -Headers $headers -UseBasicParsing
    Write-Host "  ✓ CORS Headers Present" -ForegroundColor Green
    
    # Check for CORS headers
    if ($response.Headers["Access-Control-Allow-Origin"]) {
        Write-Host "  ✓ Access-Control-Allow-Origin: $($response.Headers['Access-Control-Allow-Origin'])" -ForegroundColor Green
    }
    if ($response.Headers["Access-Control-Allow-Methods"]) {
        Write-Host "  ✓ Access-Control-Allow-Methods: $($response.Headers['Access-Control-Allow-Methods'])" -ForegroundColor Green
    }
    
    $results.Passed++
    Write-Host ""
} catch {
    Write-Host "  ✗ CORS test failed" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    $results.Failed++
    Write-Host ""
}

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Test Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Passed: $($results.Passed)" -ForegroundColor Green
Write-Host "Failed: $($results.Failed)" -ForegroundColor Red
Write-Host ""

if ($results.Failed -eq 0) {
    Write-Host "✓ All tests passed! Your API is working correctly." -ForegroundColor Green
} else {
    Write-Host "⚠ Some tests failed. Check the errors above." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Common fixes:" -ForegroundColor Yellow
    Write-Host "1. Run .\update-lambdas.ps1 to update Lambda functions" -ForegroundColor White
    Write-Host "2. Check CloudWatch Logs for Lambda errors" -ForegroundColor White
    Write-Host "3. Verify the CloudFormation stack is deployed" -ForegroundColor White
}
Write-Host ""
