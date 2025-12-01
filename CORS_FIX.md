# CORS Error Fix

## Issue
- **Error**: "CORS Missing Allow Origin"
- **Error**: "Cross-Origin Request Blocked"
- **Status**: 403 on OPTIONS request to S3

## Cause
S3 bucket doesn't have CORS configuration, which is required for browsers to upload files directly to S3 using presigned URLs.

## Fix Applied
Added CORS configuration to S3 bucket in `terraform/s3.tf`:
- Allows all origins (for development)
- Allows GET, PUT, POST, HEAD methods
- Allows all headers
- Exposes ETag header

## Next Step: Redeploy

You need to redeploy Terraform to apply the CORS configuration:

```powershell
cd terraform
.\deploy.ps1
```

This will:
- Add CORS configuration to S3 bucket
- Allow frontend to upload files directly to S3

## After Redeployment

1. **Test upload again** - Should work now!
2. **Check Network tab** - OPTIONS request should succeed (200 status)
3. **Check upload** - File should upload successfully

## For Production

In production, update the CORS configuration to only allow your frontend domain:

```hcl
allowed_origins = ["https://yourdomain.com", "https://www.yourdomain.com"]
```

Instead of `["*"]` for security.

