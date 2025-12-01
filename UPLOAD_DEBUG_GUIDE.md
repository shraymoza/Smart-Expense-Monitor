# Upload Error Debugging Guide

## Current Error
- **Error**: `PUT http://localhost:3002/undefined` → 404 Not Found
- **Issue**: Presigned URL is `undefined`

## Debugging Steps

### 1. Check Browser Console
Open DevTools (F12) → Console tab and look for:
- "Requesting presigned URL for:" - Shows what's being sent
- "API Response:" - Shows raw response from API Gateway
- "Presigned URL response received:" - Shows parsed response
- "Current user:" - Shows user object
- "Using userId:" - Shows extracted user ID

### 2. Check Network Tab
- Look for the POST request to `/receipts`
- Check the **Response** tab for that request
- See what the actual response body is

### 3. Possible Issues

#### Issue A: Response Structure Mismatch
The Lambda returns:
```json
{
  "uploadUrl": "https://...",
  "fileName": "...",
  "expiresIn": 300
}
```

But API Gateway with AWS_PROXY might wrap it differently.

**Fix**: Check console logs to see actual response structure.

#### Issue B: User ID Not Extracted
If `user.userId` is undefined, the fileName will be wrong.

**Fix**: Check "Using userId:" in console. Should show a UUID.

#### Issue C: Lambda Not Deployed
If Lambda function doesn't have the latest code, it won't return the right format.

**Fix**: Redeploy Lambda:
```powershell
cd terraform
.\deploy.ps1
```

### 4. Quick Test

Try this in browser console after signing in:
```javascript
// Test getting user
import { getCurrentUser } from 'aws-amplify/auth';
const user = await getCurrentUser();
console.log('User object:', user);
console.log('User ID:', user.userId);
console.log('Username:', user.username);
```

### 5. Test API Directly

Try calling the API directly:
```javascript
// In browser console
const token = (await fetchAuthSession()).tokens.idToken.toString();
const response = await fetch('https://pr53ispmk7.execute-api.us-east-1.amazonaws.com/dev/receipts', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    fileName: 'users/test-user/uploads/test.jpg',
    fileType: 'image/jpeg'
  })
});
const data = await response.json();
console.log('API Response:', data);
```

## Expected Response Format

The Lambda should return:
```json
{
  "uploadUrl": "https://smart-expense-monitor-receipts.s3.amazonaws.com/users/...?X-Amz-Algorithm=...",
  "fileName": "users/{userId}/uploads/{receiptId}.jpg",
  "expiresIn": 300
}
```

## Next Steps

1. **Check console logs** - See what's actually being returned
2. **Check Network tab** - See the actual API response
3. **Redeploy Lambda** - Make sure latest code is deployed
4. **Share console output** - So we can see the actual response structure

The enhanced logging should show exactly what's happening at each step!

