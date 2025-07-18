# 🚀 Production User Activation Guide

## Current Production Setup
- **Frontend**: Vercel (https://prism-frontend-kappa.vercel.app)
- **Backend**: Render (https://prism-backend-bwfx.onrender.com)
- **Database**: Neon PostgreSQL
- **Cache**: Upstash Redis
- **Environment**: PRODUCTION (not development!)

## The Email Verification Problem

In production, users cannot login because:
1. Registration creates users with `status = 'pending'`
2. Email verification fails (no SMTP configured)
3. Login requires `status = 'active'`

## Solutions (In Order of Preference)

### 1. Auto-Activation on Login (Recommended)

Add to Render environment variables:
```
AUTO_ACTIVATE_USERS=true
```

This will automatically activate pending users when they attempt to login.

### 2. Simple Activation Endpoint

Activate any user immediately:
```bash
curl -X POST https://prism-backend-bwfx.onrender.com/api/v1/activation/simple/user@email.com
```

This endpoint:
- Works in production without authentication
- Updates user status to 'active'
- Sets email_verified = true
- Returns success/error message

### 3. Direct Database Update (Emergency)

If endpoints fail, use Neon dashboard:
```sql
UPDATE users 
SET status = 'active',
    email_verified = true,
    email_verified_at = NOW(),
    is_active = true
WHERE email = 'user@email.com';
```

## Testing the Solution

1. **Check current deployment**:
```bash
curl -I https://prism-backend-bwfx.onrender.com/api/health
```

2. **Try simple activation**:
```bash
curl -X POST https://prism-backend-bwfx.onrender.com/api/v1/activation/simple/nilukush@gmail.com
```

3. **Login after activation**:
Go to https://prism-frontend-kappa.vercel.app/auth/login

## Why NOT to Use ENVIRONMENT=development

Setting `ENVIRONMENT=development` in production:
- ❌ Disables security features
- ❌ Enables debug endpoints
- ❌ Shows detailed error messages
- ❌ Reduces performance optimizations
- ❌ May expose sensitive data

Instead, use targeted solutions like `AUTO_ACTIVATE_USERS=true`.

## Long-term Solution

1. **Set up SMTP** (SendGrid, AWS SES, Resend)
2. **Configure email templates**
3. **Enable proper email verification flow**
4. **Remove activation workarounds**

## For New Users

When new users register:
1. They'll be created with pending status
2. Use the simple activation endpoint to activate them
3. Or enable AUTO_ACTIVATE_USERS for automatic activation

## Security Note

The simple activation endpoint is a temporary solution. For production:
1. Add authentication to activation endpoints
2. Implement proper email verification
3. Add rate limiting to prevent abuse
4. Log all manual activations for audit