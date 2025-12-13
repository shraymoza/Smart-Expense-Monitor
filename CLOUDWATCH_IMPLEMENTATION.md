# CloudWatch Metrics and Alarms Implementation

## ✅ Implementation Complete

### 1. CloudWatch Metrics (Custom Metrics)

**Namespace:** `SmartExpenseMonitor`

#### Metrics Published:

1. **ExpensesProcessed** (Count)
   - Published when: An expense is saved
   - Location: `receipt_processor.py` → `save_expense()`
   - Purpose: Track total number of expenses processed

2. **TotalExpenseAmount** (None)
   - Published when: An expense is saved
   - Location: `receipt_processor.py` → `save_expense()`
   - Purpose: Track total dollar amount of all expenses

3. **ExpenseByCategory** (None)
   - Published when: An expense is saved
   - Location: `receipt_processor.py` → `save_expense()`
   - Dimensions: `Category` (e.g., "Groceries", "Food & Drink")
   - Purpose: Track spending by category

4. **MonthlySpending** (None)
   - Published when: 
     - An expense is saved (`receipt_processor.py`)
     - Monthly check is performed (`expense_notifier.py`)
   - Dimensions: `Month` (YYYY-MM), `UserId`
   - Purpose: Track monthly spending per user

5. **TextractProcessingTime** (Milliseconds)
   - Published when: Textract completes processing a receipt
   - Location: `receipt_processor.py` → `extract_text_from_receipt()`
   - Purpose: Monitor OCR processing performance

6. **ThresholdExceeded** (Count)
   - Published when: User's monthly spending exceeds threshold
   - Location: `expense_notifier.py` → `check_and_notify_user()`
   - Dimensions: `Month`, `UserId`
   - Purpose: Track how many users exceeded their thresholds

### 2. CloudWatch Alarms

#### Standard Lambda Alarms:

1. **Lambda Errors Alarm**
   - Metric: `AWS/Lambda Errors`
   - Threshold: > 5 errors in 1 minute
   - Function: `receipt_processor`
   - Purpose: Alert when ProcessReceipt Lambda has too many errors

2. **Lambda Duration Alarm**
   - Metric: `AWS/Lambda Duration`
   - Threshold: Average > 25 seconds (over 5 minutes)
   - Function: `receipt_processor`
   - Purpose: Alert when Lambda execution is taking too long

3. **Lambda Throttles Alarm**
   - Metric: `AWS/Lambda Throttles`
   - Threshold: > 1 throttle in 5 minutes
   - Function: `receipt_processor`
   - Purpose: Alert when Lambda is being throttled

#### Custom Metric Alarms:

4. **Threshold Exceeded Alarm**
   - Metric: `SmartExpenseMonitor ThresholdExceeded`
   - Threshold: > 0 (any user exceeds threshold)
   - Period: 1 hour
   - Purpose: Alert when any user exceeds their monthly spending threshold

### 3. CloudWatch Dashboard

**Dashboard Name:** `smart-expense-monitor-dev-dashboard`

**Widgets:**
1. **Lambda Function Metrics**
   - Invocations, Errors, Duration

2. **DynamoDB Metrics**
   - Read/Write capacity units

3. **Custom Application Metrics**
   - Expenses Processed
   - Total Expense Amount
   - Textract Processing Time

4. **Monthly Spending Metrics**
   - Monthly Spending
   - Threshold Exceeded Count

### 4. AWS Budgets

**Budget Name:** `smart-expense-monitor-dev-monthly-budget`

**Configuration:**
- Budget Type: COST
- Limit: $15.00 USD per month
- Time Unit: MONTHLY

**Notifications:**
1. **80% Threshold** (Actual)
   - Alert when actual spend reaches $12.00 (80% of $15)
   - Notification Type: ACTUAL

2. **100% Threshold** (Actual)
   - Alert when actual spend reaches $15.00
   - Notification Type: ACTUAL

3. **100% Threshold** (Forecasted)
   - Alert if forecasted to exceed $15.00
   - Notification Type: FORECASTED

**Recipient:** SES sender email (configured in `terraform.tfvars`)

## 📊 Metrics Flow

### When Receipt is Processed:
1. Textract extracts text → Publishes `TextractProcessingTime` metric
2. Expense is saved → Publishes:
   - `ExpensesProcessed` (+1)
   - `TotalExpenseAmount` (amount)
   - `ExpenseByCategory` (amount by category)
   - `MonthlySpending` (amount for current month)

### When Monthly Check Runs:
1. For each user, calculates monthly total
2. Publishes `MonthlySpending` metric
3. If threshold exceeded, publishes `ThresholdExceeded` metric

## 🔔 Alarm Actions

Currently, alarms are configured but don't have SNS topics attached. To add email notifications:

1. Create SNS topic
2. Subscribe email to topic
3. Add topic ARN to `alarm_actions` in alarm resources

## 📈 Viewing Metrics

### CloudWatch Console:
1. Go to CloudWatch → Metrics → All metrics
2. Find namespace: `SmartExpenseMonitor`
3. View custom metrics

### Dashboard:
1. Go to CloudWatch → Dashboards
2. Open: `smart-expense-monitor-dev-dashboard`
3. View all metrics in one place

## 🚀 Deployment

After implementing, deploy with:
```powershell
cd terraform
.\deploy.ps1
```

This will:
- Create CloudWatch alarms
- Create CloudWatch dashboard
- Create AWS Budget
- Update Lambda functions with metric publishing code
- Update IAM policies for CloudWatch permissions

## ✅ Alignment with Report

### From Report Section 4.5 (Operations / Monitoring):
- ✅ CloudWatch logs for all Lambdas
- ✅ CloudWatch metrics for monthly spending
- ✅ CloudWatch alarms for multi-user cost thresholds

### From Report Section 4.5 (Cost Optimization):
- ✅ Budget Alerts (if forecasted spend > $15.00)

All monitoring requirements from the report are now implemented!

