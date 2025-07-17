# 🔧 Fixing Vercel Git Integration

## Problem
Vercel is deploying from old commit (df499ff) instead of latest (474a918)

## Solution: Import Project Correctly

### Option 1: Via Vercel Dashboard (Recommended)
1. Go to: https://vercel.com/new
2. Click "Import Git Repository"
3. Select: `nilukush/prism-core`
4. Configure:
   - **Root Directory**: `frontend`
   - **Framework Preset**: Next.js
   - **Build Command**: `npm run build`
   - **Install Command**: `npm install --legacy-peer-deps --force`
5. Add Environment Variables:
   ```
   NEXT_PUBLIC_API_URL=https://prism-backend-bwfx.onrender.com
   NEXTAUTH_URL=https://[your-project].vercel.app
   NEXTAUTH_SECRET=[generate-secret]
   ```
6. Deploy

### Option 2: Delete and Re-import
1. Delete the `prism` project in Vercel dashboard
2. Run in terminal:
   ```bash
   cd /Users/nileshkumar/gh/prism/prism-core
   vercel --no-local
   ```
3. When prompted:
   - Set up and deploy? **Y**
   - Which scope? **nilukushs-projects**
   - Link to existing project? **N**
   - Project name? **prism-frontend-latest**
   - Root directory? **frontend**

### Option 3: Force Deploy Latest Commit
1. In Vercel Dashboard, go to deployments
2. Click "Create Deployment" (three dots menu)
3. Enter commit SHA: `474a918`
4. Deploy

## Why This Happens
- Vercel caches Git integration
- Old projects may have stale webhook configurations
- Git provider permissions might be outdated

## Verification
After fixing, deployments should show:
- Correct commit: 474a918 (not df499ff)
- Build succeeds with 0 errors
- Latest code is deployed