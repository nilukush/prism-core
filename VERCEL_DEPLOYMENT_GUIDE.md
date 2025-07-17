# Vercel Deployment Guide for PRISM

This guide helps you deploy PRISM frontend to Vercel and make it publicly accessible.

## Prerequisites

- Vercel account (free tier is sufficient)
- PRISM backend already deployed (e.g., on Render)
- Git repository with the PRISM code

## Environment Variables

Before deploying, ensure these environment variables are set correctly:

```env
NEXT_PUBLIC_API_URL=https://prism-backend-bwfx.onrender.com
NEXTAUTH_URL=https://your-vercel-app.vercel.app
NEXTAUTH_SECRET=eG29daHRVrcC17u8R50HArQaStngdLjJ
```

**Important**: 
- `NEXTAUTH_SECRET` must be exactly 32 characters long with NO special characters
- Replace `your-vercel-app` with your actual Vercel app URL

## Deployment Steps

### 1. Deploy to Vercel

```bash
# From the frontend directory
cd frontend

# Install Vercel CLI if not already installed
npm i -g vercel

# Deploy
vercel
```

### 2. Configure Environment Variables in Vercel

1. Go to your Vercel project dashboard
2. Navigate to Settings → Environment Variables
3. Add the following variables:

   - `NEXT_PUBLIC_API_URL`: `https://prism-backend-bwfx.onrender.com`
   - `NEXTAUTH_URL`: `https://[your-app-name].vercel.app`
   - `NEXTAUTH_SECRET`: `eG29daHRVrcC17u8R50HArQaStngdLjJ`

### 3. Disable Deployment Protection (Make Site Public)

To make your PRISM deployment publicly accessible without authentication:

1. **Go to Project Settings**: In Vercel dashboard, select your PRISM project
2. **Navigate to**: Settings → General → Deployment Protection
3. **Disable Protection**: 
   - Find "Standard Protection" 
   - Toggle it OFF to disable protection
   - This will make your site publicly accessible

### 4. Update NEXTAUTH_URL

After deployment, update the `NEXTAUTH_URL` with your actual Vercel URL:

1. Go to Settings → Environment Variables
2. Update `NEXTAUTH_URL` to your actual deployment URL (e.g., `https://prism-frontend.vercel.app`)
3. Redeploy for changes to take effect

## Troubleshooting

### "Invalid value for 'generate.secret'" Error

This error occurs when:
- The secret contains special characters (like =, +, /)
- The secret is not exactly 32 characters
- The secret is not a string

**Solution**: Use this command to generate a valid secret:
```bash
openssl rand -base64 24 | tr -d "=/+" | cut -c1-32
```

### Site Still Requires Authentication

If your site still requires authentication after disabling protection:
1. Clear your browser cache
2. Check if you have any custom authentication logic in your Next.js middleware
3. Ensure deployment protection is disabled at the project level, not team level

### CORS Issues

If you encounter CORS errors:
1. Ensure your backend allows requests from your Vercel domain
2. Add your Vercel URL to the backend's CORS_ORIGINS configuration

## Security Considerations

When making PRISM publicly accessible:
- Anyone with the URL can access the application
- Ensure your backend has proper authentication and authorization
- Consider implementing rate limiting on your backend
- Monitor usage and costs, especially for AI features

## Alternative: Protection Bypass for Testing

If you want to keep some protection but allow automated access:

1. Keep deployment protection enabled
2. Go to Settings → General → Protection Bypass for Automation
3. Generate a bypass token
4. Access your site with: `https://your-app.vercel.app?x-vercel-protection-bypass=YOUR_TOKEN`

This is useful for:
- E2E testing
- Sharing with specific users
- Temporary access

## Next Steps

After successful deployment:
1. Test the application thoroughly
2. Configure a custom domain (optional)
3. Set up monitoring and analytics
4. Configure proper SEO settings if needed