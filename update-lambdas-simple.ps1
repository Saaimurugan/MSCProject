$Region = "ap-south-1"
$Environment = "dev"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Lambda Functions Update Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$rootDir = Get-Location

Write-Host "[1/6] Updating user-crud Lambda..." -ForegroundColor Green
Set-Location "$rootDir\backend\users"
if (Test-Path "user_crud.zip") { Remove-Item "user_crud.zip" -Force }
Compress-Archive -Path "user_crud.py" -DestinationPath "user_crud.zip" -Force
aws lambda update-function-code --function-name "msc-evaluate-user-crud-$Environment" --zip-file fileb://user_crud.zip --region $Region
Write-Host "   ✓ user-crud updated" -ForegroundColor Green
Write-Host ""

Write-Host "[2/6] Updating template-api Lambda..." -ForegroundColor Green
Set-Location "$rootDir\backend\templates"
if (Test-Path "template_api.zip") { Remove-Item "template_api.zip" -Force }
Compress-Archive -Path "template_api.py" -DestinationPath "template_api.zip" -Force
aws lambda update-function-code --function-name "msc-evaluate-template-api-$Environment" --zip-file fileb://template_api.zip --region $Region
Write-Host "   ✓ template-api updated" -ForegroundColor Green
Write-Host ""

Write-Host "[3/6] Updating take-quiz Lambda..." -ForegroundColor Green
Set-Location "$rootDir\backend\quiz"
if (Test-Path "take_quiz.zip") { Remove-Item "take_quiz.zip" -Force }
Compress-Archive -Path "take_quiz.py" -DestinationPath "take_quiz.zip" -Force
aws lambda update-function-code --function-name "msc-evaluate-take-quiz-$Environment" --zip-file fileb://take_quiz.zip --region $Region
Write-Host "   ✓ take-quiz updated" -ForegroundColor Green
Write-Host ""

Write-Host "[4/6] Updating submit-quiz Lambda..." -ForegroundColor Green
if (Test-Path "submit_quiz.zip") { Remove-Item "submit_quiz.zip" -Force }
Compress-Archive -Path "submit_quiz.py" -DestinationPath "submit_quiz.zip" -Force
aws lambda update-function-code --function-name "msc-evaluate-submit-quiz-$Environment" --zip-file fileb://submit_quiz.zip --region $Region
Write-Host "   ✓ submit-quiz updated" -ForegroundColor Green
Write-Host ""

Write-Host "[5/6] Updating get-results Lambda..." -ForegroundColor Green
if (Test-Path "get_results.zip") { Remove-Item "get_results.zip" -Force }
Compress-Archive -Path "get_results.py" -DestinationPath "get_results.zip" -Force
aws lambda update-function-code --function-name "msc-evaluate-get-results-$Environment" --zip-file fileb://get_results.zip --region $Region
Write-Host "   ✓ get-results updated" -ForegroundColor Green
Write-Host ""

Write-Host "[6/6] Updating delete-result Lambda..." -ForegroundColor Green
if (Test-Path "delete_result.zip") { Remove-Item "delete_result.zip" -Force }
Compress-Archive -Path "delete_result.py" -DestinationPath "delete_result.zip" -Force
aws lambda update-function-code --function-name "msc-evaluate-delete-result-$Environment" --zip-file fileb://delete_result.zip --region $Region
Write-Host "   ✓ delete-result updated" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Redeploying API Gateway" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $rootDir
$apiId = aws cloudformation describe-stack-resources --stack-name "msc-evaluate-stack-$Environment" --region $Region --query "StackResources[?ResourceType=='AWS::ApiGateway::RestApi'].PhysicalResourceId" --output text

if ($apiId) {
    Write-Host "API Gateway ID: $apiId" -ForegroundColor Yellow
    aws apigateway create-deployment --rest-api-id $apiId --stage-name $Environment --region $Region
    Write-Host "   ✓ API Gateway redeployed" -ForegroundColor Green
} else {
    Write-Host "   ⚠ Could not find API Gateway ID" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ✓ All Updates Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Clear your browser cache (Ctrl+Shift+Delete)" -ForegroundColor White
Write-Host "2. Refresh the application" -ForegroundColor White
Write-Host "3. Try logging in again" -ForegroundColor White
Write-Host ""

Set-Location $rootDir
