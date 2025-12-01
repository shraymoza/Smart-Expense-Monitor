# Next Steps - Development Roadmap

## Current Status ✅

- ✅ Frontend structure (Login, Signup, Dashboard pages)
- ✅ Terraform infrastructure configuration
- ✅ Automated deployment script
- ✅ User separation architecture (S3 folder structure)
- ✅ Lambda function skeleton
- ✅ API Gateway setup

---

## Phase 1: Deploy Infrastructure (IMMEDIATE NEXT STEP) 🚀

### Step 1.1: Deploy AWS Infrastructure

**Action Required:**
```powershell
cd terraform
.\deploy.ps1
```

**What this does:**
- Creates all AWS resources (Cognito, S3, DynamoDB, Lambda, API Gateway)
- Saves outputs to `terraform-outputs.json`

**After deployment, you'll have:**
- Cognito User Pool ID and Client ID
- S3 Bucket name
- API Gateway URL
- DynamoDB table names

**Time:** ~5-10 minutes

---

## Phase 2: Frontend Integration (HIGH PRIORITY) 🔐

### Step 2.1: Install AWS Amplify SDK

```bash
cd frontend
npm install aws-amplify @aws-amplify/ui-react
```

### Step 2.2: Configure Cognito Authentication

**Create:** `frontend/src/config/aws-config.js`
- Load Cognito credentials from `terraform-outputs.json`
- Configure Amplify with User Pool ID and Client ID

**Update:**
- `frontend/src/App.js` - Add Amplify configuration
- `frontend/src/pages/Login.js` - Implement real Cognito sign-in
- `frontend/src/pages/Signup.js` - Implement real Cognito sign-up
- `frontend/src/pages/Dashboard.js` - Add authentication check

**Features to add:**
- ✅ Real user authentication
- ✅ Protected routes (redirect to login if not authenticated)
- ✅ Get current user info
- ✅ Logout functionality

**Time:** ~2-3 hours

---

## Phase 3: Receipt Upload Functionality (HIGH PRIORITY) 📤

### Step 3.1: Create Upload Component

**Create:** `frontend/src/components/ReceiptUpload.js`
- File input for image/PDF selection
- Preview of selected file
- Upload progress indicator
- Error handling

### Step 3.2: Implement S3 Presigned URL Upload

**Create:** `frontend/src/services/api.js`
- Function to get presigned URL from API Gateway
- Function to upload file to S3 using presigned URL
- Upload to path: `users/{cognitoUserId}/uploads/{receiptId}.{ext}`

**Update:**
- `frontend/src/pages/Dashboard.js` - Add upload functionality
- Connect to API Gateway endpoint

**Features:**
- ✅ File selection (jpg, png, pdf)
- ✅ Upload to S3 with user-specific path
- ✅ Trigger Lambda processing
- ✅ Success/error notifications

**Time:** ~3-4 hours

---

## Phase 4: API Integration (MEDIUM PRIORITY) 🔌

### Step 4.1: Create API Service Layer

**Create:** `frontend/src/services/api.js`
- Configure API Gateway base URL
- Add Cognito authentication headers
- Create functions for:
  - `getExpenses()` - Fetch user expenses
  - `getReceipts()` - Fetch receipt metadata
  - `getPresignedUploadUrl()` - Get S3 upload URL

### Step 4.2: Update Lambda Function

**Enhance:** `backend/lambda_functions/receipt_processor.py`
- Implement presigned URL generation endpoint
- Improve receipt parsing logic
- Extract store name, date, amount from receipts
- Add expense categorization

**Time:** ~4-5 hours

---

## Phase 5: Expense Display & Reports (MEDIUM PRIORITY) 📊

### Step 5.1: Create Expense List Component

**Create:** `frontend/src/components/ExpenseList.js`
- Display expenses in a table/list
- Filter by date range
- Filter by category
- Sort by amount/date

### Step 5.2: Create Monthly Report Component

**Create:** `frontend/src/components/MonthlyReport.js`
- Calculate monthly totals
- Group by category
- Visual charts (using a charting library)
- Export to PDF/CSV

**Update:**
- `frontend/src/pages/Dashboard.js` - Add expense history and report sections

**Time:** ~4-6 hours

---

## Phase 6: Enhanced Features (LOW PRIORITY) ⭐

### Step 6.1: Receipt OCR Enhancement
- Improve Textract integration
- Better parsing of receipt data
- Extract line items

### Step 6.2: Expense Categorization
- Auto-categorize expenses (Food, Transport, Shopping, etc.)
- ML-based categorization
- Manual category override

### Step 6.3: Notifications
- Email monthly reports
- Expense alerts
- Budget tracking

**Time:** ~6-8 hours

---

## Phase 7: Deployment (FINAL STEP) 🚀

### Step 7.1: Deploy Frontend to AWS Amplify

**Actions:**
1. Connect GitHub repository to AWS Amplify
2. Configure build settings
3. Set environment variables (Cognito IDs, API Gateway URL)
4. Deploy

**Or use CLI:**
```bash
cd frontend
amplify init
amplify add hosting
amplify publish
```

**Time:** ~1 hour

---

## Recommended Order of Implementation

1. **Deploy Infrastructure** (Phase 1) - Do this first!
2. **Cognito Integration** (Phase 2) - Essential for security
3. **Receipt Upload** (Phase 3) - Core functionality
4. **API Integration** (Phase 4) - Connect everything
5. **Expense Display** (Phase 5) - User value
6. **Enhanced Features** (Phase 6) - Nice to have
7. **Production Deployment** (Phase 7) - Final step

---

## Quick Start Checklist

- [ ] Deploy Terraform infrastructure (`.\deploy.ps1`)
- [ ] Save `terraform-outputs.json` values
- [ ] Install AWS Amplify SDK in frontend
- [ ] Configure Cognito in React app
- [ ] Implement real login/signup
- [ ] Create receipt upload component
- [ ] Connect to API Gateway
- [ ] Test end-to-end flow
- [ ] Deploy frontend to Amplify

---

## Testing Strategy

After each phase:
1. **Unit Tests**: Test individual components
2. **Integration Tests**: Test API connections
3. **Manual Testing**: Test user flows
4. **CloudWatch**: Monitor Lambda logs
5. **DynamoDB**: Verify data storage

---

## Estimated Total Time

- **Phase 1**: 10 minutes
- **Phase 2**: 2-3 hours
- **Phase 3**: 3-4 hours
- **Phase 4**: 4-5 hours
- **Phase 5**: 4-6 hours
- **Phase 6**: 6-8 hours (optional)
- **Phase 7**: 1 hour

**Total MVP Time**: ~14-19 hours
**With Enhancements**: ~20-27 hours

---

## Need Help?

- Check `terraform/README.md` for infrastructure details
- Check `terraform/DEPLOYMENT.md` for deployment guide
- Check `terraform/s3-user-separation.md` for S3 structure
- Review AWS Amplify documentation for frontend integration

