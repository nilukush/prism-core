# 🚨 CRITICAL DEPLOYMENT FIXES

## Issue 1: Render - Redis Connection Error

**Error**: `redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379`

**Cause**: The app is trying to connect to localhost Redis instead of Upstash

### IMMEDIATE FIX in Render Dashboard:

1. Go to Render Dashboard → prism-backend-bwfx → Environment
2. Add/Update these variables:

```bash
# Change REDIS_URL to standard Redis format for aioredis
REDIS_URL=redis://default:ASfUAAIjcDE1MTAyZDFlYTA5ZDQ0MTc0Yjc4OTZiODQxN2IyN2MwMHAxMA@fluent-bee-10196.upstash.io:10196

# Or if you need to use localhost for some reason, add:
REDIS_URL=redis://localhost:6379

# But better to use Upstash REST client - keep these:
UPSTASH_REDIS_REST_URL=https://fluent-bee-10196.upstash.io
UPSTASH_REDIS_REST_TOKEN=ASfUAAIjcDE1MTAyZDFlYTA5ZDQ0MTc0Yjc4OTZiODQxN2IyN2MwMHAxMA
```

### Or Fix in Code (Temporary):

Create a quick patch to disable rate limiting:

```python
# In rate_limiting.py, modify the initialize method:
async def initialize(self):
    """Initialize Redis connection and strategies."""
    # TEMPORARY: Skip Redis for now
    logger.warning("Redis initialization skipped - rate limiting disabled")
    return
```

## Issue 2: Vercel - Still Using Old Commit

**Problem**: Vercel is deploying commit `2db96be` instead of `4868d4c`

### FIX Option 1: Force via Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Link to your project
vercel link

# Deploy with force flag
vercel --force

# Or deploy production
vercel --prod --force
```

### FIX Option 2: Via Dashboard

1. Go to Vercel Dashboard
2. Click on "Deployments" tab
3. Find a deployment with commit `4868d4c`
4. Click "..." menu → "Promote to Production"

If no deployment with that commit exists:
1. Click "Create Deployment"
2. Enter commit SHA: `4868d4c`
3. Deploy

### FIX Option 3: Clear Everything and Reconnect

```bash
# Remove local Vercel config
rm -rf .vercel

# Force push to ensure GitHub has latest
git push origin main --force

# In Vercel Dashboard:
# 1. Go to Settings → Git
# 2. Disconnect GitHub
# 3. Delete the project
# 4. Create new project
# 5. Import from GitHub again
# 6. Set Root Directory to "frontend"
# 7. Ensure build commands have NO "cd frontend"
```

## Quick Status Check

```bash
# Check Render backend
curl https://prism-backend-bwfx.onrender.com/health

# Check what commit Vercel is using
# Look at deployment logs or dashboard
```

## Priority Order

1. **Fix Render First** (5 min):
   - Add REDIS_URL in correct format
   - Or temporarily disable rate limiting
   - Restart service

2. **Fix Vercel Second** (10 min):
   - Use CLI to force deploy
   - Or recreate project with correct settings

## Expected Results

### Render Success:
```json
{"status":"healthy","timestamp":"...","version":"1.0.0"}
```

### Vercel Success:
- Build logs show: `Running "install" command: npm install`
- NOT: `Running "install" command: cd frontend && npm install`
- Deployment uses commit `4868d4c`

---

**DO THIS NOW**:
1. Add REDIS_URL to Render environment
2. Force deploy Vercel with CLI or recreate project