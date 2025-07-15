# Authentication Error Debug Guide

## Error: ApiError: HTTP error! status: 401 - "Incorrect username or password"

This guide provides enterprise-grade debugging approaches and solutions for the NextAuth OAuth2 password flow authentication error.

## Table of Contents
1. [Understanding the Error](#understanding-the-error)
2. [Common Causes](#common-causes)
3. [Debugging Steps](#debugging-steps)
4. [Solutions](#solutions)
5. [Best Practices](#best-practices)

## Understanding the Error

The error occurs during the OAuth2 password flow authentication callback in NextAuth. The flow is:

1. User submits credentials (email/password) via login form
2. NextAuth's credentials provider sends request to backend `/api/v1/auth/login`
3. Backend expects OAuth2 password grant format (form data, not JSON)
4. Backend returns 401 if authentication fails

## Common Causes

### 1. **Password Encoding Issues**
- Frontend sends password as plain text in form data
- Backend may expect different encoding
- Special characters in passwords may be incorrectly encoded

### 2. **OAuth2 Form Data Format**
The backend expects OAuth2 standard format:
```
username=user@example.com&password=pass123&grant_type=password
```

Common mistakes:
- Sending JSON instead of form data
- Using `email` field instead of `username`
- Missing `grant_type=password`

### 3. **CORS and Credentials**
- Missing `credentials: 'include'` in fetch requests
- CORS not properly configured on backend
- Cookies not being sent/received

### 4. **Environment Configuration**
- Incorrect `NEXT_PUBLIC_API_URL`
- Missing or incorrect `NEXTAUTH_SECRET`
- Mismatched URLs between frontend and backend

### 5. **Backend Issues**
- User doesn't exist in database
- Password hashing mismatch
- Backend auth service not running
- Database connection issues

## Debugging Steps

### Step 1: Test Backend Directly

```bash
# Test OAuth2 password flow directly
curl -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=testpassword&grant_type=password"
```

Expected response:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Step 2: Use Debug Endpoint

1. Start your Next.js app
2. Make a POST request to `/api/debug-auth`:

```bash
curl -X POST http://localhost:3100/api/debug-auth \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpassword"}'
```

This will run comprehensive tests and provide recommendations.

### Step 3: Run Test Script

```bash
cd frontend
npm run tsx scripts/test-auth.ts
```

This script tests:
- Direct backend authentication
- User info retrieval
- NextAuth provider
- Full sign-in flow

### Step 4: Check Browser DevTools

1. Open Network tab
2. Attempt login
3. Check the `/api/auth/callback/credentials` request:
   - Request payload format
   - Response status and body
   - Set-Cookie headers

### Step 5: Enable NextAuth Debug Mode

In `.env.local`:
```env
NODE_ENV=development
```

In `auth.ts`:
```typescript
export const authOptions: NextAuthOptions = {
  // ...
  debug: true,
}
```

Check server console for detailed logs.

## Solutions

### Solution 1: Fix Form Data Encoding

In `api-client.ts`, the login method is correctly implemented:

```typescript
login: (data: { email: string; password: string }) => {
  const formData = new URLSearchParams();
  formData.append('username', data.email); // Note: 'username', not 'email'
  formData.append('password', data.password);
  formData.append('grant_type', 'password');
  
  return apiClient.request<...>('/api/v1/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData.toString(),
  });
}
```

### Solution 2: Handle Special Characters

If passwords contain special characters:

```typescript
// Ensure proper encoding
formData.append('password', encodeURIComponent(data.password));
```

### Solution 3: Fix CORS Issues

Backend should allow credentials:
```python
# FastAPI example
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3100"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Solution 4: Verify User Credentials

1. Check if user exists in database
2. Verify password hashing algorithm matches
3. Test with a known good user/password

### Solution 5: Environment Variables

Ensure `.env.local` has:
```env
NEXT_PUBLIC_API_URL=http://localhost:8100
NEXTAUTH_URL=http://localhost:3100
NEXTAUTH_SECRET=your-secret-key-here
```

### Solution 6: Clear Browser Data

Sometimes stale cookies/sessions cause issues:
```javascript
// Clear all auth cookies
document.cookie.split(";").forEach(c => {
  document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
});
```

## Best Practices

### 1. **Consistent Error Handling**

```typescript
async authorize(credentials) {
  try {
    const response = await api.auth.login({
      email: credentials.email,
      password: credentials.password,
    });
    
    // Always validate response structure
    if (!response?.access_token) {
      console.error('Invalid response structure:', response);
      return null;
    }
    
    // Fetch user data with proper error handling
    const userResponse = await fetch(`${getApiUrl()}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${response.access_token}` },
    });
    
    if (!userResponse.ok) {
      console.error('Failed to fetch user data:', userResponse.status);
      return null;
    }
    
    const userData = await userResponse.json();
    return {
      id: userData.id,
      email: userData.email,
      name: userData.full_name || userData.email,
      accessToken: response.access_token,
      refreshToken: response.refresh_token,
    };
  } catch (error) {
    console.error('Authorization error:', error);
    return null;
  }
}
```

### 2. **Logging Strategy**

Add structured logging:
```typescript
const logger = {
  auth: (action: string, data: any) => {
    console.log(`[AUTH:${action}]`, {
      timestamp: new Date().toISOString(),
      ...data
    });
  }
};

// Usage
logger.auth('LOGIN_ATTEMPT', { email: credentials.email });
logger.auth('LOGIN_SUCCESS', { userId: userData.id });
logger.auth('LOGIN_FAILURE', { error: error.message });
```

### 3. **Security Considerations**

1. Never log passwords or tokens in production
2. Use HTTPS in production
3. Implement rate limiting
4. Add CSRF protection
5. Validate and sanitize all inputs

### 4. **Testing Strategy**

Create E2E tests:
```typescript
// cypress/e2e/auth.cy.ts
describe('Authentication', () => {
  it('should login with valid credentials', () => {
    cy.visit('/auth/login');
    cy.get('input[name="email"]').type('test@example.com');
    cy.get('input[name="password"]').type('testpassword');
    cy.get('button[type="submit"]').click();
    cy.url().should('include', '/dashboard');
  });
});
```

## Monitoring and Observability

### 1. **Add Authentication Metrics**

```typescript
// Track authentication attempts
const authMetrics = {
  attempts: 0,
  successes: 0,
  failures: 0,
  errors: 0,
};

// In authorize function
authMetrics.attempts++;
if (result) authMetrics.successes++;
else authMetrics.failures++;
```

### 2. **Error Tracking**

Use Sentry or similar:
```typescript
import * as Sentry from "@sentry/nextjs";

try {
  // auth logic
} catch (error) {
  Sentry.captureException(error, {
    tags: {
      component: 'auth',
      action: 'login',
    },
    extra: {
      email: credentials.email,
      // Never log passwords!
    },
  });
}
```

## Quick Checklist

- [ ] Backend is running and accessible
- [ ] API URL is correct in environment variables
- [ ] NEXTAUTH_SECRET is set
- [ ] User exists in database with correct password
- [ ] OAuth2 form data format is correct
- [ ] CORS is properly configured
- [ ] No stale cookies/sessions
- [ ] Network requests show correct payload format
- [ ] Backend logs show authentication attempts
- [ ] NextAuth debug mode shows detailed errors

## Additional Resources

1. [NextAuth.js Documentation](https://next-auth.js.org/)
2. [OAuth 2.0 Password Grant](https://oauth.net/2/grant-types/password/)
3. [FastAPI OAuth2 Guide](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)
4. [JWT Debugging](https://jwt.io/)

## Support

If issues persist after following this guide:

1. Check backend logs for specific error messages
2. Use the debug endpoint to get detailed diagnostics
3. Review the test script output for failed tests
4. Check for any recent changes to authentication logic
5. Verify database user records and password hashes