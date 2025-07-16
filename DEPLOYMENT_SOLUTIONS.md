# 🚀 PRISM Deployment Solutions

## Issue 1: Vercel Auto-Adding "cd frontend"

### Understanding the Issue
Vercel is **correctly** adding `cd frontend` because:
- Your root directory is set to `frontend`
- But your build commands also include `cd frontend`
- This results in: `cd frontend && cd frontend && npm install` (double cd)

### ✅ SOLUTION: Remove cd from Commands

In Vercel Dashboard:
1. Go to Project Settings → General → Build & Development Settings
2. Update these fields:

**Current (WRONG):**
```
Build Command: cd frontend && npm run build
Install Command: cd frontend && npm install
Output Directory: frontend/.next
```

**Change to (CORRECT):**
```
Build Command: npm run build
Install Command: npm install
Output Directory: .next
```

### Why This Works
- Vercel automatically navigates to `frontend` (your root directory)
- You don't need `cd frontend` in commands
- Output directory is relative to root directory (frontend)

## Issue 2: Render Backend Deployment

### Check Deployment Progress
Since Render CLI needs authentication, let's use direct checks:

```bash
# Quick status check
curl -I https://prism-backend-bwfx.onrender.com/health

# If you have Render CLI authenticated:
render logs prism-backend-bwfx --tail
```

### Most Likely Issues

1. **Database URL Still Missing asyncpg**
   - Even though we pushed the fix, check if it deployed
   - Go to Render Dashboard → Logs

2. **Build Cache Issue**
   - Go to Render Dashboard
   - Manual Deploy → Clear build cache & deploy

3. **Missing Environment Variables**
   - Verify ALL these are set in Render:
   ```
   PORT=8000
   DATABASE_URL=postgresql://... (with or without +asyncpg now)
   UPSTASH_REDIS_REST_URL=https://fluent-bee-10196.upstash.io
   UPSTASH_REDIS_REST_TOKEN=ASf...
   SECRET_KEY=0a6c2e3f...
   JWT_SECRET_KEY=5617ccf9...
   DEFAULT_LLM_PROVIDER=openai
   DEFAULT_LLM_MODEL=gpt-3.5-turbo
   OPENAI_API_KEY=sk-proj-...
   ```

## Quick Action Plan

### 1. Fix Vercel NOW (2 minutes)
```
1. Go to Vercel Dashboard
2. Project Settings → Build & Development Settings
3. Remove "cd frontend" from all commands:
   - Build Command: npm run build
   - Install Command: npm install
   - Output Directory: .next
4. Save and Redeploy
```

### 2. Check Render Logs (1 minute)
```
1. Go to https://dashboard.render.com
2. Click on prism-backend-bwfx
3. Go to "Logs" tab
4. Look for:
   - "Build successful" ✅
   - "Starting service" ✅
   - Any error messages ❌
```

### 3. If Render Still Failing
Most common fixes:
```
A. Add missing PORT=8000 environment variable
B. Click "Manual Deploy" → "Clear build cache & deploy"
C. Check if our code fix was deployed (look for "Fix: Auto-convert PostgreSQL URL")
```

## Monitoring Commands

### Check Backend Status
```bash
# Simple health check
curl https://prism-backend-bwfx.onrender.com/health

# With timeout
curl --max-time 10 https://prism-backend-bwfx.onrender.com/health

# Check headers only
curl -I https://prism-backend-bwfx.onrender.com/health
```

### Check Vercel Deployment
```bash
# Install Vercel CLI if needed
npm i -g vercel

# Login
vercel login

# Check deployment logs
vercel logs https://prism-app.vercel.app
```

## Expected Timeline

1. **Vercel**: Will work immediately after removing "cd frontend"
2. **Render**: 
   - If just missing PORT: 2-3 minutes after adding
   - If needs cache clear: 5-7 minutes
   - Our code fix should have deployed by now

## Success Indicators

✅ Render Backend Working:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T20:30:00Z",
  "version": "1.0.0"
}
```

✅ Vercel Frontend Working:
- Build completes without "directory not found" errors
- Shows "Ready" status in dashboard

---

## IMMEDIATE ACTIONS:

1. **GO TO VERCEL** → Remove "cd frontend" from commands
2. **GO TO RENDER** → Check logs for current error
3. **ADD PORT=8000** if missing in Render environment

The fixes are simple - just configuration adjustments!