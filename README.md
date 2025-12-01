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
├── terraform/            # Infrastructure as Code (to be implemented)
├── backend/              # AWS Lambda functions (to be implemented)
└── .gitignore
```

## Features

- User authentication (Cognito integration pending)
- Receipt upload functionality
- Monthly expense reports
- Expense history tracking
- Modern, responsive UI

## Getting Started

### Prerequisites

- Node.js (v14 or higher)
- npm or yarn

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

## Current Implementation

### Frontend Pages

- **Login Page** (`/login`): User sign-in form
- **Signup Page** (`/signup`): User registration form
- **Dashboard** (`/dashboard`): Main application dashboard

**Note**: Currently, login and signup pages navigate directly to the dashboard. AWS Cognito authentication will be integrated later.

## Future Implementation

- AWS Cognito for authentication
- S3 for receipt storage
- Lambda functions for receipt processing
- DynamoDB for expense data storage
- Textract for receipt OCR
- Terraform for infrastructure deployment
- AWS Amplify for frontend hosting

## Technologies

- **Frontend**: React, React Router
- **Infrastructure**: Terraform (planned)
- **Cloud Services**: AWS (Amplify, Cognito, S3, Lambda, DynamoDB, Textract)

