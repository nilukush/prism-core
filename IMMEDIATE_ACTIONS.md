# 🚨 IMMEDIATE ACTIONS REQUIRED

## 1. Fix Vercel RIGHT NOW (2 minutes)

### Go to Vercel Dashboard and Update:

**Build & Development Settings:**
- **Build Command**: `npm run build` ❌ ~~cd frontend && npm run build~~
- **Install Command**: `npm install` ❌ ~~cd frontend && npm install~~
- **Output Directory**: `.next` ❌ ~~frontend/.next~~

### Why This Will Work:
- Vercel already navigates to `frontend` (your root directory)
- No need for `cd frontend` in commands
- Output is relative to the root directory you set

## 2. Check Render Dashboard NOW

### Go to: https://dashboard.render.com
1. Click on **prism-backend-bwfx**
2. Go to **Logs** tab
3. Look for the LATEST error

### Most Common Fixes:

**A. If you see "ModuleNotFoundError: psycopg2"**
- Our code fix was pushed but may not have deployed
- Click **Manual Deploy** → **Clear build cache & deploy**

**B. If you see "Error: PORT is not defined"**
- Go to **Environment** tab
- Add: `PORT=8000`
- Save (auto-restarts)

**C. If you see database connection errors**
- Check DATABASE_URL in Environment
- Make sure it starts with your Neon connection string

## 3. Quick Test Commands

```bash
# Test if backend is up (run this now)
curl -I https://prism-backend-bwfx.onrender.com/health

# Monitor deployment progress
./scripts/monitor-render-deployment.sh

# Once backend is up, test API
curl https://prism-backend-bwfx.onrender.com/docs
```

## Timeline

1. **Vercel Fix**: Immediate after you update settings
2. **Render Fix**: 
   - If just PORT missing: 2-3 minutes
   - If needs rebuild: 5-7 minutes

## 🎯 SUCCESS = Both Show Green

✅ **Render**: Returns `{"status":"healthy"}`
✅ **Vercel**: Build completes without errors

---

**DO THESE NOW:**
1. Open Vercel → Remove "cd frontend" from commands
2. Open Render → Check logs for specific error
3. Add PORT=8000 if missing

The fixes are simple - just need the right settings!