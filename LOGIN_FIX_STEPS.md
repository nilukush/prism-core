# 🔐 Login Fix Steps

## The Issue
Your account was created successfully but login is failing. This is likely because:
1. Password mismatch
2. Session configuration issue

## Solution 1: Reset Your Password (Quickest)

Since password reset might not be implemented yet, let's create a new account:

1. Visit: https://prism-frontend-kappa.vercel.app/auth/register
2. Register with a different email (e.g., nilukush+test@gmail.com)
3. Use a simple password you'll remember
4. Try logging in immediately after registration

## Solution 2: Check Session Configuration

Visit these URLs in order:
1. https://prism-frontend-kappa.vercel.app/api/auth/session
2. https://prism-frontend-kappa.vercel.app/api/auth/providers

If you see errors, the NextAuth configuration needs environment variables in Vercel.

## Solution 3: Direct Backend Test

Open browser console at https://prism-frontend-kappa.vercel.app and run:

```javascript
// Replace YOUR_ACTUAL_PASSWORD with the password you used during registration
const testLogin = async () => {
  const formData = new URLSearchParams();
  formData.append('username', 'nilukush@gmail.com');
  formData.append('password', 'YOUR_ACTUAL_PASSWORD');
  formData.append('grant_type', 'password');

  try {
    const response = await fetch('https://prism-backend-bwfx.onrender.com/api/v1/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData.toString(),
    });
    
    const data = await response.json();
    console.log('Login response:', data);
    
    if (data.access_token) {
      console.log('✅ Login successful! Token:', data.access_token);
      
      // Now try logging in through NextAuth
      const signInResponse = await fetch('/api/auth/callback/credentials', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: 'nilukush@gmail.com',
          password: 'YOUR_ACTUAL_PASSWORD',
          csrfToken: await fetch('/api/auth/csrf').then(r => r.json()).then(d => d.csrfToken),
        }),
      });
      
      console.log('NextAuth response:', await signInResponse.text());
    }
  } catch (error) {
    console.error('Error:', error);
  }
};

testLogin();
```

## Solution 4: Environment Variables in Vercel

Make sure these are set in Vercel Dashboard:
1. Go to: https://vercel.com/nilukushs-projects/prism-app/settings/environment-variables
2. Ensure these are present:
   - `NEXTAUTH_URL` = `https://prism-frontend-kappa.vercel.app`
   - `NEXTAUTH_SECRET` = `eG29daHRVrcC17u8R50HArQaStngdLjJ`
   - `NEXT_PUBLIC_API_URL` = `https://prism-backend-bwfx.onrender.com`

3. After adding/updating, redeploy:
   ```bash
   vercel --prod --force
   ```

## Most Likely Issue

Based on the backend response, the login endpoint is working perfectly. The issue is either:
1. **Wrong password** - You might have used a different password during registration
2. **NextAuth session** - The frontend session management might need the environment variables

## Quick Win

Just create a new account with a password you're sure about:
- Email: `nilukush+test@gmail.com` 
- Password: `Test123!@#`

Then login with those exact credentials.