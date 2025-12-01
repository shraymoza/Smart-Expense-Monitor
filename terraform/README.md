# Terraform Infrastructure for Smart Expense Monitor

This directory contains Terraform configuration files for deploying the serverless infrastructure on AWS.

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

1. **AWS CLI configured** with your access key ID and secret access key
2. **Terraform installed** (version >= 1.0)
3. **AWS Account** with appropriate permissions

## Setup Instructions

### 1. Configure AWS Credentials

Ensure your AWS credentials are configured. You can verify this by running:

```bash
aws configure list
```

Or set environment variables:
```bash
export AWS_ACCESS_KEY_ID="your-access-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
export AWS_DEFAULT_REGION="us-east-1"
```

### 2. Initialize Terraform

```bash
cd terraform
terraform init
```

### 3. Configure Variables

Copy the example variables file and update with your values:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and update:
- `aws_region`: Your preferred AWS region
- `s3_bucket_name`: A globally unique bucket name (or leave empty for auto-generation)
- Other variables as needed

### 4. Review the Plan

```bash
terraform plan
```

This will show you what resources will be created.

### 5. Deploy Infrastructure

```bash
terraform apply
```

Type `yes` when prompted to confirm the deployment.

### 6. Save Outputs

After deployment, Terraform will output important values like:
- Cognito User Pool ID and Client ID
- S3 Bucket Name
- API Gateway URL
- DynamoDB Table Names

Save these outputs as you'll need them for:
- Frontend configuration (Cognito)
- Lambda function environment variables
- API integration

## Outputs

After deployment, you can view outputs with:

```bash
terraform output
```

Or get specific outputs:
```bash
terraform output cognito_user_pool_id
terraform output api_gateway_url
```

## File Structure

```
terraform/
├── versions.tf          # Terraform and provider versions
├── provider.tf          # AWS provider configuration
├── variables.tf         # Input variables
├── outputs.tf          # Output values
├── cognito.tf          # Cognito User Pool setup
├── s3.tf               # S3 bucket configuration
├── dynamodb.tf         # DynamoDB tables
├── lambda.tf           # Lambda functions
├── api_gateway.tf      # API Gateway setup
├── iam.tf              # IAM roles and policies
├── terraform.tfvars.example  # Example variables file
└── README.md           # This file
```

## Important Notes

1. **S3 Bucket Name**: Must be globally unique. If you don't specify one, Terraform will auto-generate it.

2. **Lambda Function**: The Lambda function expects a zip file at `../backend/lambda_functions/receipt_processor.zip`. You'll need to create this before deploying.

3. **Cognito Domain**: The Cognito domain is auto-generated with a random suffix to ensure uniqueness.

4. **Costs**: This infrastructure uses:
   - DynamoDB: Pay-per-request (no charges for idle)
   - Lambda: Pay per invocation
   - S3: Pay for storage and requests
   - API Gateway: Pay per API call
   - Textract: Pay per page processed (if enabled)

## Destroying Infrastructure

To remove all resources:

```bash
terraform destroy
```

**Warning**: This will delete all resources including data in DynamoDB and S3.

## Next Steps

After deploying the infrastructure:

1. **Create Lambda Function Code**: Build the receipt processor Lambda function
2. **Update Frontend**: Configure React app with Cognito User Pool ID and API Gateway URL
3. **Test Integration**: Upload receipts and verify the flow

## Troubleshooting

### Common Issues

1. **Bucket name already exists**: Change the `s3_bucket_name` in `terraform.tfvars`
2. **Lambda function not found**: Create the zip file at the expected path
3. **Permission errors**: Ensure your AWS credentials have sufficient permissions
4. **Cognito domain conflicts**: Terraform will auto-generate a unique domain

### Required IAM Permissions

Your AWS user/role needs permissions for:
- Cognito (Create/Manage User Pools)
- S3 (Create/Manage Buckets)
- DynamoDB (Create/Manage Tables)
- Lambda (Create/Manage Functions)
- API Gateway (Create/Manage APIs)
- IAM (Create/Manage Roles and Policies)
- CloudWatch (Create Log Groups)

