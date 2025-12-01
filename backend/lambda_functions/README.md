# Lambda Functions

This directory contains the Lambda function code for processing receipts.

## Receipt Processor Function

The `receipt_processor.py` function handles:
- Processing receipts uploaded to S3
- Extracting text using AWS Textract
- Parsing receipt data
- Storing data in DynamoDB
- Handling API Gateway requests

## Building the Lambda Package

To create the deployment package:

```bash
cd backend/lambda_functions

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create deployment package
zip -r receipt_processor.zip receipt_processor.py venv/lib/python*/site-packages/

# Or use a simpler approach (if boto3 is already in Lambda runtime)
zip receipt_processor.zip receipt_processor.py
```

**Note**: The Lambda runtime (Python 3.11) already includes boto3, so you may only need to zip the Python file if you're not using additional dependencies.

## Deployment

After creating `receipt_processor.zip`, place it in this directory. Terraform will reference it when deploying the Lambda function.

## Environment Variables

The Lambda function uses these environment variables (set by Terraform):
- `EXPENSES_TABLE_NAME`: DynamoDB table for expenses
- `RECEIPTS_TABLE_NAME`: DynamoDB table for receipt metadata
- `S3_BUCKET_NAME`: S3 bucket name
- `ENABLE_TEXTRACT`: Enable/disable Textract OCR

## Next Steps

1. Implement proper receipt parsing logic
2. Extract user ID from Cognito tokens
3. Add error handling and retry logic
4. Implement presigned URL generation for S3 uploads
5. Add expense categorization logic

