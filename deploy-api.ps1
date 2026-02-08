#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Deploy MSC Evaluate API Gateway
.DESCRIPTION
    This script creates API Gateway endpoints for all Lambda functions with CORS enabled and deploys to the specified stage.
.PARAMETER Region
    AWS region (default: ap-south-1)
.PARAMETER Environment
    Environment name (default: dev)
.PARAMETER StageName
    API Gateway stage name (default: dev)
#>

param(
    [string]$Region = "ap-south-1",
    [string]$Environment = "dev",
    [string]$StageName = "dev"
)

# Set error action preference
$ErrorActionPreference = "Stop"

Write-Host "Starting MSC Evaluate API Gateway Deployment" -ForegroundColor Green
Write-Host "Region: $Region" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Cyan
Write-Host "Stage: $StageName" -ForegroundColor Cyan

# Check if AWS CLI is installed
try {
    aws --version | Out-Null
} catch {
    Write-Error "AWS CLI is not installed or not in PATH. Please install AWS CLI first."
    exit 1
}

# Check AWS credentials
try {
    aws sts get-caller-identity | Out-Null
    Write-Host "AWS credentials verified" -ForegroundColor Green
} catch {
    Write-Error "AWS credentials not configured. Please run 'aws configure' first."
    exit 1
}

# API Gateway configuration
$apiName = "msc-evaluate-api-$Environment"
$apiDescription = "MSC Evaluate Quiz Application API"

# Define API endpoints and their corresponding Lambda functions
$apiEndpoints = @(
    @{
        Path = "/auth/login"
        Method = "POST"
        LambdaFunction = "msc-evaluate-auth-login-$Environment"
        Description = "User login endpoint"
    },
    @{
        Path = "/auth/signup"
        Method = "POST"
        LambdaFunction = "msc-evaluate-auth-signup-$Environment"
        Description = "User registration endpoint"
    },
    @{
        Path = "/admin/users"
        Method = "GET"
        LambdaFunction = "msc-evaluate-admin-get-users-$Environment"
        Description = "Get all users (admin only)"
    },
    @{
        Path = "/admin/users"
        Method = "POST"
        LambdaFunction = "msc-evaluate-admin-create-user-$Environment"
        Description = "Create new user (admin only)"
    },
    @{
        Path = "/admin/users/{userId}"
        Method = "DELETE"
        LambdaFunction = "msc-evaluate-admin-delete-user-$Environment"
        Description = "Delete user (admin only)"
    },
    @{
        Path = "/admin/users/{userId}/role"
        Method = "PUT"
        LambdaFunction = "msc-evaluate-admin-update-user-role-$Environment"
        Description = "Update user role (admin only)"
    },
    @{
        Path = "/admin/usage-logs"
        Method = "GET"
        LambdaFunction = "msc-evaluate-admin-get-usage-logs-$Environment"
        Description = "Get usage logs (admin only)"
    },
    @{
        Path = "/profile"
        Method = "GET"
        LambdaFunction = "msc-evaluate-profile-get-profile-$Environment"
        Description = "Get user profile"
    },
    @{
        Path = "/profile"
        Method = "PUT"
        LambdaFunction = "msc-evaluate-profile-update-profile-$Environment"
        Description = "Update user profile"
    },
    @{
        Path = "/profile/password"
        Method = "PUT"
        LambdaFunction = "msc-evaluate-profile-change-password-$Environment"
        Description = "Change user password"
    },
    @{
        Path = "/templates"
        Method = "GET"
        LambdaFunction = "msc-evaluate-templates-get-templates-$Environment"
        Description = "Get quiz templates"
    },
    @{
        Path = "/templates"
        Method = "POST"
        LambdaFunction = "msc-evaluate-templates-create-template-$Environment"
        Description = "Create quiz template"
    },
    @{
        Path = "/quiz/take"
        Method = "POST"
        LambdaFunction = "msc-evaluate-quiz-take-quiz-$Environment"
        Description = "Start taking a quiz"
    },
    @{
        Path = "/quiz/submit"
        Method = "POST"
        LambdaFunction = "msc-evaluate-quiz-submit-quiz-$Environment"
        Description = "Submit quiz for evaluation"
    },
    @{
        Path = "/reports"
        Method = "GET"
        LambdaFunction = "msc-evaluate-reports-get-all-reports-$Environment"
        Description = "Get all reports (admin/tutor)"
    },
    @{
        Path = "/reports/user/{userId}"
        Method = "GET"
        LambdaFunction = "msc-evaluate-reports-get-user-reports-$Environment"
        Description = "Get user-specific reports"
    },
    @{
        Path = "/reports/template/{templateId}"
        Method = "GET"
        LambdaFunction = "msc-evaluate-reports-get-template-reports-$Environment"
        Description = "Get template-specific reports"
    },
    @{
        Path = "/ai/evaluate"
        Method = "POST"
        LambdaFunction = "msc-evaluate-ai-scorer-$Environment"
        Description = "AI-powered answer evaluation"
    }
)

# Global variables
$apiId = ""
$accountId = ""

# Function to get AWS account ID
function Get-AccountId {
    try {
        $identity = aws sts get-caller-identity | ConvertFrom-Json
        return $identity.Account
    } catch {
        Write-Error "Failed to get AWS account ID"
        exit 1
    }
}

# Function to check if API Gateway exists
function Test-ApiGateway {
    param([string]$ApiName)
    try {
        $apis = aws apigateway get-rest-apis --region $Region | ConvertFrom-Json
        $api = $apis.items | Where-Object { $_.name -eq $ApiName }
        return $api
    } catch {
        return $null
    }
}

# Function to create API Gateway
function New-ApiGateway {
    param([string]$ApiName, [string]$Description)
    
    Write-Host "Creating API Gateway: $ApiName" -ForegroundColor Yellow
    
    try {
        $api = aws apigateway create-rest-api --name $ApiName --description $Description --region $Region | ConvertFrom-Json
        Write-Host "API Gateway created: $($api.id)" -ForegroundColor Green
        return $api
    } catch {
        Write-Error "Failed to create API Gateway: $($_.Exception.Message)"
        exit 1
    }
}

# Function to get root resource ID
function Get-RootResourceId {
    param([string]$ApiId)
    
    try {
        $resources = aws apigateway get-resources --rest-api-id $ApiId --region $Region | ConvertFrom-Json
        $rootResource = $resources.items | Where-Object { $_.path -eq "/" }
        return $rootResource.id
    } catch {
        Write-Error "Failed to get root resource ID"
        exit 1
    }
}

# Function to create resource path
function New-ResourcePath {
    param(
        [string]$ApiId,
        [string]$ParentId,
        [string]$PathPart
    )
    
    # First check if resource already exists
    try {
        $resources = aws apigateway get-resources --rest-api-id $ApiId --region $Region | ConvertFrom-Json
        $existingResource = $resources.items | Where-Object { $_.pathPart -eq $PathPart -and $_.parentId -eq $ParentId }
        if ($existingResource) {
            return $existingResource.id
        }
    } catch {
        Write-Warning "Could not check existing resources"
    }
    
    # Try to create new resource
    try {
        $resource = aws apigateway create-resource --rest-api-id $ApiId --parent-id $ParentId --path-part $PathPart --region $Region | ConvertFrom-Json
        return $resource.id
    } catch {
        # If creation failed, try to find existing resource again
        try {
            $resources = aws apigateway get-resources --rest-api-id $ApiId --region $Region | ConvertFrom-Json
            $existingResource = $resources.items | Where-Object { $_.pathPart -eq $PathPart -and $_.parentId -eq $ParentId }
            if ($existingResource) {
                return $existingResource.id
            }
        } catch {
            Write-Error "Failed to create or find resource: $PathPart"
            return $null
        }
    }
}

# Function to create resource hierarchy
function New-ResourceHierarchy {
    param(
        [string]$ApiId,
        [string]$Path
    )
    
    $pathParts = $Path.Trim('/').Split('/')
    $currentParentId = Get-RootResourceId -ApiId $ApiId
    
    foreach ($part in $pathParts) {
        if ($part -and $currentParentId) {
            $newResourceId = New-ResourcePath -ApiId $ApiId -ParentId $currentParentId -PathPart $part
            if ($newResourceId) {
                $currentParentId = $newResourceId
            } else {
                Write-Warning "Failed to create/find resource: $part"
                return $null
            }
        }
    }
    
    return $currentParentId
}

# Function to create method
function New-Method {
    param(
        [string]$ApiId,
        [string]$ResourceId,
        [string]$HttpMethod,
        [string]$LambdaFunction
    )
    
    if (-not $ResourceId) {
        Write-Warning "Invalid ResourceId for $HttpMethod $LambdaFunction"
        return
    }
    
    try {
        # Create method
        aws apigateway put-method --rest-api-id $ApiId --resource-id $ResourceId --http-method $HttpMethod --authorization-type "NONE" --region $Region 2>$null | Out-Null
        
        # Create integration
        $lambdaArn = "arn:aws:lambda:${Region}:${accountId}:function:${LambdaFunction}"
        $integrationUri = "arn:aws:apigateway:${Region}:lambda:path/2015-03-31/functions/${lambdaArn}/invocations"
        
        aws apigateway put-integration --rest-api-id $ApiId --resource-id $ResourceId --http-method $HttpMethod --type AWS_PROXY --integration-http-method POST --uri $integrationUri --region $Region 2>$null | Out-Null
        
        # Add Lambda permission
        $statementId = "apigateway-$ApiId-$ResourceId-$HttpMethod"
        $sourceArn = "arn:aws:execute-api:${Region}:${accountId}:${ApiId}/*/*"
        aws lambda add-permission --function-name $LambdaFunction --statement-id $statementId --action lambda:InvokeFunction --principal apigateway.amazonaws.com --source-arn $sourceArn --region $Region 2>$null | Out-Null
        
        Write-Host "Method created: $HttpMethod for $LambdaFunction" -ForegroundColor Green
        
    } catch {
        Write-Warning "Failed to create method $HttpMethod for $LambdaFunction : $($_.Exception.Message)"
    }
}

# Function to enable CORS
function Enable-CORS {
    param(
        [string]$ApiId,
        [string]$ResourceId
    )
    
    try {
        # Create OPTIONS method
        aws apigateway put-method --rest-api-id $ApiId --resource-id $ResourceId --http-method OPTIONS --authorization-type "NONE" --region $Region 2>$null | Out-Null
        
        # Create mock integration for OPTIONS
        $requestTemplates = '{"application/json": "{\"statusCode\": 200}"}'
        aws apigateway put-integration --rest-api-id $ApiId --resource-id $ResourceId --http-method OPTIONS --type MOCK --request-templates $requestTemplates --region $Region 2>$null | Out-Null
        
        # Create method response for OPTIONS
        aws apigateway put-method-response --rest-api-id $ApiId --resource-id $ResourceId --http-method OPTIONS --status-code 200 --response-parameters "method.response.header.Access-Control-Allow-Headers=false,method.response.header.Access-Control-Allow-Methods=false,method.response.header.Access-Control-Allow-Origin=false" --region $Region 2>$null | Out-Null
        
        # Create integration response for OPTIONS
        $responseParams = '{"method.response.header.Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token", "method.response.header.Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS", "method.response.header.Access-Control-Allow-Origin": "*"}'
        aws apigateway put-integration-response --rest-api-id $ApiId --resource-id $ResourceId --http-method OPTIONS --status-code 200 --response-parameters $responseParams --region $Region 2>$null | Out-Null
        
    } catch {
        Write-Warning "Failed to enable CORS for resource: $($_.Exception.Message)"
    }
}

# Function to deploy API
function Deploy-Api {
    param(
        [string]$ApiId,
        [string]$StageName
    )
    
    Write-Host "Deploying API to stage: $StageName" -ForegroundColor Yellow
    
    try {
        aws apigateway create-deployment --rest-api-id $ApiId --stage-name $StageName --region $Region | Out-Null
        
        $apiUrl = "https://$ApiId.execute-api.$Region.amazonaws.com/$StageName"
        Write-Host "API deployed successfully" -ForegroundColor Green
        Write-Host "API URL: $apiUrl" -ForegroundColor Cyan
        
        return $apiUrl
        
    } catch {
        Write-Error "Failed to deploy API: $($_.Exception.Message)"
        exit 1
    }
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

# Main deployment process
try {
    # Get AWS account ID
    $accountId = Get-AccountId
    Write-Host "Account ID: $accountId" -ForegroundColor Cyan
    
    # Check if API Gateway exists
    $existingApi = Test-ApiGateway -ApiName $apiName
    
    if ($existingApi) {
        Write-Host "API Gateway already exists: $($existingApi.name)" -ForegroundColor Green
        $apiId = $existingApi.id
    } else {
        $api = New-ApiGateway -ApiName $apiName -Description $apiDescription
        $apiId = $api.id
    }
    
    Write-Host "API ID: $apiId" -ForegroundColor Cyan
    
    # Create endpoints
    $createdEndpoints = @()
    $resourceCache = @{}
    
    foreach ($endpoint in $apiEndpoints) {
        Write-Host "Processing endpoint: $($endpoint.Method) $($endpoint.Path)" -ForegroundColor Yellow
        
        # Check if Lambda function exists
        if (-not (Test-LambdaFunction -FunctionName $endpoint.LambdaFunction)) {
            Write-Warning "Lambda function not found: $($endpoint.LambdaFunction). Skipping endpoint."
            continue
        }
        
        try {
            # Create resource hierarchy
            $resourceId = ""
            if ($resourceCache.ContainsKey($endpoint.Path)) {
                $resourceId = $resourceCache[$endpoint.Path]
            } else {
                $resourceId = New-ResourceHierarchy -ApiId $apiId -Path $endpoint.Path
                $resourceCache[$endpoint.Path] = $resourceId
            }
            
            # Create method
            New-Method -ApiId $apiId -ResourceId $resourceId -HttpMethod $endpoint.Method -LambdaFunction $endpoint.LambdaFunction
            
            # Enable CORS for this resource
            Enable-CORS -ApiId $apiId -ResourceId $resourceId
            
            $createdEndpoints += $endpoint
            
        } catch {
            Write-Warning "Failed to create endpoint $($endpoint.Method) $($endpoint.Path): $($_.Exception.Message)"
        }
    }
    
    # Deploy API
    if ($createdEndpoints.Count -gt 0) {
        $apiUrl = Deploy-Api -ApiId $apiId -StageName $StageName
        
        Write-Host "API Gateway deployment completed successfully!" -ForegroundColor Green
        Write-Host "API Name: $apiName" -ForegroundColor Cyan
        Write-Host "API ID: $apiId" -ForegroundColor Cyan
        Write-Host "Region: $Region" -ForegroundColor Cyan
        Write-Host "Stage: $StageName" -ForegroundColor Cyan
        Write-Host "API URL: $apiUrl" -ForegroundColor Cyan
        Write-Host "Endpoints created: $($createdEndpoints.Count)" -ForegroundColor Cyan
        
        # Display endpoint summary
        Write-Host "API Endpoints:" -ForegroundColor Blue
        foreach ($endpoint in $createdEndpoints) {
            Write-Host "  $($endpoint.Method) $apiUrl$($endpoint.Path) -> $($endpoint.LambdaFunction)" -ForegroundColor White
        }
        
    } else {
        Write-Warning "No endpoints were created. Please check that Lambda functions exist."
    }
    
} catch {
    Write-Error "API Gateway deployment failed: $($_.Exception.Message)"
    exit 1
}