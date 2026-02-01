#!/bin/bash

# MSC Evaluate Deployment Script for Linux/macOS
set -e

# Default values
ENVIRONMENT="dev"
PROJECT_NAME="msc-evaluate"
REGION="us-east-1"
JWT_SECRET=""
SKIP_FRONTEND=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;36m'
NC='\033[0m' # No Color

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -p|--project)
            PROJECT_NAME="$2"
            shift 2
            ;;
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        -j|--jwt-secret)
            JWT_SECRET="$2"
            shift 2
            ;;
        --skip-frontend)
            SKIP_FRONTEND=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -e, --environment    Environment name (default: dev)"
            echo "  -p, --project        Project name (default: msc-evaluate)"
            echo "  -r, --region         AWS region (default: us-east-1)"
            echo "  -j, --jwt-secret     JWT secret key"
            echo "  --skip-frontend      Skip frontend build and deployment"
            echo "  -h, --help           Show this help message"
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

function check_prerequisites() {
    print_color $BLUE "🔍 Checking prerequisites..."
    
    # Check AWS CLI
    if command -v aws &> /dev/null; then
        AWS_VERSION=$(aws --version 2>&1)
        print_color $GREEN "✅ AWS CLI found: $AWS_VERSION"
    else
        print_color $RED "❌ AWS CLI not found. Please install AWS CLI first."
        exit 1
    fi
    
    # Check AWS credentials
    if aws sts get-caller-identity &> /dev/null; then
        ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
        print_color $GREEN "✅ AWS credentials configured for account: $ACCOUNT_ID"
    else
        print_color $RED "❌ AWS credentials not configured. Run 'aws configure' first."
        exit 1
    fi
    
    # Check Node.js (if not skipping frontend)
    if [ "$SKIP_FRONTEND" = false ]; then
        if command -v node &> /dev/null; then
            NODE_VERSION=$(node --version)
            print_color $GREEN "✅ Node.js found: $NODE_VERSION"
        else
            print_color $RED "❌ Node.js not found. Please install Node.js 18+ first."
            exit 1
        fi
        
        if command -v npm &> /dev/null; then
            NPM_VERSION=$(npm --version)
            print_color $GREEN "✅ npm found: $NPM_VERSION"
        else
            print_color $RED "❌ npm not found. Please install npm first."
            exit 1
        fi
    fi
    
    # Check Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        print_color $GREEN "✅ Python found: $PYTHON_VERSION"
    else
        print_color $RED "❌ Python not found. Please install Python 3.9+ first."
        exit 1
    fi
    
    # Check zip command
    if command -v zip &> /dev/null; then
        print_color $GREEN "✅ zip command found"
    else
        print_color $RED "❌ zip command not found. Please install zip utility."
        exit 1
    fi
}

function generate_jwt_secret() {
    if [ -z "$JWT_SECRET" ]; then
        JWT_SECRET=$(openssl rand -base64 48 | tr -d "=+/" | cut -c1-64)
        print_color $YELLOW "🔑 Generated JWT Secret: $JWT_SECRET"
    fi
    echo $JWT_SECRET
}

function deploy_infrastructure() {
    local jwt_secret=$1
    
    print_color $BLUE "🚀 Deploying infrastructure..."
    
    local stack_name="$PROJECT_NAME-infrastructure-$ENVIRONMENT"
    
    aws cloudformation deploy \
        --template-file "infrastructure/complete-infrastructure.yaml" \
        --stack-name "$stack_name" \
        --parameter-overrides \
            "ProjectName=$PROJECT_NAME" \
            "Environment=$ENVIRONMENT" \
            "JWTSecret=$jwt_secret" \
        --capabilities CAPABILITY_NAMED_IAM \
        --region "$REGION"
    
    if [ $? -eq 0 ]; then
        print_color $GREEN "✅ Infrastructure deployed successfully!"
    else
        print_color $RED "❌ Infrastructure deployment failed"
        exit 1
    fi
}

function get_stack_outputs() {
    local stack_name=$1
    
    aws cloudformation describe-stacks \
        --stack-name "$stack_name" \
        --region "$REGION" \
        --query "Stacks[0].Outputs" \
        --output json
}

function package_lambda_functions() {
    print_color $BLUE "📦 Packaging Lambda functions..."
    
    # Create temp directory for packaging
    local temp_dir="temp-lambda-packages"
    rm -rf "$temp_dir"
    mkdir -p "$temp_dir"
    
    # Define functions
    declare -A functions=(
        ["auth-login"]="backend/auth/login.py"
        ["auth-signup"]="backend/auth/signup.py"
        ["templates-get"]="backend/templates/get_templates.py"
        ["templates-create"]="backend/templates/create_template.py"
        ["quiz-get"]="backend/quiz/take_quiz.py"
        ["quiz-submit"]="backend/quiz/submit_quiz.py"
    )
    
    for func_name in "${!functions[@]}"; do
        print_color $YELLOW "  📦 Packaging $func_name..."
        
        local package_dir="$temp_dir/$func_name"
        mkdir -p "$package_dir"
        
        # Copy shared modules
        cp -r backend/shared/* "$package_dir/"
        
        # Copy function file
        local func_file=$(basename "${functions[$func_name]}")
        cp "${functions[$func_name]}" "$package_dir/$func_file"
        
        # Create zip file
        local zip_path="$temp_dir/$func_name.zip"
        (cd "$package_dir" && zip -r "../$func_name.zip" . > /dev/null)
        
        print_color $GREEN "  ✅ Created $zip_path"
    done
}

function update_lambda_functions() {
    local stack_outputs=$1
    
    print_color $BLUE "🔄 Updating Lambda functions..."
    
    declare -A functions=(
        ["auth-login"]="login.lambda_handler"
        ["auth-signup"]="signup.lambda_handler"
        ["templates-get"]="get_templates.lambda_handler"
        ["templates-create"]="create_template.lambda_handler"
        ["quiz-get"]="take_quiz.lambda_handler"
        ["quiz-submit"]="submit_quiz.lambda_handler"
    )
    
    for func_name in "${!functions[@]}"; do
        local function_name="$PROJECT_NAME-$func_name-$ENVIRONMENT"
        local zip_path="temp-lambda-packages/$func_name.zip"
        
        print_color $YELLOW "  🔄 Updating $function_name..."
        
        aws lambda update-function-code \
            --function-name "$function_name" \
            --zip-file "fileb://$zip_path" \
            --region "$REGION" > /dev/null
        
        if [ $? -eq 0 ]; then
            print_color $GREEN "  ✅ Updated $function_name"
        else
            print_color $RED "  ❌ Failed to update $function_name"
        fi
    done
}

function build_frontend() {
    local stack_outputs=$1
    
    if [ "$SKIP_FRONTEND" = true ]; then
        print_color $YELLOW "⏭️ Skipping frontend build..."
        return
    fi
    
    print_color $BLUE "🏗️ Building React frontend..."
    
    cd frontend
    
    # Install dependencies
    print_color $YELLOW "  📦 Installing dependencies..."
    npm install
    
    # Create environment file
    local api_url=$(echo "$stack_outputs" | jq -r '.[] | select(.OutputKey=="ApiGatewayUrl") | .OutputValue')
    echo "REACT_APP_API_URL=$api_url" > .env
    print_color $GREEN "  ✅ Created .env with API URL: $api_url"
    
    # Build for production
    print_color $YELLOW "  🏗️ Building for production..."
    npm run build
    
    if [ $? -eq 0 ]; then
        print_color $GREEN "  ✅ Frontend built successfully!"
    else
        print_color $RED "❌ Frontend build failed"
        exit 1
    fi
    
    cd ..
}

function deploy_frontend() {
    local stack_outputs=$1
    
    if [ "$SKIP_FRONTEND" = true ]; then
        print_color $YELLOW "⏭️ Skipping frontend deployment..."
        return
    fi
    
    print_color $BLUE "🚀 Deploying frontend to S3..."
    
    local bucket_name=$(echo "$stack_outputs" | jq -r '.[] | select(.OutputKey=="FrontendBucketName") | .OutputValue')
    
    aws s3 sync "frontend/build/" "s3://$bucket_name" --delete --region "$REGION"
    
    if [ $? -eq 0 ]; then
        print_color $GREEN "✅ Frontend deployed to S3!"
    else
        print_color $RED "❌ Frontend deployment failed"
        exit 1
    fi
}

function cleanup() {
    print_color $BLUE "🧹 Cleaning up temporary files..."
    
    if [ -d "temp-lambda-packages" ]; then
        rm -rf "temp-lambda-packages"
        print_color $GREEN "✅ Cleaned up temporary files"
    fi
}

function show_deployment_summary() {
    local stack_outputs=$1
    
    local api_url=$(echo "$stack_outputs" | jq -r '.[] | select(.OutputKey=="ApiGatewayUrl") | .OutputValue')
    local cloudfront_url=$(echo "$stack_outputs" | jq -r '.[] | select(.OutputKey=="CloudFrontUrl") | .OutputValue')
    local bucket_name=$(echo "$stack_outputs" | jq -r '.[] | select(.OutputKey=="FrontendBucketName") | .OutputValue')
    
    print_color $GREEN "\n🎉 Deployment completed successfully!"
    print_color $BLUE "=================================================="
    print_color $BLUE "📊 Deployment Summary:"
    print_color $YELLOW "  Environment: $ENVIRONMENT"
    print_color $YELLOW "  Region: $REGION"
    print_color $YELLOW "  API Gateway URL: $api_url"
    
    if [ "$SKIP_FRONTEND" = false ]; then
        print_color $YELLOW "  Frontend URL: $cloudfront_url"
        print_color $YELLOW "  S3 Bucket: $bucket_name"
    fi
    
    print_color $BLUE "\n🔗 Next Steps:"
    print_color $YELLOW "  1. Wait 5-10 minutes for CloudFront distribution to deploy"
    print_color $YELLOW "  2. Access your application at: $cloudfront_url"
    print_color $YELLOW "  3. Create your first admin user via the signup page"
    print_color $BLUE "=================================================="
}

# Main execution
function main() {
    print_color $BLUE "🚀 MSC Evaluate Deployment Script"
    print_color $YELLOW "Environment: $ENVIRONMENT | Region: $REGION"
    
    check_prerequisites
    
    JWT_SECRET=$(generate_jwt_secret)
    
    deploy_infrastructure "$JWT_SECRET"
    
    local stack_name="$PROJECT_NAME-infrastructure-$ENVIRONMENT"
    local stack_outputs=$(get_stack_outputs "$stack_name")
    
    package_lambda_functions
    update_lambda_functions "$stack_outputs"
    
    build_frontend "$stack_outputs"
    deploy_frontend "$stack_outputs"
    
    show_deployment_summary "$stack_outputs"
    
    print_color $GREEN "\n✅ Deployment script completed!"
}

# Trap to ensure cleanup on exit
trap cleanup EXIT

# Run main function
main