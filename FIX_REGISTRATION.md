# 🔧 Fix Registration Issue

## Problem
Registration failing with "something went wrong" error because of incorrect environment variables.

## Solution

### 1. Update Vercel Environment Variables

Go to: https://vercel.com/nilukushs-projects/prism-app/settings/environment-variables

Add/Update these variables:

```
NEXT_PUBLIC_API_URL=https://prism-backend-bwfx.onrender.com
NEXTAUTH_URL=https://prism-frontend-kappa.vercel.app
NEXTAUTH_SECRET=eG29daHRVrcC17u8R50HArQaStngdLjJ
NEXT_PUBLIC_APP_URL=https://prism-frontend-kappa.vercel.app
NEXT_PUBLIC_APP_NAME=PRISM
```

### 2. Redeploy After Setting Variables

```bash
vercel --prod
```

### 3. Update Backend CORS (if needed)

In Render Dashboard, ensure `CORS_ORIGINS` includes:
```
https://prism-frontend-kappa.vercel.app,https://prism-9z5biinym-nilukushs-projects.vercel.app,http://localhost:3000,http://localhost:3100
```

## Testing

1. Visit: https://prism-frontend-kappa.vercel.app/auth/register
2. Fill in the registration form
3. Check browser console (F12) for any errors
4. If still failing, check Network tab for the actual API response

## Common Issues

1. **Backend is sleeping** - First request takes 30-60 seconds on free tier
2. **CORS error** - Update CORS_ORIGINS in Render
3. **Wrong API URL** - Make sure NEXT_PUBLIC_API_URL is correct
4. **Auth secret mismatch** - Use the same secret everywhere