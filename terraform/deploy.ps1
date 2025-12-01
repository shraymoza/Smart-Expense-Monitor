# deploy.ps1
# Automated deployment script for Smart Expense Monitor infrastructure
# This script handles AWS credentials, Lambda packaging, and Terraform deployment

param(
    [switch]$SkipZip,
    [switch]$SkipPlan,
    [switch]$Destroy
)

$ErrorActionPreference = "Stop"

# Colors for output
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Warning { Write-Host $args -ForegroundColor Yellow }
function Write-Error { Write-Host $args -ForegroundColor Red }

Write-Info "Smart Expense Monitor - Terraform Deployment Script"
Write-Info "====================================================`n"

# Step 1: Check for AWS credentials file
$credentialsFile = Join-Path $PSScriptRoot "aws-credentials.json"
$credentialsExample = Join-Path $PSScriptRoot "aws-credentials.json.example"

if (-not (Test-Path $credentialsFile)) {
    Write-Warning "AWS credentials file not found!"
    Write-Info "Creating credentials file from example..."
    
    if (Test-Path $credentialsExample) {
        Copy-Item $credentialsExample $credentialsFile
        Write-Info "Please edit 'aws-credentials.json' and add your AWS credentials"
        Write-Info "   File location: $credentialsFile"
        Write-Error "Deployment aborted. Please configure credentials and run again."
        exit 1
    } else {
        Write-Error "Credentials example file not found. Please create aws-credentials.json manually."
        exit 1
    }
}

# Step 2: Load AWS credentials
Write-Info "Loading AWS credentials from file..."
try {
    $credentials = Get-Content $credentialsFile | ConvertFrom-Json
    
    if (-not $credentials.access_key_id -or $credentials.access_key_id -eq "YOUR_ACCESS_KEY_ID_HERE") {
        Write-Error "Please configure your AWS Access Key ID in aws-credentials.json"
        exit 1
    }
    
    if (-not $credentials.secret_access_key -or $credentials.secret_access_key -eq "YOUR_SECRET_ACCESS_KEY_HERE") {
        Write-Error "Please configure your AWS Secret Access Key in aws-credentials.json"
        exit 1
    }
    
    $env:AWS_ACCESS_KEY_ID = $credentials.access_key_id
    $env:AWS_SECRET_ACCESS_KEY = $credentials.secret_access_key
    $env:AWS_DEFAULT_REGION = if ($credentials.region) { $credentials.region } else { "us-east-1" }
    $env:AWS_REGION = $env:AWS_DEFAULT_REGION
    
    Write-Success "AWS credentials loaded"
    Write-Info "   Region: $env:AWS_DEFAULT_REGION`n"
} catch {
    Write-Error "Error loading credentials: $_"
    exit 1
}

# Step 3: Create Lambda zip file (if not skipped)
if (-not $SkipZip) {
    Write-Info "Creating Lambda deployment package..."
    
    $lambdaDir = Join-Path $PSScriptRoot "..\backend\lambda_functions"
    $lambdaZip = Join-Path $lambdaDir "receipt_processor.zip"
    $lambdaScript = Join-Path $lambdaDir "receipt_processor.py"
    
    # Resolve relative paths
    $lambdaDir = Resolve-Path $lambdaDir -ErrorAction SilentlyContinue
    if (-not $lambdaDir) {
        Write-Error "Lambda functions directory not found: $lambdaDir"
        exit 1
    }
    
    $lambdaScript = Join-Path $lambdaDir "receipt_processor.py"
    $lambdaZip = Join-Path $lambdaDir "receipt_processor.zip"
    
    if (-not (Test-Path $lambdaScript)) {
        Write-Error "Lambda function file not found: $lambdaScript"
        exit 1
    }
    
    # Remove old zip if exists
    if (Test-Path $lambdaZip) {
        Remove-Item $lambdaZip -Force
        Write-Info "   Removed existing zip file"
    }
    
    # Create zip file
    try {
        # Ensure we're in the right directory
        Push-Location $lambdaDir
        Compress-Archive -Path "receipt_processor.py" -DestinationPath "receipt_processor.zip" -Force
        Pop-Location
        Write-Success "Lambda zip file created: $lambdaZip`n"
    } catch {
        if ($PWD.Path -ne $PSScriptRoot) { Pop-Location }
        Write-Error "Error creating zip file: $_"
        exit 1
    }
} else {
    Write-Info "Skipping Lambda zip creation`n"
}

# Step 4: Setup terraform.tfvars if it doesn't exist
$tfvarsFile = Join-Path $PSScriptRoot "terraform.tfvars"
$tfvarsExample = Join-Path $PSScriptRoot "terraform.tfvars.example"

if (-not (Test-Path $tfvarsFile)) {
    Write-Info "Creating terraform.tfvars from example..."
    
    if (Test-Path $tfvarsExample) {
        Copy-Item $tfvarsExample $tfvarsFile
        Write-Success "terraform.tfvars created (using default values)"
        Write-Info "   You can edit it to customize your deployment`n"
    } else {
        Write-Warning "terraform.tfvars.example not found. Using defaults."
    }
} else {
    Write-Info "Using existing terraform.tfvars`n"
}

# Step 5: Initialize Terraform
Write-Info "Initializing Terraform..."
try {
    Push-Location $PSScriptRoot
    terraform init
    if ($LASTEXITCODE -ne 0) {
        throw "Terraform init failed"
    }
    Write-Success "Terraform initialized`n"
} catch {
    Write-Error "Terraform initialization failed: $_"
    Pop-Location
    exit 1
}

# Step 6: Validate Terraform configuration
Write-Info "Validating Terraform configuration..."
try {
    terraform validate
    if ($LASTEXITCODE -ne 0) {
        throw "Terraform validation failed"
    }
    Write-Success "Terraform configuration is valid`n"
} catch {
    Write-Error "Terraform validation failed: $_"
    Pop-Location
    exit 1
}

# Step 7: Plan or Apply
if ($Destroy) {
    Write-Warning "DESTROY MODE: This will delete all infrastructure!"
    $confirm = Read-Host "Type 'yes' to confirm"
    if ($confirm -ne "yes") {
        Write-Info "Destruction cancelled"
        Pop-Location
        exit 0
    }
    
    Write-Info "Destroying infrastructure..."
    terraform destroy -auto-approve
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Terraform destroy failed"
        Pop-Location
        exit 1
    }
    Write-Success "Infrastructure destroyed"
} else {
    if (-not $SkipPlan) {
        Write-Info "Running Terraform plan..."
        terraform plan -out=tfplan
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Terraform plan failed"
            Pop-Location
            exit 1
        }
        
        Write-Info "`nReview the plan above. Proceeding with apply...`n"
        Start-Sleep -Seconds 2
    }
    
    Write-Info "Applying Terraform configuration..."
    if (Test-Path "tfplan") {
        terraform apply tfplan
        Remove-Item tfplan -ErrorAction SilentlyContinue
    } else {
        terraform apply -auto-approve
    }
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Terraform apply failed"
        Pop-Location
        exit 1
    }
    
    Write-Success "`nInfrastructure deployed successfully!`n"
    
    # Step 8: Display outputs
    Write-Info "Infrastructure Outputs:"
    Write-Info "=========================="
    terraform output
    
    # Save outputs to file
    $outputFile = Join-Path $PSScriptRoot "terraform-outputs.json"
    terraform output -json | Out-File $outputFile -Encoding utf8
    Write-Success "`nOutputs saved to: $outputFile"
}

Pop-Location
Write-Success "`nDeployment script completed!"

