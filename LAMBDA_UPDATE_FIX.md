# Lambda Function Update Fix

## Issue
API is returning: `{"message": "Upload endpoint - to be implemented"}`
This means the Lambda function hasn't been updated with the new presigned URL code.

## Solution

### Step 1: Recreate Zip File (Already Done ✅)
The zip file has been recreated with the latest code.

### Step 2: Force Terraform to Update Lambda

Run the deployment script:

```powershell
cd terraform
.\deploy.ps1
```

This will:
- Detect the new zip file (using `source_code_hash`)
- Update the Lambda function with new code
- Deploy the changes

### Step 3: Verify Update

After deployment, check CloudWatch logs:
1. Go to AWS Console → CloudWatch
2. Find log group: `/aws/lambda/smart-expense-monitor-dev-receipt-processor`
3. Look for recent invocations
4. Check if `upload_receipt` function is being called

### Step 4: Test Again

Try uploading a receipt again. You should now see:
- Console log: "Calling upload_receipt function"
- API Response with `uploadUrl` field
- Successful upload to S3

## What Changed

1. ✅ Updated routing logic to handle API Gateway path format
2. ✅ Added logging to debug path matching
3. ✅ Added `source_code_hash` to force Terraform updates
4. ✅ Recreated zip file with latest code

## If Still Not Working

Check CloudWatch logs for:
- "API Event - Method: POST, Path: /receipts"
- "Calling upload_receipt function"
- Any error messages

Share the CloudWatch log output if issues persist.

