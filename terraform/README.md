# Terraform Infrastructure for Smart Expense Monitor

This directory contains Terraform configuration files for deploying the serverless infrastructure on AWS.

## Quick Start

### 1. Setup AWS Credentials

Create `aws-credentials.json` from the example:

```powershell
cd terraform
Copy-Item aws-credentials.json.example aws-credentials.json
```

Edit `aws-credentials.json` and add your AWS credentials:
```json
{
  "access_key_id": "AKIAIOSFODNN7EXAMPLE",
  "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
  "region": "us-east-1"
}
```

**Note**: This file is in `.gitignore` and will not be committed to git.

### 2. Deploy Infrastructure

Run the automated deployment script:

```powershell
.\deploy.ps1
```

That's it! The script will:
- ✅ Load AWS credentials from `aws-credentials.json`
- ✅ Create Lambda zip file automatically
- ✅ Setup `terraform.tfvars` if needed
- ✅ Initialize Terraform
- ✅ Validate configuration
- ✅ Plan and apply changes
- ✅ Save outputs to `terraform-outputs.json`

### 3. Customize (Optional)

Edit `terraform.tfvars` to customize:
- AWS region
- S3 bucket name
- Lambda settings
- Environment name

## Script Options

```powershell
# Skip Lambda zip creation (if already exists)
.\deploy.ps1 -SkipZip

# Skip Terraform plan (apply directly)
.\deploy.ps1 -SkipPlan

# Destroy infrastructure
.\deploy.ps1 -Destroy
```

## Architecture

The infrastructure includes:

- **AWS Cognito**: User authentication and authorization
- **S3 Bucket**: Storage for uploaded receipts
- **DynamoDB**: Tables for expenses and receipt metadata
- **Lambda Functions**: Serverless functions for receipt processing
- **API Gateway**: REST API endpoints
- **IAM Roles & Policies**: Security and permissions
- **CloudWatch**: Logging and monitoring

## Prerequisites

1. **AWS CLI configured** or credentials in `aws-credentials.json`
2. **Terraform installed** (version >= 1.0)
3. **PowerShell** (for deployment script)
4. **AWS Account** with appropriate permissions

## Manual Deployment

If you prefer manual deployment:

```bash
# 1. Create Lambda zip
cd ../backend/lambda_functions
zip receipt_processor.zip receipt_processor.py

# 2. Initialize Terraform
cd ../../terraform
terraform init

# 3. Plan
terraform plan

# 4. Apply
terraform apply
```

## Outputs

After deployment, outputs are saved to `terraform-outputs.json` and include:
- Cognito User Pool ID and Client ID
- S3 Bucket Name
- API Gateway URL
- DynamoDB Table Names
- Lambda Function ARN

## File Structure

```
terraform/
├── versions.tf              # Terraform and provider versions
├── provider.tf              # AWS provider configuration
├── variables.tf             # Input variables
├── outputs.tf               # Output values
├── main.tf                  # Additional resources
├── cognito.tf               # Cognito User Pool setup
├── s3.tf                    # S3 bucket configuration
├── dynamodb.tf              # DynamoDB tables
├── lambda.tf                # Lambda functions
├── api_gateway.tf           # API Gateway setup
├── iam.tf                   # IAM roles and policies
├── terraform.tfvars.example # Example variables file
├── aws-credentials.json.example  # Example credentials file
├── deploy.ps1               # Automated deployment script
├── README.md                # This file
└── DEPLOYMENT.md            # Detailed deployment guide
```

## Important Notes

1. **S3 Bucket Name**: Must be globally unique. If you don't specify one in `terraform.tfvars`, Terraform will auto-generate it.

2. **Lambda Function**: The deployment script automatically creates the zip file from `receipt_processor.py`.

3. **Credentials**: Never commit `aws-credentials.json` or `terraform.tfvars` to git. They are in `.gitignore`.

4. **Costs**: This infrastructure uses:
   - DynamoDB: Pay-per-request (no charges for idle)
   - Lambda: Pay per invocation
   - S3: Pay for storage and requests
   - API Gateway: Pay per API call
   - Textract: Pay per page processed (if enabled)

## Destroying Infrastructure

To remove all resources:

```powershell
.\deploy.ps1 -Destroy
```

**Warning**: This will delete all resources including data in DynamoDB and S3.

## Troubleshooting

### Common Issues

1. **Credentials not found**: Ensure `aws-credentials.json` exists and is properly formatted
2. **Bucket name already exists**: Change the `s3_bucket_name` in `terraform.tfvars`
3. **Lambda function not found**: The script creates it automatically, but ensure `receipt_processor.py` exists
4. **Permission errors**: Ensure your AWS credentials have sufficient permissions

### Required IAM Permissions

Your AWS user/role needs permissions for:
- Cognito (Create/Manage User Pools)
- S3 (Create/Manage Buckets)
- DynamoDB (Create/Manage Tables)
- Lambda (Create/Manage Functions)
- API Gateway (Create/Manage APIs)
- IAM (Create/Manage Roles and Policies)
- CloudWatch (Create Log Groups)
- Textract (if enabled)

## Next Steps

After deploying the infrastructure:

1. **Update Frontend**: Configure React app with Cognito User Pool ID and API Gateway URL from outputs
2. **Test Integration**: Upload receipts and verify the flow
3. **Monitor**: Check CloudWatch logs for Lambda function execution
