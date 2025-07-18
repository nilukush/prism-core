# 🚀 Quick Login Fix - Email Verification Issue

## The Problem
Your account is stuck in "pending" status because:
1. You registered successfully ✅
2. Email verification failed (no email template) ⚠️
3. Login blocked because status != "active" ❌

## Solution 1: Enable DEBUG Mode (Easiest)

The backend already has code to allow pending users in DEBUG mode!

### In Render Dashboard:
1. Go to: https://dashboard.render.com
2. Click your backend service
3. Go to "Environment" tab
4. Add variable: `DEBUG=true`
5. Save and wait for redeploy

Then try logging in again - it should work!

## Solution 2: Direct API Call

I noticed there's a debug endpoint in the code. Try this in your browser console:

```javascript
// First, check your user status
fetch('https://prism-backend-bwfx.onrender.com/api/v1/debug/user-status/nilukush@gmail.com')
  .then(r => r.json())
  .then(data => console.log('User status:', data))
  .catch(err => console.error('Error:', err));

// If the above works, activate your account
fetch('https://prism-backend-bwfx.onrender.com/api/v1/debug/activate-user/nilukush@gmail.com', {
  method: 'POST'
})
  .then(r => r.json())
  .then(data => console.log('Activation result:', data))
  .catch(err => console.error('Error:', err));
```

## Solution 3: Skip Email Verification

Add to Render environment variables:
- `SKIP_EMAIL_VERIFICATION=true`
- `APP_ENV=development`

## Why This Happened

The registration flow expects:
1. User registers → status = "pending"
2. Email sent with verification link
3. User clicks link → status = "active"
4. User can now login

But email failed, so you're stuck at step 2.

## After Fixing

Once you can login, you should:
1. Create an organization
2. Create a project
3. Start using PRISM!

The easiest fix is adding `DEBUG=true` to Render - the code already handles this case!