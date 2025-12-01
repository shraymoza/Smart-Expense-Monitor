# Deployment Guide

## Quick Start

### Step 1: Create Lambda Deployment Package

Before deploying Terraform, you need to create the Lambda function zip file:

```bash
# Navigate to lambda functions directory
cd ../backend/lambda_functions

# Create zip file (boto3 is already in Lambda runtime)
zip receipt_processor.zip receipt_processor.py

# Move it to the expected location
mv receipt_processor.zip .
```

### Step 2: Configure Terraform Variables

```bash
cd ../../terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your preferred settings.

### Step 3: Initialize Terraform

```bash
terraform init
```

### Step 4: Review and Deploy

```bash
# Review what will be created
terraform plan

# Deploy infrastructure
terraform apply
```

Type `yes` when prompted.

### Step 5: Save Outputs

After deployment, save the outputs:

```bash
terraform output -json > outputs.json
```

You'll need these values for:
- Frontend configuration (Cognito User Pool ID, Client ID)
- API Gateway URL for API calls
- S3 bucket name for uploads

## Post-Deployment

1. **Update Frontend**: Add Cognito configuration to React app
2. **Test Upload**: Try uploading a receipt via the dashboard
3. **Monitor Logs**: Check CloudWatch logs for Lambda function

## Troubleshooting

### Lambda Function Not Found Error

If you get an error about the Lambda zip file not existing:
1. Create the zip file as shown in Step 1
2. Ensure it's at: `backend/lambda_functions/receipt_processor.zip`
3. Re-run `terraform apply`

### S3 Bucket Name Conflict

If the bucket name is taken:
1. Update `s3_bucket_name` in `terraform.tfvars` with a unique name
2. Re-run `terraform plan` and `terraform apply`

### Permission Errors

Ensure your AWS credentials have permissions for:
- IAM (create roles)
- Lambda (create functions)
- S3 (create buckets)
- DynamoDB (create tables)
- Cognito (create user pools)
- API Gateway (create APIs)
- CloudWatch (create log groups)

