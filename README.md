# Smart Expense Monitor

A serverless expense tracking application that allows users to upload daily receipts from various stores and generate monthly expense reports.

## Project Structure

```
Smart-Expense-Monitor/
├── frontend/              # React frontend application
│   ├── public/
│   ├── src/
│   │   ├── pages/        # Page components (Login, Signup, Dashboard)
│   │   ├── App.js
│   │   └── index.js
│   └── package.json
├── terraform/            # Infrastructure as Code
│   ├── deploy.ps1        # Automated deployment script
│   ├── aws-credentials.json.example
│   └── *.tf              # Terraform configuration files
├── backend/              # AWS Lambda functions
│   └── lambda_functions/
│       └── receipt_processor.py
└── .gitignore
```

## Features

- User authentication (AWS Cognito)
- Receipt upload with user-specific storage
- Monthly expense reports
- Expense history tracking
- Modern, responsive UI
- Serverless architecture

## User Data Separation

✅ **Each user's receipts are stored separately in S3:**
- Structure: `users/{userId}/uploads/{receiptId}.{ext}`
- User ID is extracted from the S3 key path
- DynamoDB records are tagged with userId
- API queries filter by userId automatically
- Complete isolation between users

**S3 Bucket Name**: `smart-expense-monitor-receipts`

## Getting Started

### Prerequisites

- Node.js (v14 or higher)
- npm or yarn
- Terraform (>= 1.0)
- PowerShell (for deployment script)
- AWS Account with credentials

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

The application will open at `http://localhost:3000`

### Infrastructure Deployment

1. **Setup AWS Credentials** (one-time):
   ```powershell
   cd terraform
   Copy-Item aws-credentials.json.example aws-credentials.json
   ```
   Edit `aws-credentials.json` and add your AWS credentials.

2. **Deploy Infrastructure**:
   ```powershell
   .\deploy.ps1
   ```

The script automatically:
- Creates Lambda zip file
- Sets up terraform.tfvars
- Deploys all AWS resources
- Saves outputs to `terraform-outputs.json`

## Current Implementation

### Frontend Pages

- **Login Page** (`/login`): User sign-in form
- **Signup Page** (`/signup`): User registration form
- **Dashboard** (`/dashboard`): Main application dashboard

**Note**: Currently, login and signup pages navigate directly to the dashboard. AWS Cognito authentication will be integrated next.

### Infrastructure Components

- **AWS Cognito**: User authentication
- **S3 Bucket**: Receipt storage (user-separated folders)
- **DynamoDB**: Expense and receipt metadata
- **Lambda**: Receipt processing with Textract OCR
- **API Gateway**: REST API endpoints
- **IAM**: Security roles and policies

## S3 User Separation

Receipts are stored with complete user isolation:

```
smart-expense-monitor-receipts/
├── users/
│   ├── {userId1}/uploads/receipt1.jpg
│   ├── {userId2}/uploads/receipt1.pdf
│   └── {userId3}/uploads/receipt1.png
```

- Each user has their own folder
- Lambda extracts userId from S3 key path
- DynamoDB queries automatically filter by userId
- No cross-user access possible

## Technologies

- **Frontend**: React, React Router
- **Infrastructure**: Terraform
- **Cloud Services**: 
  - AWS Amplify (frontend hosting)
  - AWS Cognito (authentication)
  - AWS S3 (receipt storage)
  - AWS Lambda (serverless functions)
  - AWS DynamoDB (data storage)
  - AWS Textract (OCR)
  - AWS API Gateway (REST API)

## Security

- ✅ User data isolation in S3
- ✅ Cognito authentication
- ✅ IAM role-based access control
- ✅ Encrypted S3 storage
- ✅ Private S3 bucket (no public access)
- ✅ API Gateway with Cognito authorizer

## Next Steps

- [ ] Integrate Cognito authentication in frontend
- [ ] Implement receipt upload functionality
- [ ] Add expense categorization
- [ ] Create monthly report generation
- [ ] Deploy frontend to AWS Amplify
