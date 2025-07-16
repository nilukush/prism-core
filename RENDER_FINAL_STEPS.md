# ✅ Render Deployment Final Steps

## 🎯 Your Render Services Detected

We found these services deploying:
- **prism-backend.onrender.com** (503 - Still deploying) ✓
- **prism-api.onrender.com** (503 - Still deploying) ✓

Both are currently building/starting up. This is normal!

## ⏱️ While Deployment Completes (5-10 min)

### 1. Check Render Dashboard
- Look for "Deploy in progress" status
- Watch the logs for:
  - ✅ "Build successful"
  - ✅ "Starting service..."
  - ✅ "Application startup complete"

### 2. Monitor Progress
```bash
# Quick check (every 2 min)
./scripts/check-render-status.sh

# Or manually test your URLs
curl https://prism-backend.onrender.com/health
curl https://prism-api.onrender.com/health
```

## 🚀 Once Deployment is Live

### 1. Verify It's Working
```bash
# Should return {"status":"healthy","timestamp":"...","version":"1.0.0"}
curl https://prism-backend.onrender.com/health

# View your API docs
open https://prism-backend.onrender.com/docs
```

### 2. Update These Environment Variables in Render

Go to Render Dashboard → Your Service → Environment

Add/Update:
```bash
BACKEND_URL=https://prism-backend.onrender.com
FRONTEND_URL=https://your-app.vercel.app  # After Vercel deployment
CORS_ALLOWED_ORIGINS=https://your-app.vercel.app,http://localhost:3000
```

### 3. Test AI Configuration
```bash
# Test that AI is configured (you'll need auth first)
curl -X POST https://prism-backend.onrender.com/api/v1/ai/config/test \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
```

## 💵 Cost Protection Verification

Your settings will ensure:
- ✅ Max $20/month spending (hard limit)
- ✅ ~$0.002 per PRD with caching
- ✅ Rate limiting: 5 AI requests/minute

**Verify at**: https://platform.openai.com/usage

## 🎨 Next: Deploy Frontend to Vercel

Once backend is live:

```bash
cd frontend

# Update environment
echo "NEXT_PUBLIC_API_URL=https://prism-backend.onrender.com" > .env.production

# Deploy to Vercel
npm run build
vercel --prod
```

## 🔍 Common Issues & Solutions

### "Still 503 after 10 minutes"
- Check Render logs for build errors
- Common: Missing environment variable
- Try: Manual restart in Render dashboard

### "Build failed"
- Usually: Dockerfile issue or dependency problem
- Check: Build logs in Render
- Fix: Ensure all requirements.txt packages are listed

### "Health check failing"
- Verify: PORT environment variable is 8000
- Check: All required env vars are set
- Try: Restart service

## 📱 Quick Test Commands

```bash
# Once live, test these:

# 1. Health check
curl https://prism-backend.onrender.com/health

# 2. API docs
open https://prism-backend.onrender.com/docs

# 3. Create test user (optional)
curl -X POST https://prism-backend.onrender.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "Test123!@#",
    "full_name": "Test User"
  }'
```

## 🎯 Success Checklist

- [ ] Render shows "Live" status
- [ ] Health endpoint returns 200 OK
- [ ] API docs load at /docs
- [ ] Environment variables updated
- [ ] CORS includes your frontend URL
- [ ] OpenAI billing alerts set
- [ ] First PRD generated successfully

---

**Remember**: First deployment always takes longer. Subsequent deployments will be much faster (1-2 minutes)!