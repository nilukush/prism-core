# 🧹 Vercel Project Cleanup & Configuration

## Current Situation
You have multiple Vercel projects:
1. **prism** - Old project with stuck Git integration (commit df499ff)
2. **frontend** - New project we created that's working

## Recommended Actions

### 1. Delete Old Failed Projects
Go to Vercel dashboard and delete these projects:
- `prism` (if it exists)
- `prism-core` (if it exists)
- Any other failed PRISM projects

### 2. Keep Only Working Project
Keep: **frontend** - This is the one that successfully deployed

### 3. Connect to GitHub (IMPORTANT)
```bash
cd /Users/nileshkumar/gh/prism/prism-core/frontend
vercel git connect
```

When prompted:
1. Select GitHub as provider
2. Authorize Vercel to access your repository
3. Select `nilukush/prism-core`
4. Confirm connection

### 4. Configure Git Settings
In Vercel Dashboard:
1. Go to: https://vercel.com/nilukushs-projects/frontend/settings/git
2. Set:
   - **Production Branch**: main
   - **Root Directory**: frontend
   - **Include source files outside Root Directory**: ✅ Enabled

### 5. Environment Variables
Ensure these are set in Vercel:
```
NEXT_PUBLIC_API_URL=https://prism-backend-bwfx.onrender.com
NEXTAUTH_URL=https://frontend-nilukushs-projects.vercel.app
NEXTAUTH_SECRET=[generate-32-char-secret]
GOOGLE_CLIENT_ID=[if-using-google-oauth]
GOOGLE_CLIENT_SECRET=[if-using-google-oauth]
```

## Why We Created New Project
- Old project had stuck Git webhook
- Was pulling old commit (df499ff) instead of latest
- Creating fresh project was faster than debugging webhook

## Final Setup
After connecting to GitHub:
- Future pushes to `main` will auto-deploy
- No need for manual deployments
- Git integration will track latest commits