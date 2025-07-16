# Force Vercel to Deploy Latest Commit (0279ba9)

## Problem Summary
- Vercel is stuck on old commit `5405bfb` instead of latest `0279ba9`
- The old commit has the problematic `@radix-ui/react-badge` package
- Fixed in commit `4976748` by removing the package

## Solution Options

### Option 1: Via Vercel Dashboard (Recommended)
1. Go to: https://vercel.com/nilukushs-projects/prism/deployments
2. Click **"Create Deployment"** button
3. In the deployment dialog:
   - Select **"Deploy from Git commit"**
   - Enter commit SHA: `0279ba9`
   - Click **"Create Deployment"**

### Option 2: Clear Cache and Force Redeploy
1. Go to Vercel Settings → Advanced
2. Click **"Clear Build Cache"**
3. Go to Deployments tab
4. On the latest deployment, click the three dots menu
5. Select **"Redeploy"**
6. Choose **"Redeploy with existing Build Cache cleared"**

### Option 3: Force Push Empty Commit
```bash
cd /Users/nileshkumar/gh/prism/prism-core/frontend
git commit --allow-empty -m "Force Vercel deployment [skip ci]"
git push origin main
```

### Option 4: Use Vercel API (if you have a token)
```bash
# Get your token from: https://vercel.com/account/tokens
export VERCEL_TOKEN="your-token-here"

# Trigger deployment
curl -X POST https://api.vercel.com/v13/deployments \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "prism",
    "gitSource": {
      "type": "github",
      "ref": "0279ba9",
      "repoId": "your-repo-id"
    }
  }'
```

### Option 5: Disconnect and Reconnect Git
1. Go to Vercel Settings → Git
2. Click **"Disconnect from Git"**
3. Click **"Connect Git Repository"**
4. Select your repository
5. This will trigger a fresh deployment with latest commit

## Verify Deployment
After triggering deployment:
1. Check build logs for commit SHA `0279ba9`
2. Verify no npm errors about `@radix-ui/react-badge`
3. Confirm deployment succeeds

## Current Status
- Latest commit: `0279ba9` (Fix: DDoS protection Redis connection for Upstash)
- Problem commit: `5405bfb` (has @radix-ui/react-badge issue)
- Fix commit: `4976748` (removed problematic package)