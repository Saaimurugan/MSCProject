# MSC Evaluate Deployment Script for Windows PowerShell
param(
    [string]$Environment = "dev",
    [string]$ProjectName = "msc-evaluate",
    [string]$Region = "us-east-1",
    [string]$JWTSecret = "",
    [switch]$SkipFrontend = $false
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

function Check-Prerequisites {
    Write-ColorOutput "🔍 Checking prerequisites..." $Blue
    
    # Check AWS CLI
    try {
        $awsVersion = aws --version 2>$null
        Write-ColorOutput "✅ AWS CLI found: $awsVersion" $Green
    } catch {
        Write-ColorOutput "❌ AWS CLI not found. Please install AWS CLI first." $Red
        exit 1
    }
    
    # Check AWS credentials
    try {
        $identity = aws sts get-caller-identity 2>$null | ConvertFrom-Json
        Write-ColorOutput "✅ AWS credentials configured for account: $($identity.Account)" $Green
    } catch {
        Write-ColorOutput "❌ AWS credentials not configured. Run 'aws configure' first." $Red
        exit 1
    }
    
    # Check Node.js (if not skipping frontend)
    if (-not $SkipFrontend) {
        try {
            $nodeVersion = node --version 2>$null
            Write-ColorOutput "✅ Node.js found: $nodeVersion" $Green
        } catch {
            Write-ColorOutput "❌ Node.js not found. Please install Node.js 18+ first." $Red
            exit 1
        }
    }
    
    # Check Python
    try {
        $pythonVersion = python --version 2>$null
        Write-ColorOutput "✅ Python found: $pythonVersion" $Green
    } catch {
        Write-ColorOutput "❌ Python not found. Please install Python 3.9+ first." $Red
        exit 1
    }
}

function Generate-JWTSecret {
    if ([string]::IsNullOrEmpty($JWTSecret)) {
        $JWTSecret = -join ((1..64) | ForEach {Get-Random -input ([char[]]([char]'a'..[char]'z') + [char[]]([char]'A'..[char]'Z') + [char[]]([char]'0'..[char]'9'))})
        Write-ColorOutput "🔑 Generated JWT Secret: $JWTSecret" $Yellow
    }
    return $JWTSecret
}

function Deploy-Infrastructure {
    param([string]$JWTSecret)
    
    Write-ColorOutput "🚀 Deploying infrastructure..." $Blue
    
    $stackName = "$ProjectName-infrastructure-$Environment"
    
    try {
        aws cloudformation deploy `
            --template-file "infrastructure/complete-infrastructure.yaml" `
            --stack-name $stackName `
            --parameter-overrides `
                "ProjectName=$ProjectName" `
                "Environment=$Environment" `
                "JWTSecret=$JWTSecret" `
            --capabilities CAPABILITY_NAMED_IAM `
            --region $Region
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ Infrastructure deployed successfully!" $Green
        } else {
            throw "CloudFormation deployment failed"
        }
    } catch {
        Write-ColorOutput "❌ Infrastructure deployment failed: $_" $Red
        exit 1
    }
}

function Get-StackOutputs {
    param([string]$StackName)
    
    try {
        $outputs = aws cloudformation describe-stacks `
            --stack-name $StackName `
            --region $Region `
            --query "Stacks[0].Outputs" | ConvertFrom-Json
        
        $outputHash = @{}
        foreach ($output in $outputs) {
            $outputHash[$output.OutputKey] = $output.OutputValue
        }
        return $outputHash
    } catch {
        Write-ColorOutput "❌ Failed to get stack outputs: $_" $Red
        exit 1
    }
}

function Package-Lambda-Functions {
    Write-ColorOutput "📦 Packaging Lambda functions..." $Blue
    
    # Create temp directory for packaging
    $tempDir = "temp-lambda-packages"
    if (Test-Path $tempDir) {
        Remove-Item $tempDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $tempDir | Out-Null
    
    # Package each Lambda function
    $functions = @(
        @{Name="auth-login"; Handler="login.lambda_handler"; Path="backend/auth/login.py"},
        @{Name="auth-signup"; Handler="signup.lambda_handler"; Path="backend/auth/signup.py"},
        @{Name="templates-get"; Handler="get_templates.lambda_handler"; Path="backend/templates/get_templates.py"},
        @{Name="templates-create"; Handler="create_template.lambda_handler"; Path="backend/templates/create_template.py"},
        @{Name="quiz-get"; Handler="take_quiz.lambda_handler"; Path="backend/quiz/take_quiz.py"},
        @{Name="quiz-submit"; Handler="submit_quiz.lambda_handler"; Path="backend/quiz/submit_quiz.py"}
    )
    
    foreach ($func in $functions) {
        Write-ColorOutput "  📦 Packaging $($func.Name)..." $Yellow
        
        $packageDir = "$tempDir/$($func.Name)"
        New-Item -ItemType Directory -Path $packageDir | Out-Null
        
        # Copy shared modules
        Copy-Item "backend/shared/*" $packageDir -Recurse
        
        # Copy function file
        $functionFile = Split-Path $func.Path -Leaf
        Copy-Item $func.Path "$packageDir/$functionFile"
        
        # Create zip file
        $zipPath = "$tempDir/$($func.Name).zip"
        Compress-Archive -Path "$packageDir/*" -DestinationPath $zipPath -Force
        
        Write-ColorOutput "  ✅ Created $zipPath" $Green
    }
    
    return $functions
}

function Update-Lambda-Functions {
    param([array]$Functions, [hashtable]$StackOutputs)
    
    Write-ColorOutput "🔄 Updating Lambda functions..." $Blue
    
    foreach ($func in $Functions) {
        $functionName = "$ProjectName-$($func.Name)-$Environment"
        $zipPath = "temp-lambda-packages/$($func.Name).zip"
        
        Write-ColorOutput "  🔄 Updating $functionName..." $Yellow
        
        try {
            aws lambda update-function-code `
                --function-name $functionName `
                --zip-file "fileb://$zipPath" `
                --region $Region | Out-Null
            
            Write-ColorOutput "  ✅ Updated $functionName" $Green
        } catch {
            Write-ColorOutput "  ❌ Failed to update $functionName : $_" $Red
        }
    }
}

function Build-Frontend {
    param([hashtable]$StackOutputs)
    
    if ($SkipFrontend) {
        Write-ColorOutput "⏭️ Skipping frontend build..." $Yellow
        return
    }
    
    Write-ColorOutput "🏗️ Building React frontend..." $Blue
    
    Push-Location "frontend"
    
    try {
        # Install dependencies
        Write-ColorOutput "  📦 Installing dependencies..." $Yellow
        npm install
        
        # Create environment file
        $apiUrl = $StackOutputs["ApiGatewayUrl"]
        $envContent = "REACT_APP_API_URL=$apiUrl"
        $envContent | Out-File -FilePath ".env" -Encoding UTF8
        Write-ColorOutput "  ✅ Created .env with API URL: $apiUrl" $Green
        
        # Build for production
        Write-ColorOutput "  🏗️ Building for production..." $Yellow
        npm run build
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "  ✅ Frontend built successfully!" $Green
        } else {
            throw "Frontend build failed"
        }
    } catch {
        Write-ColorOutput "❌ Frontend build failed: $_" $Red
        exit 1
    } finally {
        Pop-Location
    }
}

function Deploy-Frontend {
    param([hashtable]$StackOutputs)
    
    if ($SkipFrontend) {
        Write-ColorOutput "⏭️ Skipping frontend deployment..." $Yellow
        return
    }
    
    Write-ColorOutput "🚀 Deploying frontend to S3..." $Blue
    
    $bucketName = $StackOutputs["FrontendBucketName"]
    
    try {
        aws s3 sync "frontend/build/" "s3://$bucketName" --delete --region $Region
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ Frontend deployed to S3!" $Green
        } else {
            throw "S3 sync failed"
        }
    } catch {
        Write-ColorOutput "❌ Frontend deployment failed: $_" $Red
        exit 1
    }
}

function Cleanup {
    Write-ColorOutput "🧹 Cleaning up temporary files..." $Blue
    
    if (Test-Path "temp-lambda-packages") {
        Remove-Item "temp-lambda-packages" -Recurse -Force
        Write-ColorOutput "✅ Cleaned up temporary files" $Green
    }
}

function Show-Deployment-Summary {
    param([hashtable]$StackOutputs)
    
    Write-ColorOutput "`n🎉 Deployment completed successfully!" $Green
    Write-ColorOutput "=" * 50 $Blue
    Write-ColorOutput "📊 Deployment Summary:" $Blue
    Write-ColorOutput "  Environment: $Environment" $Yellow
    Write-ColorOutput "  Region: $Region" $Yellow
    Write-ColorOutput "  API Gateway URL: $($StackOutputs['ApiGatewayUrl'])" $Yellow
    
    if (-not $SkipFrontend) {
        Write-ColorOutput "  Frontend URL: $($StackOutputs['CloudFrontUrl'])" $Yellow
        Write-ColorOutput "  S3 Bucket: $($StackOutputs['FrontendBucketName'])" $Yellow
    }
    
    Write-ColorOutput "`n🔗 Next Steps:" $Blue
    Write-ColorOutput "  1. Wait 5-10 minutes for CloudFront distribution to deploy" $Yellow
    Write-ColorOutput "  2. Access your application at: $($StackOutputs['CloudFrontUrl'])" $Yellow
    Write-ColorOutput "  3. Create your first admin user via the signup page" $Yellow
    Write-ColorOutput "=" * 50 $Blue
}

# Main execution
try {
    Write-ColorOutput "🚀 MSC Evaluate Deployment Script" $Blue
    Write-ColorOutput "Environment: $Environment | Region: $Region" $Yellow
    
    Check-Prerequisites
    $JWTSecret = Generate-JWTSecret
    Deploy-Infrastructure -JWTSecret $JWTSecret
    
    $stackName = "$ProjectName-infrastructure-$Environment"
    $stackOutputs = Get-StackOutputs -StackName $stackName
    
    $functions = Package-Lambda-Functions
    Update-Lambda-Functions -Functions $functions -StackOutputs $stackOutputs
    
    Build-Frontend -StackOutputs $stackOutputs
    Deploy-Frontend -StackOutputs $stackOutputs
    
    Show-Deployment-Summary -StackOutputs $stackOutputs
    
} catch {
    Write-ColorOutput "❌ Deployment failed: $_" $Red
    exit 1
} finally {
    Cleanup
}

Write-ColorOutput "`n✅ Deployment script completed!" $Green