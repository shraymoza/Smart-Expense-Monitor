# Script to destroy AWS infrastructure for Smart Expense Monitor
# This will remove all AWS resources to stop costs
# Run this when you want to pause your project

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Destroying Smart Expense Monitor Infrastructure" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if AWS credentials exist
$credentialsFile = "aws-credentials.json"
if (-not (Test-Path $credentialsFile)) {
    Write-Host "Error: $credentialsFile not found!" -ForegroundColor Red
    Write-Host "Please create $credentialsFile with your AWS credentials." -ForegroundColor Yellow
    exit 1
}

# Load AWS credentials
Write-Host "Loading AWS credentials..." -ForegroundColor Green
try {
    $credentials = Get-Content $credentialsFile | ConvertFrom-Json
    
    # Support both naming conventions
    $accessKey = if ($credentials.access_key_id) { $credentials.access_key_id } else { $credentials.AWS_ACCESS_KEY_ID }
    $secretKey = if ($credentials.secret_access_key) { $credentials.secret_access_key } else { $credentials.AWS_SECRET_ACCESS_KEY }
    $region = if ($credentials.region) { $credentials.region } else { if ($credentials.AWS_DEFAULT_REGION) { $credentials.AWS_DEFAULT_REGION } else { "us-east-1" } }
    
    if (-not $accessKey -or $accessKey -eq "YOUR_ACCESS_KEY_ID_HERE") {
        Write-Host "Error: Please configure your AWS Access Key ID in aws-credentials.json" -ForegroundColor Red
        exit 1
    }
    
    if (-not $secretKey -or $secretKey -eq "YOUR_SECRET_ACCESS_KEY_HERE") {
        Write-Host "Error: Please configure your AWS Secret Access Key in aws-credentials.json" -ForegroundColor Red
        exit 1
    }
    
    $env:AWS_ACCESS_KEY_ID = $accessKey
    $env:AWS_SECRET_ACCESS_KEY = $secretKey
    $env:AWS_DEFAULT_REGION = $region
    $env:AWS_REGION = $region
    
    Write-Host "AWS credentials loaded successfully" -ForegroundColor Green
    Write-Host "   Region: $region" -ForegroundColor Cyan
    Write-Host ""
} catch {
    Write-Host "Error loading credentials: $_" -ForegroundColor Red
    exit 1
}

# Save important outputs before destroying
Write-Host "Saving current infrastructure outputs..." -ForegroundColor Yellow
if (Test-Path "terraform-outputs.json") {
    $outputs = Get-Content "terraform-outputs.json" | ConvertFrom-Json
    $backupFile = "terraform-outputs-backup-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
    Copy-Item "terraform-outputs.json" $backupFile
    Write-Host "Outputs backed up to: $backupFile" -ForegroundColor Green
}
Write-Host ""

# Initialize Terraform
Write-Host "Initializing Terraform..." -ForegroundColor Yellow
terraform init
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Terraform initialization failed!" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Show what will be destroyed
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "WARNING: This will destroy ALL resources!" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "The following resources will be destroyed:" -ForegroundColor Yellow
terraform plan -destroy
Write-Host ""

# Confirm destruction
$confirmation = Read-Host "Are you sure you want to destroy all resources? (yes/no)"
if ($confirmation -ne "yes") {
    Write-Host "Destruction cancelled." -ForegroundColor Green
    exit 0
}

# Destroy infrastructure
Write-Host ""
Write-Host "Destroying infrastructure..." -ForegroundColor Red
terraform destroy -auto-approve

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Infrastructure destroyed successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "All AWS resources have been removed." -ForegroundColor Green
    Write-Host "Your Terraform configuration files are preserved." -ForegroundColor Green
    Write-Host ""
    Write-Host "To redeploy tomorrow, run: .\deploy.ps1" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "Error: Destruction failed. Please check the errors above." -ForegroundColor Red
    exit 1
}

