# 🚀 Render Environment Variables for PRISM

## Complete List of Environment Variables for Render Dashboard

Copy these exactly into your Render web service environment variables.

### 🔐 Core Configuration (Required)

```bash
# Database (Your Neon PostgreSQL)
DATABASE_URL=postgresql://neondb_owner:npg_rQk92nifVozE@ep-tiny-grass-aet08v5u-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require

# Redis (Your Upstash)
UPSTASH_REDIS_REST_URL=https://fluent-bee-10196.upstash.io
UPSTASH_REDIS_REST_TOKEN=ASfUAAIjcDE1MTAyZDFlYTA5ZDQ0MTc0Yjc4OTZiODQxN2IyN2MwMHAxMA

# Security (Use these exact values from your .env.production)
SECRET_KEY=0a6c2e3f6cf70fa1f3e442932af087bb8c437a498ad9f7c9145321ad98ef2c74
JWT_SECRET_KEY=5617ccf9d5fb1a5f15ccf1ff76a1909f91266fdfea5176fa574dc662c9ee164b

# Application
ENVIRONMENT=production
PORT=8000
```

### 🤖 AI Configuration (OpenAI)

```bash
# AI Provider Settings
DEFAULT_LLM_PROVIDER=openai
DEFAULT_LLM_MODEL=gpt-3.5-turbo
OPENAI_API_KEY=sk-proj-YOUR-OPENAI-API-KEY-HERE

# Model Configuration
LLM_MAX_TOKENS=2000
LLM_TEMPERATURE=0.7
LLM_REQUEST_TIMEOUT=60
LLM_TOP_P=0.9
LLM_FREQUENCY_PENALTY=0.0
LLM_PRESENCE_PENALTY=0.0

# Cost Control (CRITICAL for Open Source!)
AI_CACHE_ENABLED=true
AI_CACHE_TTL=86400
AI_SEMANTIC_CACHE_ENABLED=true
AI_MONTHLY_BUDGET_USD=20
AI_DAILY_REQUEST_LIMIT=500
AI_USER_MONTHLY_LIMIT=50

# AI Rate Limiting
RATE_LIMIT_AI_PER_MINUTE=5
RATE_LIMIT_AI_PER_HOUR=100
RATE_LIMIT_AI_PER_DAY=500
```

### 🌐 URLs (Update after deployment)

```bash
# These will be updated after you deploy
BACKEND_URL=https://prism-backend.onrender.com  # Change to your actual URL
FRONTEND_URL=https://prism-app.vercel.app       # Change to your Vercel URL
CORS_ALLOWED_ORIGINS=https://prism-app.vercel.app,http://localhost:3000
```

### 🛡️ Additional Security & Performance

```bash
# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_DEFAULT=100
RATE_LIMIT_WINDOW=3600

# Logging
LOG_LEVEL=INFO
DOCS_ENABLED=true

# Security Headers
BEHIND_PROXY=true
SECURE_HEADERS_ENABLED=true

# Session Management
SESSION_LIFETIME_SECONDS=86400
REFRESH_TOKEN_EXPIRE_DAYS=7
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Algorithm
ALGORITHM=HS256

# Feature Flags
FEATURE_ANALYTICS_ENABLED=false
EMAIL_VERIFICATION_REQUIRED=false
```

## 📋 Step-by-Step: Adding to Render

### 1. Go to Render Dashboard
- Navigate to your web service
- Click on "Environment" tab

### 2. Add Variables One by One
For each variable above:
1. Click "Add Environment Variable"
2. Enter the KEY exactly as shown
3. Enter the VALUE exactly as shown
4. Click "Save"

### 3. Important Notes

⚠️ **SECURITY WARNING**: 
- Your OpenAI API key is exposed in the screenshots
- Consider regenerating it after deployment
- Never commit API keys to Git

💡 **TIPS**:
- Use "Add Secret File" for sensitive values
- Group related variables together
- Double-check DATABASE_URL and Redis credentials

### 4. Variables to Update After Deployment

After your Render service is created, update these:
```bash
BACKEND_URL=https://[your-actual-render-url].onrender.com
FRONTEND_URL=https://[your-actual-vercel-url].vercel.app
CORS_ALLOWED_ORIGINS=https://[your-actual-vercel-url].vercel.app,http://localhost:3000
```

## 🚨 Cost Protection for Open Source

Since this is a free open source project, these settings are CRITICAL:

```bash
# These prevent runaway costs
AI_CACHE_ENABLED=true              # Saves 80% on repeated requests
AI_CACHE_TTL=86400                 # 24-hour cache
AI_MONTHLY_BUDGET_USD=20           # Hard stop at $20
AI_USER_MONTHLY_LIMIT=50           # Prevent single user abuse
RATE_LIMIT_AI_PER_MINUTE=5         # Prevent rapid-fire requests
```

## 📊 Monitoring Your Costs

### OpenAI Dashboard
1. Go to https://platform.openai.com/usage
2. Set up usage alerts:
   - $5 (25% of budget)
   - $10 (50% of budget)
   - $15 (75% of budget)
   - $20 (100% - service stops)

### In Your Application
```bash
# Check current usage (after deployment)
curl https://[your-backend].onrender.com/api/v1/admin/ai-usage
```

## 🎯 Deployment Checklist

Before clicking "Deploy":

- [ ] All DATABASE_URL and Redis credentials are correct
- [ ] API keys are added (OPENAI_API_KEY)
- [ ] Security keys are unique (SECRET_KEY, JWT_SECRET_KEY)
- [ ] Cost controls are enabled (AI_CACHE_ENABLED=true)
- [ ] Rate limits are set (RATE_LIMIT_AI_PER_MINUTE=5)
- [ ] Budget limit is set (AI_MONTHLY_BUDGET_USD=20)

## 💡 For Open Source Success

1. **Start Conservative**: These settings limit to ~10,000 API calls/month
2. **Monitor Daily**: Check usage for first week
3. **Add Donation Button**: Consider GitHub Sponsors for API costs
4. **Document Limits**: Tell users about rate limits in README
5. **Implement Fallback**: Code already falls back to mock if budget exceeded

## 🆘 Troubleshooting

If deployment fails:
1. Check all environment variables are set
2. Verify DATABASE_URL connection
3. Test Redis connection
4. Check Render logs for specific errors

Remember: With these settings, your maximum monthly cost is capped at $20, and with caching, you'll likely spend only $5-10/month while serving hundreds of users!