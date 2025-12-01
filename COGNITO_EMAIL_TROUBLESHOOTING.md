# Cognito Email Verification Troubleshooting

## Issue: Not Receiving Verification Email

### Possible Causes

1. **Cognito Sandbox Limitations**
   - Cognito's default email service has limitations
   - Daily sending limit (usually 50 emails/day in sandbox)
   - Emails might go to spam folder
   - Some email providers block Cognito emails

2. **Email Configuration**
   - Currently using `COGNITO_DEFAULT` which has restrictions
   - Need to configure AWS SES for production use

### Quick Checks

1. **Check Spam Folder**
   - Verification emails often go to spam
   - Check your spam/junk folder

2. **Check Browser Console**
   - Open browser DevTools (F12)
   - Check Console tab for any errors
   - Look for "Signup result:" log message

3. **Check AWS Cognito Console**
   - Go to AWS Console > Cognito
   - Find your User Pool: `smart-expense-monitor-dev-user-pool`
   - Go to "Users" tab
   - Check if your user was created
   - Check user status (should be "Unconfirmed")

### Solutions

#### Option 1: Use AWS SES (Recommended for Production)

1. **Verify Your Email Domain in SES**
   ```bash
   # In AWS Console > SES
   # Verify your email address or domain
   ```

2. **Update Terraform Configuration**
   Add to `terraform/cognito.tf`:
   ```hcl
   email_configuration {
     email_sending_account = "DEVELOPER"
     from_email_address   = "noreply@yourdomain.com"
     source_arn           = "arn:aws:ses:us-east-1:YOUR_ACCOUNT:identity/yourdomain.com"
   }
   ```

3. **Redeploy**
   ```powershell
   cd terraform
   .\deploy.ps1
   ```

#### Option 2: Temporarily Disable Email Verification (Development Only)

**⚠️ WARNING: Only for development/testing!**

1. **Update Cognito User Pool**
   - Go to AWS Console > Cognito
   - Select your User Pool
   - Go to "Sign-in experience" > "User attributes"
   - Under "Email", uncheck "Required"
   - Or change verification to "No verification"

2. **Update Terraform** (if you want to manage it)
   ```hcl
   # In cognito.tf, you can't easily disable verification
   # Better to do it manually in console for testing
   ```

#### Option 3: Check Cognito Email Settings

1. **Verify Email Configuration**
   - AWS Console > Cognito > Your User Pool
   - Go to "Messaging" tab
   - Check email configuration
   - Verify it's set to "Cognito default"

2. **Check Email Limits**
   - Cognito sandbox has daily limits
   - Check if you've exceeded the limit
   - Wait 24 hours or move to SES

### Testing the Signup Flow

1. **Check Console Logs**
   - Open browser DevTools (F12)
   - Go to Console tab
   - Try signing up
   - Look for:
     - "Signup result:" - shows what happened
     - Any error messages

2. **Check User in Cognito**
   - AWS Console > Cognito > Users
   - Find your email
   - Check status:
     - "Unconfirmed" = waiting for verification
     - "Confirmed" = already verified
     - "Archived" = deleted

3. **Resend Verification Code**
   - If user exists but unconfirmed
   - You can resend code from Cognito console
   - Or add a "Resend Code" button in the app

### Adding Resend Code Functionality

I can add a "Resend verification code" button to the signup page. This would:
- Call Cognito API to resend the code
- Show a success message
- Help if email was missed

Would you like me to add this feature?

### Current Configuration

- **Email Service:** COGNITO_DEFAULT (sandbox mode)
- **Verification Method:** Code
- **Email Required:** Yes
- **Daily Limit:** ~50 emails (Cognito sandbox)

### Next Steps

1. **Check spam folder first**
2. **Check browser console for errors**
3. **Check Cognito console for user status**
4. **Consider setting up AWS SES for production**

Let me know what you find in the console logs and I can help debug further!

