# 🚨 PRISM Deployment Action Plan

## Current Issues Summary

1. **Render Backend**: Not responding (timeout/502)
2. **OpenAI API Key**: Invalid/expired (401 error)
3. **Vercel Frontend**: Build failing (wrong directory)

## 🔥 Priority 1: Fix Render Backend

### Immediate Actions:

1. **Go to Render Dashboard**
   - URL: https://dashboard.render.com
   - Navigate to: prism-backend-bwfx service
   - Click on "Logs" tab

2. **Check for These Common Errors**:
   ```
   ❌ "Port 8000 is already in use" → Add PORT=8000 env var
   ❌ "Cannot connect to database" → Check DATABASE_URL
   ❌ "Redis connection refused" → Verify Upstash credentials
   ❌ "Module not found" → Build cache issue
   ```

3. **Required Environment Variables**:
   ```bash
   # CRITICAL - Must have these
   PORT=8000
   DATABASE_URL=postgresql://neondb_owner:npg_rQk92nifVozE@ep-tiny-grass-aet08v5u-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require
   UPSTASH_REDIS_REST_URL=https://fluent-bee-10196.upstash.io
   UPSTASH_REDIS_REST_TOKEN=ASfUAAIjcDE1MTAyZDFlYTA5ZDQ0MTc0Yjc4OTZiODQxN2IyN2MwMHAxMA
   SECRET_KEY=0a6c2e3f6cf70fa1f3e442932af087bb8c437a498ad9f7c9145321ad98ef2c74
   JWT_SECRET_KEY=5617ccf9d5fb1a5f15ccf1ff76a1909f91266fdfea5176fa574dc662c9ee164b
   
   # AI Configuration
   DEFAULT_LLM_PROVIDER=openai
   DEFAULT_LLM_MODEL=gpt-3.5-turbo
   OPENAI_API_KEY=[YOUR-NEW-KEY-HERE]
   
   # Cost Controls
   AI_CACHE_ENABLED=true
   AI_CACHE_TTL=86400
   AI_MONTHLY_BUDGET_USD=20
   RATE_LIMIT_AI_PER_MINUTE=5
   
   # System
   ENVIRONMENT=production
   LOG_LEVEL=INFO
   DOCS_ENABLED=true
   RATE_LIMIT_ENABLED=false
   ```

4. **If Still Failing**:
   - Click "Manual Deploy" → "Clear build cache & deploy"
   - This forces a fresh build

## 🔑 Priority 2: Fix OpenAI API Key

Your API key was likely exposed in screenshots and revoked by OpenAI.

### Steps:
1. **Generate New API Key**:
   - Go to: https://platform.openai.com/api-keys
   - Click "Create new secret key"
   - Name it: "PRISM Production"
   - Copy immediately (shown only once!)

2. **Update in Render**:
   - Dashboard → prism-backend-bwfx → Environment
   - Update: `OPENAI_API_KEY=sk-proj-[your-new-key]`
   - Click "Save Changes"
   - Service will auto-restart

3. **Set Billing Alerts**:
   - https://platform.openai.com/account/billing
   - Add payment method if needed
   - Set alerts at: $5, $10, $15, $20

## 🎨 Priority 3: Fix Vercel Deployment

### Option A: Vercel Dashboard (Easiest)
1. Go to: https://vercel.com/dashboard
2. Click "Add New..." → "Project"
3. Import: `nilukush/prism-core`
4. **IMPORTANT**: Set Root Directory to `frontend`
5. Add environment variables:
   ```
   NEXT_PUBLIC_API_URL=https://prism-backend-bwfx.onrender.com
   NEXTAUTH_URL=https://[your-vercel-url].vercel.app
   NEXTAUTH_SECRET=[generate-with-openssl-rand-base64-32]
   ```
6. Click "Deploy"

### Option B: CLI Fix
```bash
cd frontend

# Install Vercel CLI if needed
npm i -g vercel

# Deploy with correct settings
vercel --prod

# When prompted:
# - Set up and deploy? Y
# - Which scope? (your account)
# - Link to existing project? N
# - What's your project name? prism-frontend
# - In which directory is your code? ./
# - Want to modify settings? N
```

## ✅ Success Checklist

After completing the above:

1. **Backend Health Check**:
   ```bash
   curl https://prism-backend-bwfx.onrender.com/health
   # Should return: {"status":"healthy","timestamp":"...","version":"1.0.0"}
   ```

2. **API Documentation**:
   ```bash
   open https://prism-backend-bwfx.onrender.com/docs
   ```

3. **Test AI Integration**:
   ```bash
   # Will need auth, but should not return 500
   curl -X POST https://prism-backend-bwfx.onrender.com/api/v1/ai/generate/prd \
     -H "Content-Type: application/json" \
     -d '{"product_name":"Test","description":"Test product"}'
   ```

## 🚀 Quick Debug Commands

```bash
# Check backend status
curl -I https://prism-backend-bwfx.onrender.com/health

# Test database connection (requires auth)
curl https://prism-backend-bwfx.onrender.com/api/v1/health/detailed

# View all registered routes
curl https://prism-backend-bwfx.onrender.com/openapi.json | jq '.paths | keys'
```

## 📱 Emergency Contacts

- **Render Status**: https://status.render.com
- **OpenAI Status**: https://status.openai.com
- **Vercel Status**: https://www.vercel-status.com

## ⏱️ Timeline

1. **Fix Render** (10-15 min): Check logs, add env vars, redeploy
2. **Fix OpenAI** (5 min): Generate key, update in Render
3. **Deploy Frontend** (5-10 min): Via Vercel dashboard

**Total Time**: ~30 minutes to full deployment

---

## 🆘 If Still Stuck

1. **Render not starting?**
   - Share the error logs from Render dashboard
   - Try deploying a simple "hello world" to test

2. **OpenAI still failing?**
   - Double-check key starts with `sk-proj-`
   - Ensure you have credits/payment method
   - Try key in local test first

3. **Vercel still failing?**
   - Make sure you selected `frontend` as root
   - Check package.json exists in frontend/
   - Try local build first: `cd frontend && npm run build`

Remember: First deployments always take longer. Once working, updates are much faster!