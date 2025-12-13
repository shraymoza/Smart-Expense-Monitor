# Script to extract Terraform outputs for AWS Amplify environment variables
# Run this after deploying your infrastructure

Write-Host "Extracting Terraform outputs for Amplify environment variables..." -ForegroundColor Cyan
Write-Host ""

cd terraform

# Get Terraform outputs
$outputs = terraform output -json | ConvertFrom-Json

if (-not $outputs) {
    Write-Host "Error: Could not get Terraform outputs. Make sure Terraform is initialized and deployed." -ForegroundColor Red
    exit 1
}

Write-Host "=== Copy these environment variables to AWS Amplify Console ===" -ForegroundColor Green
Write-Host ""
Write-Host "REACT_APP_AWS_REGION=us-east-1" -ForegroundColor Yellow
Write-Host "REACT_APP_COGNITO_USER_POOL_ID=$($outputs.cognito_user_pool_id.value)" -ForegroundColor Yellow
Write-Host "REACT_APP_COGNITO_CLIENT_ID=$($outputs.cognito_user_pool_client_id.value)" -ForegroundColor Yellow
Write-Host "REACT_APP_API_GATEWAY_URL=$($outputs.api_gateway_url.value)" -ForegroundColor Yellow
Write-Host "REACT_APP_S3_BUCKET_NAME=$($outputs.s3_bucket_name.value)" -ForegroundColor Yellow
Write-Host ""
Write-Host "=== Instructions ===" -ForegroundColor Green
Write-Host "1. Go to AWS Amplify Console" -ForegroundColor White
Write-Host "2. Select your app" -ForegroundColor White
Write-Host "3. Go to App settings > Environment variables" -ForegroundColor White
Write-Host "4. Add each variable above" -ForegroundColor White
Write-Host "5. Save and redeploy" -ForegroundColor White
Write-Host ""

cd ..

