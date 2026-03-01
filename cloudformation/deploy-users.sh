#!/bin/bash
# Bash script to deploy user management Lambda function
# Usage: ./deploy-users.sh --environment dev --region us-east-1

set -e

# Default values
ENVIRONMENT="dev"
REGION="us-east-1"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -e, --environment ENV    Environment name (default: dev)"
            echo "  -r, --region REGION      AWS region (default: us-east-1)"
            echo "  -h, --help              Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "========================================"
echo "User Management Lambda Deployment"
echo "========================================"
echo ""

FUNCTION_NAME="msc-evaluate-user-crud-${ENVIRONMENT}"
BACKEND_PATH="../backend/users"
ZIP_FILE="user_crud.zip"

# Check if backend directory exists
if [ ! -d "$BACKEND_PATH" ]; then
    echo "Error: Backend directory not found: $BACKEND_PATH"
    exit 1
fi

# Navigate to backend directory
cd "$BACKEND_PATH"

echo "1. Packaging Lambda function..."

# Remove old zip if exists
rm -f "$ZIP_FILE"

# Create zip file
zip "$ZIP_FILE" user_crud.py

echo "   ✓ Package created: $ZIP_FILE"
echo ""

echo "2. Deploying to AWS Lambda..."

# Update Lambda function
aws lambda update-function-code \
    --function-name "$FUNCTION_NAME" \
    --zip-file "fileb://$ZIP_FILE" \
    --region "$REGION"

echo "   ✓ Lambda function updated successfully"
echo ""

echo "3. Initializing default users..."

TABLE_NAME="msc-evaluate-users-${ENVIRONMENT}"

# Check if Python is available
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "   ⚠ Python not found. Run 'python init_users.py $TABLE_NAME' manually"
    PYTHON_CMD=""
fi

if [ -n "$PYTHON_CMD" ]; then
    $PYTHON_CMD init_users.py "$TABLE_NAME"
    echo "   ✓ Default users initialized"
fi

echo ""
echo "========================================"
echo "Deployment Complete!"
echo "========================================"
echo ""
echo "Function Name: $FUNCTION_NAME"
echo "Region: $REGION"
echo ""
echo "Default Credentials:"
echo "  Admin:   admin / admin123"
echo "  Tutor:   tutor / tutor123"
echo "  Student: student / student123"
echo ""
