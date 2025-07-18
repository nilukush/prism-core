# Login Issue Fix Guide

## Problem Summary
The user successfully registered but login is failing. The backend registration worked (tables created, user stored) but the login request appears to not be reaching the backend or there's a frontend authentication issue.

## Identified Issues

### 1. Backend Health Check Error
The backend health endpoint returns an internal server error:
```bash
curl -s http://localhost:8100/api/v1/health | jq
# Returns: {"error": "internal_server_error", "message": "An unexpected error occurred"}
```

### 2. Potential Issues Found

1. **NextAuth Configuration**: The auth flow expects OAuth2 password grant type format
2. **CORS Configuration**: Properly configured for localhost:3100
3. **API Client**: Correctly formats login requests as form-urlencoded
4. **Auth Routes**: Properly included in the main router

## Fix Steps

### Step 1: Check Backend Status
First, ensure the backend is running properly:

```bash
# Check if backend is running
ps aux | grep uvicorn

# If not running, start it:
cd /Users/nileshkumar/gh/prism/prism-core/backend
python -m uvicorn src.main:app --host 0.0.0.0 --port 8100 --reload
```

### Step 2: Test Backend Directly
Run the debug script in your browser console:

```javascript
// 1. Open http://localhost:3100/auth/login in your browser
// 2. Open Developer Tools (F12)
// 3. Go to Console tab
// 4. Copy and paste this script:

async function testLogin() {
  console.log('Testing backend connectivity...');
  
  // Test health endpoint
  try {
    const health = await fetch('http://localhost:8100/health');
    console.log('Health check:', await health.json());
  } catch (e) {
    console.error('Backend not reachable:', e);
    return;
  }
  
  // Test direct login
  const formData = new URLSearchParams();
  formData.append('username', 'nilukush@gmail.com');
  formData.append('password', 'YOUR_PASSWORD'); // Replace with your actual password
  formData.append('grant_type', 'password');
  
  try {
    const response = await fetch('http://localhost:8100/api/v1/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData.toString(),
    });
    
    const data = await response.json();
    console.log('Login response:', { status: response.status, data });
    
    if (data.access_token) {
      console.log('✅ Backend login successful!');
      
      // Test token validity
      const meResponse = await fetch('http://localhost:8100/api/v1/auth/me', {
        headers: {
          'Authorization': `Bearer ${data.access_token}`
        }
      });
      console.log('User data:', await meResponse.json());
    }
  } catch (e) {
    console.error('Login error:', e);
  }
}

// Run the test
testLogin();
```

### Step 3: Use Enhanced Login Page (Temporary)
I've created an enhanced login page with debugging information. To use it:

```bash
# Backup current login page
cp src/app/auth/login/page.tsx src/app/auth/login/page.tsx.backup

# Use the enhanced version
cp src/app/auth/login/login-fix.tsx src/app/auth/login/page.tsx
```

This enhanced page will show debug information when login fails.

### Step 4: Check Backend Logs
If the backend is having issues, check the logs:

```bash
# If using Docker:
docker logs prism-backend

# If running directly, check the terminal where uvicorn is running
```

### Step 5: Common Fixes

#### Fix 1: Backend Database Connection
If the health check is failing due to database issues:

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# If not, start it:
docker-compose up -d postgres

# Or run PostgreSQL locally:
brew services start postgresql@15
```

#### Fix 2: Environment Variables
Ensure the backend has correct environment variables:

```bash
cd /Users/nileshkumar/gh/prism/prism-core/backend
cat .env | grep -E "DATABASE_URL|SECRET_KEY"
```

#### Fix 3: Clear Browser Storage
Sometimes old session data causes issues:

```javascript
// Run in browser console
localStorage.clear();
sessionStorage.clear();
document.cookie.split(";").forEach(c => {
  document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
});
location.reload();
```

### Step 6: Manual Testing Flow

1. **Test Backend Health**:
   ```bash
   curl http://localhost:8100/health
   ```

2. **Test Backend Auth Endpoint**:
   ```bash
   curl -X POST http://localhost:8100/api/v1/auth/login \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=nilukush@gmail.com&password=YOUR_PASSWORD&grant_type=password"
   ```

3. **Test Frontend Session**:
   ```bash
   curl http://localhost:3100/api/auth/session \
     -H "Cookie: YOUR_SESSION_COOKIE"
   ```

## Quick Fix Script

Run this script to attempt an automatic fix:

```bash
#!/bin/bash
# Save as fix-login.sh and run with: bash fix-login.sh

echo "🔧 Attempting to fix login issues..."

# 1. Check backend
if ! curl -s http://localhost:8100/health > /dev/null 2>&1; then
    echo "❌ Backend not running. Starting..."
    cd /Users/nileshkumar/gh/prism/prism-core/backend
    python -m uvicorn src.main:app --host 0.0.0.0 --port 8100 --reload &
    sleep 5
fi

# 2. Test backend health
echo "🏥 Testing backend health..."
curl -s http://localhost:8100/health | jq

# 3. Clear frontend cache
echo "🧹 Clearing frontend cache..."
cd /Users/nileshkumar/gh/prism/prism-core/frontend
rm -rf .next/cache

echo "✅ Fix attempt complete. Try logging in again."
```

## Root Cause Analysis

The most likely causes are:
1. **Backend not running or crashed** - The health endpoint error suggests this
2. **Database connection issues** - Backend might not be able to connect to PostgreSQL
3. **Environment configuration mismatch** - Frontend and backend might have different configurations

## Next Steps

1. Run the debug script in the browser console
2. Check which step fails
3. Apply the appropriate fix from above
4. If issues persist, check the enhanced login page debug output

The enhanced login page will show exactly where the login process fails, making it easier to identify the root cause.