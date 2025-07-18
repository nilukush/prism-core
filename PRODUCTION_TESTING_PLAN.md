# 🧪 PRISM Production User Activation Testing Plan

## Overview
This document provides a comprehensive testing plan to verify that user registration, activation, and login work correctly in production after the SQLAlchemy fix.

## 🎯 Testing Objectives
1. Verify new users can register successfully
2. Confirm activation endpoint works for all users
3. Ensure activated users can login
4. Monitor for any errors or edge cases
5. Validate the fix works across different scenarios

## 📋 Pre-Testing Checklist

### 1. Verify Deployment Status
```bash
# Check if backend is running
curl -I https://prism-backend-bwfx.onrender.com/api/health

# Expected: HTTP/1.1 200 OK
```

### 2. Check Current Database State
Run this in Neon SQL Editor:
```sql
-- Count users by status
SELECT status, COUNT(*) as count 
FROM users 
GROUP BY status;

-- List recent registrations
SELECT id, email, status, email_verified, created_at 
FROM users 
ORDER BY created_at DESC 
LIMIT 10;
```

## 🔄 Testing Workflow

### Step 1: Register New Test User
1. Go to: https://prism-frontend-kappa.vercel.app/auth/register
2. Register with a unique email (e.g., `test-TIMESTAMP@example.com`)
3. Use a strong password (e.g., `Test123!@#`)
4. Note the exact email and password used

### Step 2: Verify Registration in Database
```sql
-- Check if user was created
SELECT id, email, status, email_verified, is_active 
FROM users 
WHERE email = 'your-test-email@example.com';

-- Expected: status = 'pending', email_verified = false
```

### Step 3: Activate User via API
```bash
# Activate the test user
curl -X POST https://prism-backend-bwfx.onrender.com/api/v1/activation/simple/test-email@example.com

# Expected response:
# {"message":"User test-email@example.com activated successfully","status":"active","email_verified":true}
```

### Step 4: Verify Activation in Database
```sql
-- Confirm activation worked
SELECT id, email, status, email_verified, is_active, email_verified_at 
FROM users 
WHERE email = 'your-test-email@example.com';

-- Expected: status = 'active', email_verified = true, is_active = true
```

### Step 5: Test Login
1. Go to: https://prism-frontend-kappa.vercel.app/auth/login
2. Enter the test email and password
3. Click "Sign In"
4. Expected: Successful login and redirect to dashboard

### Step 6: Verify Session
- Check browser DevTools > Application > Cookies
- Look for session cookies (next-auth.session-token)
- Verify you can access protected pages

## 🔍 Advanced Testing Scenarios

### A. Multiple User Test
```bash
# Create test script
cat > test_activation.sh << 'EOF'
#!/bin/bash
BASE_URL="https://prism-backend-bwfx.onrender.com/api/v1/activation/simple"
EMAILS=("test1@example.com" "test2@example.com" "test3@example.com")

for email in "${EMAILS[@]}"; do
    echo "Activating $email..."
    curl -X POST "$BASE_URL/$email"
    echo -e "\n"
done
EOF

chmod +x test_activation.sh
```

### B. Error Handling Test
```bash
# Test non-existent user
curl -X POST https://prism-backend-bwfx.onrender.com/api/v1/activation/simple/nonexistent@example.com

# Expected: {"error":"User not found","email":"nonexistent@example.com"}
```

### C. Already Active User Test
```bash
# Try activating an already active user
curl -X POST https://prism-backend-bwfx.onrender.com/api/v1/activation/simple/already-active@example.com

# Expected: Success message (idempotent operation)
```

## 📊 Monitoring & Metrics

### 1. Backend Logs
Check Render dashboard for:
- HTTP 200 responses for activation endpoint
- No 500 errors or exceptions
- Successful database connections

### 2. Success Metrics
Track in database:
```sql
-- Registration success rate (last 24 hours)
SELECT 
    COUNT(*) as total_users,
    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_users,
    ROUND(100.0 * SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) / COUNT(*), 2) as activation_rate
FROM users 
WHERE created_at > NOW() - INTERVAL '24 hours';

-- Recent activation timestamps
SELECT email, email_verified_at 
FROM users 
WHERE email_verified_at > NOW() - INTERVAL '1 hour'
ORDER BY email_verified_at DESC;
```

### 3. Error Monitoring
```sql
-- Check for any stuck users
SELECT email, status, created_at 
FROM users 
WHERE status = 'pending' 
AND created_at < NOW() - INTERVAL '1 hour';
```

## 🚨 Troubleshooting Guide

### Issue: Activation Returns 500 Error
1. Check Render logs for specific error
2. Verify database connection is active
3. Check SQLAlchemy version compatibility

### Issue: User Not Found Error
1. Verify email exists in database
2. Check for typos in email
3. Ensure user registration completed

### Issue: Login Still Fails After Activation
1. Clear browser cache/cookies
2. Try incognito/private browsing
3. Verify password is correct
4. Check frontend console for errors

## ✅ Testing Checklist

- [ ] Backend health check passes
- [ ] New user registration works
- [ ] Activation endpoint returns success
- [ ] Database shows user as active
- [ ] Login works with activated user
- [ ] Session persists across page refreshes
- [ ] Multiple users can be activated
- [ ] Error cases handled gracefully
- [ ] No 500 errors in logs
- [ ] Performance is acceptable (<2s response)

## 📝 Test Results Template

```markdown
## Test Run: [DATE TIME]

### Environment
- Frontend: https://prism-frontend-kappa.vercel.app
- Backend: https://prism-backend-bwfx.onrender.com
- Tester: [Name]

### Test Cases
1. **New User Registration**
   - Email: test-TIMESTAMP@example.com
   - Result: ✅/❌
   - Notes: 

2. **User Activation**
   - Endpoint: /api/v1/activation/simple/{email}
   - Response Time: X.XX seconds
   - Result: ✅/❌
   - Response: 

3. **Login After Activation**
   - Result: ✅/❌
   - Redirect: 
   - Session Created: Yes/No

### Issues Found
- None / List any issues

### Recommendations
- None / List any improvements
```

## 🎯 Success Criteria

The fix is considered successful when:
1. ✅ 5+ new users can register and be activated
2. ✅ All activated users can login successfully
3. ✅ No SQLAlchemy errors in logs
4. ✅ Response time < 2 seconds for activation
5. ✅ Zero 500 errors during testing
6. ✅ Works for different email formats/domains

## 🔐 Security Considerations

1. **Rate Limiting**: Monitor for abuse of activation endpoint
2. **Audit Trail**: All activations logged with timestamp
3. **Future Enhancement**: Add admin authentication to activation endpoint
4. **Email Validation**: Consider adding email format validation

## 📅 Regular Testing Schedule

- **Daily**: Check activation success rate
- **Weekly**: Full registration flow test
- **Monthly**: Security audit of activation process
- **Quarterly**: Performance testing under load

---

**Last Updated**: 2025-01-18
**Next Review**: After implementing proper email verification