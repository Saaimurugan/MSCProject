#!/bin/bash

# MSC Evaluate Destruction Script for Linux/macOS
set -e

# Default values
ENVIRONMENT="dev"
PROJECT_NAME="msc-evaluate"
REGION="us-east-1"
FORCE=false

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
        -f|--force)
            FORCE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -e, --environment    Environment name (default: dev)"
            echo "  -p, --project        Project name (default: msc-evaluate)"
            echo "  -r, --region         AWS region (default: us-east-1)"
            echo "  -f, --force          Skip confirmation prompt"
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

function confirm_destruction() {
    if [ "$FORCE" = false ]; then
        print_color $RED "⚠️  WARNING: This will destroy all resources for environment '$ENVIRONMENT'"
        print_color $YELLOW "This includes:"
        print_color $YELLOW "  - All DynamoDB tables and data"
        print_color $YELLOW "  - All Lambda functions"
        print_color $YELLOW "  - API Gateway"
        print_color $YELLOW "  - S3 bucket and website content"
        print_color $YELLOW "  - CloudFront distribution"
        
        echo -n "Type 'DELETE' to confirm destruction: "
        read confirmation
        if [ "$confirmation" != "DELETE" ]; then
            print_color $GREEN "❌ Destruction cancelled"
            exit 0
        fi
    fi
}

function empty_s3_bucket() {
    local bucket_name=$1
    
    if [ -z "$bucket_name" ]; then
        return
    fi
    
    print_color $YELLOW "🗑️ Emptying S3 bucket: $bucket_name"
    
    # Check if bucket exists
    if aws s3api head-bucket --bucket "$bucket_name" --region "$REGION" 2>/dev/null; then
        # Empty the bucket
        aws s3 rm "s3://$bucket_name" --recursive --region "$REGION"
        print_color $GREEN "✅ S3 bucket emptied successfully"
    else
        print_color $BLUE "ℹ️ S3 bucket does not exist or already empty"
    fi
}

function get_s3_bucket_name() {
    local stack_name=$1
    
    local bucket_name=$(aws cloudformation describe-stacks \
        --stack-name "$stack_name" \
        --region "$REGION" \
        --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" \
        --output text 2>/dev/null || echo "")
    
    if [ -n "$bucket_name" ] && [ "$bucket_name" != "None" ]; then
        echo "$bucket_name"
    fi
}

function delete_cloudformation_stack() {
    local stack_name=$1
    
    print_color $YELLOW "🗑️ Deleting CloudFormation stack: $stack_name"
    
    # Check if stack exists
    if ! aws cloudformation describe-stacks --stack-name "$stack_name" --region "$REGION" &>/dev/null; then
        print_color $BLUE "ℹ️ Stack '$stack_name' does not exist"
        return
    fi
    
    # Delete the stack
    aws cloudformation delete-stack --stack-name "$stack_name" --region "$REGION"
    
    print_color $BLUE "⏳ Waiting for stack deletion to complete..."
    aws cloudformation wait stack-delete-complete --stack-name "$stack_name" --region "$REGION"
    
    if [ $? -eq 0 ]; then
        print_color $GREEN "✅ Stack deleted successfully"
    else
        print_color $YELLOW "⚠️ Stack deletion may have failed or timed out"
    fi
}

function show_destruction_summary() {
    print_color $BLUE "\n🎯 Destruction Summary:"
    print_color $BLUE "========================================"
    print_color $YELLOW "  Environment: $ENVIRONMENT"
    print_color $YELLOW "  Region: $REGION"
    print_color $YELLOW "  Project: $PROJECT_NAME"
    print_color $GREEN "\n✅ All resources have been destroyed!"
    print_color $BLUE "========================================"
}

# Main execution
function main() {
    print_color $RED "🗑️ MSC Evaluate Destruction Script"
    print_color $YELLOW "Environment: $ENVIRONMENT | Region: $REGION"
    
    confirm_destruction
    
    local stack_name="$PROJECT_NAME-infrastructure-$ENVIRONMENT"
    
    # Get S3 bucket name before deleting stack
    local bucket_name=$(get_s3_bucket_name "$stack_name")
    
    # Empty S3 bucket first (required before stack deletion)
    if [ -n "$bucket_name" ]; then
        empty_s3_bucket "$bucket_name"
    fi
    
    # Delete CloudFormation stack
    delete_cloudformation_stack "$stack_name"
    
    show_destruction_summary
    
    print_color $GREEN "\n✅ Destruction script completed!"
}

# Run main function
main