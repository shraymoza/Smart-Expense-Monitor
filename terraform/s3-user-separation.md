# S3 User Separation Architecture

## Bucket Structure

All receipts are stored in a single S3 bucket with the following structure:

```
smart-expense-monitor-receipts/
├── users/
│   ├── {userId1}/
│   │   └── uploads/
│   │       ├── receipt-1.jpg
│   │       ├── receipt-2.pdf
│   │       └── receipt-3.png
│   ├── {userId2}/
│   │   └── uploads/
│   │       ├── receipt-1.jpg
│   │       └── receipt-2.pdf
│   └── {userId3}/
│       └── uploads/
│           └── receipt-1.jpg
```

## User Isolation

### 1. **Folder-Based Separation**
- Each user has their own folder: `users/{userId}/uploads/`
- User ID is extracted from the S3 key path by the Lambda function
- No user can access another user's receipts

### 2. **Lambda Processing**
- Lambda function extracts `userId` from the S3 key: `users/{userId}/uploads/{filename}`
- All DynamoDB records are tagged with the correct `userId`
- Expenses are stored with `userId` as the partition key

### 3. **API Access Control**
- API Gateway uses Cognito User Pool authorizer
- User ID is extracted from the Cognito token (JWT claims)
- Users can only query their own expenses (filtered by `userId`)

### 4. **IAM Policies**
- Lambda has access to all user folders (for processing)
- Users (via Cognito) can only access their own folder through API Gateway
- S3 bucket policy enforces user-specific access

## Security Features

✅ **Complete User Isolation**: Each user's receipts are in a separate folder  
✅ **Cognito Authentication**: Only authenticated users can upload/access receipts  
✅ **IAM Enforcement**: Policies prevent cross-user access  
✅ **Lambda Validation**: Lambda function validates userId from S3 key path  
✅ **DynamoDB Partitioning**: Expenses are partitioned by userId  

## Example S3 Keys

- User `user-123`: `users/user-123/uploads/receipt-abc123.jpg`
- User `user-456`: `users/user-456/uploads/receipt-xyz789.pdf`

## Frontend Upload Path

When uploading from the frontend, the S3 key should be:
```
users/{cognitoUserId}/uploads/{receiptId}.{extension}
```

Where:
- `cognitoUserId` = User's Cognito sub claim or username
- `receiptId` = Unique identifier for the receipt
- `extension` = File extension (jpg, png, pdf, etc.)

