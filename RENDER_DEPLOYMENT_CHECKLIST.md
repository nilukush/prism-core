# 🚀 Render Deployment Checklist & Verification

## 📋 Pre-Deployment Verification

### Environment Variables to Add in Render Dashboard

Since you selected **OpenAI GPT-3.5**, here are the EXACT environment variables you need:

```bash
# ===== CORE CONFIGURATION =====
DATABASE_URL=postgresql://neondb_owner:npg_rQk92nifVozE@ep-tiny-grass-aet08v5u-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require
UPSTASH_REDIS_REST_URL=https://fluent-bee-10196.upstash.io
UPSTASH_REDIS_REST_TOKEN=ASfUAAIjcDE1MTAyZDFlYTA5ZDQ0MTc0Yjc4OTZiODQxN2IyN2MwMHAxMA
SECRET_KEY=0a6c2e3f6cf70fa1f3e442932af087bb8c437a498ad9f7c9145321ad98ef2c74
JWT_SECRET_KEY=5617ccf9d5fb1a5f15ccf1ff76a1909f91266fdfea5176fa574dc662c9ee164b

# ===== SYSTEM =====
ENVIRONMENT=production
PORT=8000
BEHIND_PROXY=true
LOG_LEVEL=INFO
DOCS_ENABLED=true

# ===== AI CONFIGURATION (OpenAI GPT-3.5) =====
DEFAULT_LLM_PROVIDER=openai
DEFAULT_LLM_MODEL=gpt-3.5-turbo
OPENAI_API_KEY=[YOUR-API-KEY-HERE]  # Add your actual key
LLM_MAX_TOKENS=2000
LLM_TEMPERATURE=0.7
LLM_REQUEST_TIMEOUT=60
LLM_TOP_P=0.9
LLM_FREQUENCY_PENALTY=0.0
LLM_PRESENCE_PENALTY=0.0

# ===== COST PROTECTION (CRITICAL!) =====
AI_CACHE_ENABLED=true
AI_CACHE_TTL=86400
AI_SEMANTIC_CACHE_ENABLED=true
AI_MONTHLY_BUDGET_USD=20
AI_DAILY_REQUEST_LIMIT=500
AI_USER_MONTHLY_LIMIT=50

# ===== RATE LIMITING =====
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_AI_PER_MINUTE=5
RATE_LIMIT_AI_PER_HOUR=100
RATE_LIMIT_AI_PER_DAY=500

# ===== URLS (Update after deployment) =====
BACKEND_URL=https://[your-app].onrender.com
FRONTEND_URL=https://[your-frontend].vercel.app
CORS_ALLOWED_ORIGINS=https://[your-frontend].vercel.app,http://localhost:3000

# ===== AUTHENTICATION =====
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
SESSION_LIFETIME_SECONDS=86400

# ===== FEATURES =====
FEATURE_ANALYTICS_ENABLED=false
EMAIL_VERIFICATION_REQUIRED=false
SECURE_HEADERS_ENABLED=true
```

## 🔍 During Deployment

### Monitor Build Logs

Look for these key indicators:

✅ **Good Signs**:
```
==> Building...
[+] Building 123.4s (15/15) FINISHED
==> Uploading build...
==> Build uploaded in 12s
==> Starting service...
```

❌ **Warning Signs**:
```
ERROR: failed to solve: process "/bin/sh -c pip install -r requirements.txt"
ModuleNotFoundError: No module named 'fastapi'
Error: Cannot find module
```

### Common Build Issues & Solutions

#### 1. Docker Build Fails
```bash
# Issue: "failed to solve: executor failed"
# Solution: Check Dockerfile syntax and paths
```

#### 2. Port Binding Error
```bash
# Issue: "bind: address already in use"
# Solution: Ensure PORT=8000 is set
```

#### 3. Module Not Found
```bash
# Issue: "ModuleNotFoundError"
# Solution: Check requirements.txt is complete
```

## ✅ Post-Deployment Verification

### Step 1: Basic Health Check

```bash
# Replace with your actual URL
curl https://prism-backend.onrender.com/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2024-01-15T12:00:00Z",
  "version": "1.0.0"
}
```

### Step 2: API Documentation

Visit: `https://[your-app].onrender.com/docs`

You should see the Swagger UI with all API endpoints.

### Step 3: Database Connection Test

```bash
curl https://[your-app].onrender.com/api/v1/health/detailed \
  -H "Authorization: Bearer [admin-token]"

# Should show:
{
  "database": "connected",
  "redis": "connected",
  "ai_provider": "openai"
}
```

### Step 4: AI Configuration Test

```bash
# Test AI is configured correctly
curl -X POST https://[your-app].onrender.com/api/v1/ai/test \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello"}'

# Should return AI response (or mock if budget exceeded)
```

## 🚨 Troubleshooting Deployment Issues

### Issue: Service Won't Start

**Check Logs**:
```bash
# In Render dashboard → Logs tab
# Look for:
- Database connection errors
- Missing environment variables
- Port binding issues
```

**Common Fixes**:
1. Verify all environment variables are set
2. Check DATABASE_URL format
3. Ensure PORT=8000 is set
4. Verify Redis credentials

### Issue: 502 Bad Gateway

**Causes**:
- Service is still starting (wait 2-3 minutes)
- Build failed (check logs)
- Health check failing

**Solutions**:
1. Wait for cold start (first deployment takes longer)
2. Check build logs for errors
3. Verify health check path is `/health`

### Issue: Database Connection Failed

**Error**: `connection to server at "xxx", port 5432 failed`

**Fix**:
1. Verify DATABASE_URL is exact copy from Neon
2. Check if Neon database is active (not suspended)
3. Ensure `?sslmode=require` is in URL

### Issue: Redis Connection Failed

**Error**: `Redis connection refused`

**Fix**:
1. Verify Upstash REST URL and token
2. Check token hasn't expired
3. Ensure using REST URL (not standard Redis URL)

## 📊 Cost Monitoring Setup

### OpenAI Dashboard Setup

1. Go to https://platform.openai.com/usage
2. Set up billing alerts:
   - Alert 1: $5 (25% of budget)
   - Alert 2: $10 (50% of budget)
   - Alert 3: $15 (75% of budget)
   - Alert 4: $20 (100% - STOP)

### In-App Monitoring

After deployment, create an admin monitoring endpoint:

```bash
# Check current AI usage
curl https://[your-app].onrender.com/api/v1/admin/ai-usage \
  -H "Authorization: Bearer [admin-token]"

# Response:
{
  "current_month_cost": 2.45,
  "budget_remaining": 17.55,
  "requests_today": 156,
  "cache_hit_rate": 0.82,
  "average_cost_per_request": 0.0016
}
```

## 🔒 Security Checklist

- [ ] API key is added via Render dashboard (not in code)
- [ ] All secrets use Render's secret management
- [ ] CORS is configured for your frontend only
- [ ] Rate limiting is enabled
- [ ] Budget limits are set
- [ ] Monitoring is configured

## 📈 Performance Optimization

### After First Week

Check these metrics:
```bash
# Cache performance
curl https://[your-app].onrender.com/api/v1/metrics/cache

# Should show >80% hit rate
```

### Optimize if Needed

1. **High Costs**: Increase cache TTL to 172800 (2 days)
2. **Slow Responses**: Check if service is sleeping (normal for free tier)
3. **Rate Limits Hit**: Adjust based on actual usage

## 🎯 Next Steps After Successful Deployment

1. **Update Frontend Environment**:
   ```bash
   # In Vercel, update:
   NEXT_PUBLIC_API_URL=https://[your-actual-render-url].onrender.com
   ```

2. **Test End-to-End**:
   - Login from frontend
   - Create a project
   - Generate a PRD with AI
   - Verify it uses OpenAI (check response quality)

3. **Monitor First 24 Hours**:
   - Check OpenAI usage every few hours
   - Verify caching is working
   - Monitor error logs

4. **Set Up Alerts**:
   - UptimeRobot for downtime
   - OpenAI for cost overruns
   - Render for deployment failures

## 🆘 Emergency Procedures

### If Costs Spike

1. **Immediate**: Set DEFAULT_LLM_PROVIDER=mock in Render
2. **Investigate**: Check logs for abuse patterns
3. **Adjust**: Lower rate limits or user quotas

### If Service Crashes

1. **Check**: Render logs for error details
2. **Restart**: Manual restart from Render dashboard
3. **Rollback**: Use previous deployment if needed

## 📞 Support Resources

- **Render Status**: https://status.render.com
- **Render Docs**: https://render.com/docs
- **OpenAI Status**: https://status.openai.com
- **Your Logs**: Render Dashboard → Your Service → Logs

Remember: With your configuration, maximum monthly cost is capped at $20, and with 80%+ cache hit rate, actual costs should be $5-10/month!