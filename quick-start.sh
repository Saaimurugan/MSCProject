#!/bin/bash

# MSC Evaluate - Quick Start Script for AWS
# This script checks prerequisites and guides you through deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

CHECK_ONLY=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --check-only)
            CHECK_ONLY=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--check-only]"
            echo "  --check-only    Only check prerequisites, don't deploy"
            exit 0
            ;;
        *)
            echo "Unknown option $1"
            exit 1
            ;;
    esac
done

function print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

function show_banner() {
    print_color $BLUE "╔══════════════════════════════════════════════════════════════╗"
    print_color $BLUE "║                    MSC Evaluate - Quick Start                ║"
    print_color $BLUE "║                   AWS Serverless Deployment                  ║"
    print_color $BLUE "╚══════════════════════════════════════════════════════════════╝"
}

function check_prerequisites() {
    print_color $BLUE "\n🔍 Checking Prerequisites..."
    local all_good=true
    
    # Check AWS CLI
    if command -v aws &> /dev/null; then
        local aws_version=$(aws --version 2>&1)
        print_color $GREEN "✅ AWS CLI: $aws_version"
    else
        print_color $RED "❌ AWS CLI not found"
        print_color $YELLOW "   Install from: https://aws.amazon.com/cli/"
        all_good=false
    fi
    
    # Check AWS credentials
    if aws sts get-caller-identity &> /dev/null; then
        local account_id=$(aws sts get-caller-identity --query Account --output text)
        local user_arn=$(aws sts get-caller-identity --query Arn --output text)
        print_color $GREEN "✅ AWS Account: $account_id"
        print_color $YELLOW "   User/Role: $user_arn"
    else
        print_color $RED "❌ AWS credentials not configured"
        print_color $YELLOW "   Run: aws configure"
        all_good=false
    fi
    
    # Check Node.js
    if command -v node &> /dev/null; then
        local node_version=$(node --version)
        print_color $GREEN "✅ Node.js: $node_version"
    else
        print_color $RED "❌ Node.js not found"
        print_color $YELLOW "   Install from: https://nodejs.org"
        all_good=false
    fi
    
    # Check npm
    if command -v npm &> /dev/null; then
        local npm_version=$(npm --version)
        print_color $GREEN "✅ npm: $npm_version"
    else
        print_color $RED "❌ npm not found"
        print_color $YELLOW "   Install Node.js which includes npm"
        all_good=false
    fi
    
    # Check Python
    if command -v python3 &> /dev/null; then
        local python_version=$(python3 --version)
        print_color $GREEN "✅ Python: $python_version"
    else
        print_color $RED "❌ Python not found"
        print_color $YELLOW "   Install Python 3.9+ from: https://python.org"
        all_good=false
    fi
    
    # Check zip
    if command -v zip &> /dev/null; then
        print_color $GREEN "✅ zip utility found"
    else
        print_color $RED "❌ zip utility not found"
        print_color $YELLOW "   Install: sudo apt install zip (Ubuntu/Debian) or brew install zip (macOS)"
        all_good=false
    fi
    
    # Check jq (for JSON parsing)
    if command -v jq &> /dev/null; then
        print_color $GREEN "✅ jq found"
    else
        print_color $YELLOW "⚠️  jq not found (recommended for JSON parsing)"
        print_color $YELLOW "   Install: sudo apt install jq (Ubuntu/Debian) or brew install jq (macOS)"
    fi
    
    if [ "$all_good" = true ]; then
        return 0
    else
        return 1
    fi
}

function show_aws_regions() {
    print_color $BLUE "\n🌍 Popular AWS Regions:"
    print_color $YELLOW "   us-east-1      (N. Virginia) - Default, lowest latency for US East"
    print_color $YELLOW "   us-west-2      (Oregon) - US West Coast"
    print_color $YELLOW "   eu-west-1      (Ireland) - Europe"
    print_color $YELLOW "   ap-southeast-1 (Singapore) - Asia Pacific"
    print_color $YELLOW "   ap-south-1     (Mumbai) - India"
}

function get_user_preferences() {
    print_color $BLUE "\n⚙️  Configuration Setup"
    
    # Environment
    echo -n "Environment name (dev/staging/prod) [dev]: "
    read environment
    environment=${environment:-dev}
    
    # Region
    show_aws_regions
    echo -n "AWS Region [us-east-1]: "
    read region
    region=${region:-us-east-1}
    
    # Project name
    echo -n "Project name [msc-evaluate]: "
    read project_name
    project_name=${project_name:-msc-evaluate}
    
    # Skip frontend option
    echo -n "Skip frontend deployment? (y/N) [N]: "
    read skip_frontend_input
    if [[ "$skip_frontend_input" == "y" || "$skip_frontend_input" == "Y" ]]; then
        skip_frontend=true
    else
        skip_frontend=false
    fi
    
    # Return values via global variables
    CONFIG_ENVIRONMENT="$environment"
    CONFIG_REGION="$region"
    CONFIG_PROJECT_NAME="$project_name"
    CONFIG_SKIP_FRONTEND="$skip_frontend"
}

function show_deployment_command() {
    print_color $GREEN "\n🚀 Ready to Deploy!"
    print_color $BLUE "Your deployment command:"
    
    local command="./deploy.sh --environment \"$CONFIG_ENVIRONMENT\" --region \"$CONFIG_REGION\" --project \"$CONFIG_PROJECT_NAME\""
    if [ "$CONFIG_SKIP_FRONTEND" = true ]; then
        command="$command --skip-frontend"
    fi
    
    print_color $MAGENTA "$command"
    
    print_color $YELLOW "\nEstimated deployment time: 10-15 minutes"
    print_color $YELLOW "Estimated monthly cost: \$1-65 (depending on usage)"
}

function show_next_steps() {
    print_color $BLUE "\n📋 Next Steps:"
    print_color $YELLOW "1. Review the deployment command above"
    print_color $YELLOW "2. Run the deployment command when ready"
    print_color $YELLOW "3. Wait for deployment to complete (10-15 minutes)"
    print_color $YELLOW "4. Access your application using the provided URLs"
    print_color $YELLOW "5. Create your first admin user via signup"
    
    print_color $BLUE "\n📚 Documentation:"
    print_color $YELLOW "   README.md - Complete project documentation"
    print_color $YELLOW "   AWS-DEPLOYMENT-GUIDE.md - Detailed AWS deployment guide"
    print_color $YELLOW "   deployment-guide.md - Manual deployment steps"
}

function show_troubleshooting() {
    print_color $BLUE "\n🔧 Troubleshooting:"
    print_color $YELLOW "   If deployment fails:"
    print_color $YELLOW "   1. Check AWS credentials and permissions"
    print_color $YELLOW "   2. Verify all prerequisites are installed"
    print_color $YELLOW "   3. Check CloudWatch logs for detailed errors"
    print_color $YELLOW "   4. Run cleanup script if needed: ./destroy.sh"
}

# Main execution
show_banner

if ! check_prerequisites; then
    if [ "$CHECK_ONLY" = true ]; then
        print_color $RED "\n❌ Prerequisites check failed!"
        print_color $YELLOW "Please install missing components before deployment."
        exit 1
    else
        print_color $RED "\n❌ Prerequisites check failed!"
        print_color $YELLOW "Please install missing components and run this script again."
        print_color $YELLOW "Or run with --check-only flag to just check prerequisites."
        exit 1
    fi
fi

if [ "$CHECK_ONLY" = true ]; then
    print_color $GREEN "\n✅ All prerequisites are satisfied!"
    print_color $GREEN "You're ready to deploy MSC Evaluate to AWS!"
    exit 0
fi

get_user_preferences
show_deployment_command

echo -n -e "\nProceed with deployment? (Y/n) [Y]: "
read proceed
if [[ "$proceed" == "n" || "$proceed" == "N" ]]; then
    print_color $YELLOW "Deployment cancelled. Run this script again when ready!"
    exit 0
fi

# Run the deployment
print_color $GREEN "\n🚀 Starting deployment..."

# Build deployment arguments
deploy_args=(
    "--environment" "$CONFIG_ENVIRONMENT"
    "--region" "$CONFIG_REGION" 
    "--project" "$CONFIG_PROJECT_NAME"
)

if [ "$CONFIG_SKIP_FRONTEND" = true ]; then
    deploy_args+=("--skip-frontend")
fi

# Make deploy script executable if not already
chmod +x deploy.sh

# Run deployment
if ./deploy.sh "${deploy_args[@]}"; then
    print_color $GREEN "\n🎉 Deployment completed successfully!"
    show_next_steps
else
    print_color $RED "\n❌ Deployment failed!"
    show_troubleshooting
    exit 1
fi