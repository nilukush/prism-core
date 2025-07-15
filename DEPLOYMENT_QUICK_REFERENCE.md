# 🚀 PRISM Deployment Quick Reference

## Your Current Setup

### ✅ Completed
- **Database**: Neon PostgreSQL (ep-tiny-grass-aet08v5u)
- **Cache**: Upstash Redis (fluent-bee-10196)
- **AI Provider**: OpenAI GPT-3.5-turbo
- **Budget**: $20/month (selected in script)

### 🔄 In Progress
- **Backend**: Deploying to Render
- **Frontend**: Next step (Vercel)

## 🎯 Critical Environment Variables for Render

```bash
# These MUST be added in Render dashboard:

DEFAULT_LLM_PROVIDER=openai
DEFAULT_LLM_MODEL=gpt-3.5-turbo
OPENAI_API_KEY=sk-proj-[YOUR-KEY]  # Your actual key

# Cost Protection (ESSENTIAL!)
AI_CACHE_ENABLED=true
AI_CACHE_TTL=86400
AI_MONTHLY_BUDGET_USD=20
RATE_LIMIT_AI_PER_MINUTE=5

# Your Database & Redis (already have these)
DATABASE_URL=postgresql://neondb_owner:npg_rQk92nifVozE@ep-tiny-grass-aet08v5u-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require
UPSTASH_REDIS_REST_URL=https://fluent-bee-10196.upstash.io
UPSTASH_REDIS_REST_TOKEN=ASfUAAIjcDE1MTAyZDFlYTA5ZDQ0MTc0Yjc4OTZiODQxN2IyN2MwMHAxMA
```

## 📋 While Render is Deploying

### 1. Watch the Logs
Look for:
- ✅ "Build successful"
- ✅ "Starting service"
- ✅ "Listening on port 8000"

### 2. Common Issues
- **"Module not found"**: Check requirements.txt
- **"Port already in use"**: Ensure PORT=8000 is set
- **"Database connection failed"**: Verify DATABASE_URL

### 3. First Deployment Takes Time
- Build: 3-5 minutes
- Start: 1-2 minutes
- Total: ~5-7 minutes

## 🔍 After Deployment Completes

### 1. Get Your URL
Your Render URL will be: `https://[your-app-name].onrender.com`

### 2. Test It's Working
```bash
# Quick test (replace with your URL)
curl https://prism-backend.onrender.com/health

# Should return:
{"status":"healthy","timestamp":"..."}
```

### 3. Update These Variables in Render
```bash
BACKEND_URL=https://[your-actual-url].onrender.com
CORS_ALLOWED_ORIGINS=https://[your-vercel-url].vercel.app,http://localhost:3000
```

## 💰 OpenAI Cost Protection Active

With your configuration:
- **Max cost**: $20/month (hard limit)
- **Expected cost**: $5-10/month (with caching)
- **Per PRD**: ~$0.002 (1/5 of a cent)
- **Cache saves**: 80% of requests

## 🚨 Important Reminders

1. **Regenerate your OpenAI API key** if it was exposed
2. **Set billing alerts** at https://platform.openai.com/account/billing
3. **Monitor usage** daily for first week
4. **Check cache hit rate** (should be >80%)

## 📊 Monitoring Commands

After deployment:
```bash
# Check if service is up
curl https://[your-url].onrender.com/health

# View API docs
open https://[your-url].onrender.com/docs

# Monitor deployment
./scripts/monitor-deployment.sh
```

## 🎯 Next Steps

1. **Wait for Render deployment** to complete (5-7 mins)
2. **Run monitoring script** to verify
3. **Deploy frontend to Vercel**
4. **Test end-to-end flow**

## 🆘 If Something Goes Wrong

1. Check Render logs (Dashboard → Logs)
2. Verify all environment variables are set
3. Ensure database is active (Neon dashboard)
4. Try manual restart in Render

Remember: First deployment always takes longer. Subsequent deployments are much faster!