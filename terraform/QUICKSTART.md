# Quick Start Guide

## One-Time Setup

### 1. Configure AWS Credentials

```powershell
cd terraform
Copy-Item aws-credentials.json.example aws-credentials.json
```

Open `aws-credentials.json` and add your credentials:
```json
{
  "access_key_id": "YOUR_ACTUAL_ACCESS_KEY",
  "secret_access_key": "YOUR_ACTUAL_SECRET_KEY",
  "region": "us-east-1"
}
```

**✅ This file is gitignored and won't be committed.**

## Deploy

Simply run:

```powershell
.\deploy.ps1
```

The script will:
- ✅ Load your AWS credentials
- ✅ Create Lambda zip automatically
- ✅ Setup terraform.tfvars if needed
- ✅ Initialize Terraform
- ✅ Deploy everything
- ✅ Save outputs to `terraform-outputs.json`

## That's It!

Your infrastructure is now deployed. Check `terraform-outputs.json` for:
- Cognito User Pool ID (for frontend)
- API Gateway URL (for API calls)
- S3 Bucket Name (for uploads)

## Next Deployments

Just run `.\deploy.ps1` again - no need to reconfigure anything!

## Destroy Infrastructure

```powershell
.\deploy.ps1 -Destroy
```

