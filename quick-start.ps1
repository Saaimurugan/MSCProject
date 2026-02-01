# MSC Evaluate - Quick Start Script for AWS
# This script checks prerequisites and guides you through deployment

param(
    [switch]$CheckOnly = $false
)

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Cyan"
$Magenta = "Magenta"

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Show-Banner {
    Write-ColorOutput @"
╔══════════════════════════════════════════════════════════════╗
║                    MSC Evaluate - Quick Start                ║
║                   AWS Serverless Deployment                  ║
╚══════════════════════════════════════════════════════════════╝
"@ $Blue
}

function Check-Prerequisites {
    Write-ColorOutput "`n🔍 Checking Prerequisites..." $Blue
    $allGood = $true
    
    # Check AWS CLI
    try {
        $awsVersion = aws --version 2>$null
        Write-ColorOutput "✅ AWS CLI: $awsVersion" $Green
    } catch {
        Write-ColorOutput "❌ AWS CLI not found" $Red
        Write-ColorOutput "   Install from: https://aws.amazon.com/cli/" $Yellow
        $allGood = $false
    }
    
    # Check AWS credentials
    try {
        $identity = aws sts get-caller-identity 2>$null | ConvertFrom-Json
        Write-ColorOutput "✅ AWS Account: $($identity.Account)" $Green
        Write-ColorOutput "   User/Role: $($identity.Arn)" $Yellow
    } catch {
        Write-ColorOutput "❌ AWS credentials not configured" $Red
        Write-ColorOutput "   Run: aws configure" $Yellow
        $allGood = $false
    }
    
    # Check Node.js
    try {
        $nodeVersion = node --version 2>$null
        Write-ColorOutput "✅ Node.js: $nodeVersion" $Green
    } catch {
        Write-ColorOutput "❌ Node.js not found" $Red
        Write-ColorOutput "   Install from: https://nodejs.org" $Yellow
        $allGood = $false
    }
    
    # Check Python
    try {
        $pythonVersion = python --version 2>$null
        Write-ColorOutput "✅ Python: $pythonVersion" $Green
    } catch {
        Write-ColorOutput "❌ Python not found" $Red
        Write-ColorOutput "   Install Python 3.9+ from: https://python.org" $Yellow
        $allGood = $false
    }
    
    # Check PowerShell execution policy
    $policy = Get-ExecutionPolicy
    if ($policy -eq "Restricted") {
        Write-ColorOutput "⚠️  PowerShell execution policy is Restricted" $Yellow
        Write-ColorOutput "   Run: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" $Yellow
    } else {
        Write-ColorOutput "✅ PowerShell execution policy: $policy" $Green
    }
    
    return $allGood
}

function Show-AWS-Regions {
    Write-ColorOutput "`n🌍 Popular AWS Regions:" $Blue
    Write-ColorOutput "   us-east-1      (N. Virginia) - Default, lowest latency for US East" $Yellow
    Write-ColorOutput "   us-west-2      (Oregon) - US West Coast" $Yellow
    Write-ColorOutput "   eu-west-1      (Ireland) - Europe" $Yellow
    Write-ColorOutput "   ap-southeast-1 (Singapore) - Asia Pacific" $Yellow
    Write-ColorOutput "   ap-south-1     (Mumbai) - India" $Yellow
}

function Get-User-Preferences {
    Write-ColorOutput "`n⚙️  Configuration Setup" $Blue
    
    # Environment
    $environment = Read-Host "Environment name (dev/staging/prod) [dev]"
    if ([string]::IsNullOrEmpty($environment)) { $environment = "dev" }
    
    # Region
    Show-AWS-Regions
    $region = Read-Host "AWS Region [us-east-1]"
    if ([string]::IsNullOrEmpty($region)) { $region = "us-east-1" }
    
    # Project name
    $projectName = Read-Host "Project name [msc-evaluate]"
    if ([string]::IsNullOrEmpty($projectName)) { $projectName = "msc-evaluate" }
    
    # Skip frontend option
    $skipFrontendInput = Read-Host "Skip frontend deployment? (y/N) [N]"
    $skipFrontend = $skipFrontendInput -eq "y" -or $skipFrontendInput -eq "Y"
    
    return @{
        Environment = $environment
        Region = $region
        ProjectName = $projectName
        SkipFrontend = $skipFrontend
    }
}

function Show-Deployment-Command {
    param($Config)
    
    Write-ColorOutput "`n🚀 Ready to Deploy!" $Green
    Write-ColorOutput "Your deployment command:" $Blue
    
    $command = ".\deploy.ps1 -Environment `"$($Config.Environment)`" -Region `"$($Config.Region)`" -ProjectName `"$($Config.ProjectName)`""
    if ($Config.SkipFrontend) {
        $command += " -SkipFrontend"
    }
    
    Write-ColorOutput $command $Magenta
    
    Write-ColorOutput "`nEstimated deployment time: 10-15 minutes" $Yellow
    Write-ColorOutput "Estimated monthly cost: $1-65 (depending on usage)" $Yellow
}

function Show-Next-Steps {
    Write-ColorOutput "`n📋 Next Steps:" $Blue
    Write-ColorOutput "1. Review the deployment command above" $Yellow
    Write-ColorOutput "2. Run the deployment command when ready" $Yellow
    Write-ColorOutput "3. Wait for deployment to complete (10-15 minutes)" $Yellow
    Write-ColorOutput "4. Access your application using the provided URLs" $Yellow
    Write-ColorOutput "5. Create your first admin user via signup" $Yellow
    
    Write-ColorOutput "`n📚 Documentation:" $Blue
    Write-ColorOutput "   README.md - Complete project documentation" $Yellow
    Write-ColorOutput "   AWS-DEPLOYMENT-GUIDE.md - Detailed AWS deployment guide" $Yellow
    Write-ColorOutput "   deployment-guide.md - Manual deployment steps" $Yellow
}

function Show-Troubleshooting {
    Write-ColorOutput "`n🔧 Troubleshooting:" $Blue
    Write-ColorOutput "   If deployment fails:" $Yellow
    Write-ColorOutput "   1. Check AWS credentials and permissions" $Yellow
    Write-ColorOutput "   2. Verify all prerequisites are installed" $Yellow
    Write-ColorOutput "   3. Check CloudWatch logs for detailed errors" $Yellow
    Write-ColorOutput "   4. Run cleanup script if needed: .\destroy.ps1" $Yellow
}

# Main execution
Show-Banner

$prereqsOk = Check-Prerequisites

if ($CheckOnly) {
    if ($prereqsOk) {
        Write-ColorOutput "`n✅ All prerequisites are satisfied!" $Green
        Write-ColorOutput "You're ready to deploy MSC Evaluate to AWS!" $Green
    } else {
        Write-ColorOutput "`n❌ Please install missing prerequisites before deployment" $Red
    }
    exit
}

if (-not $prereqsOk) {
    Write-ColorOutput "`n❌ Prerequisites check failed!" $Red
    Write-ColorOutput "Please install missing components and run this script again." $Yellow
    Write-ColorOutput "Or run with -CheckOnly flag to just check prerequisites." $Yellow
    exit 1
}

$config = Get-User-Preferences
Show-Deployment-Command -Config $config

$proceed = Read-Host "`nProceed with deployment? (Y/n) [Y]"
if ($proceed -eq "n" -or $proceed -eq "N") {
    Write-ColorOutput "Deployment cancelled. Run this script again when ready!" $Yellow
    exit 0
}

# Run the deployment
Write-ColorOutput "`n🚀 Starting deployment..." $Green
$deployArgs = @(
    "-Environment", $config.Environment,
    "-Region", $config.Region,
    "-ProjectName", $config.ProjectName
)
if ($config.SkipFrontend) {
    $deployArgs += "-SkipFrontend"
}

try {
    & ".\deploy.ps1" @deployArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput "`n🎉 Deployment completed successfully!" $Green
        Show-Next-Steps
    } else {
        Write-ColorOutput "`n❌ Deployment failed!" $Red
        Show-Troubleshooting
    }
} catch {
    Write-ColorOutput "`n❌ Deployment error: $_" $Red
    Show-Troubleshooting
}