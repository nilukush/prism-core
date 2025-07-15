# 🖱️ PRISM Quick Deployment - What to Click

## 1️⃣ Complete Neon Setup (1 minute)
You're on the right screen! Just click:
- ✅ **"Create project"** button (bottom right)
- Wait for provisioning (~30 seconds)
- Copy the connection string when it appears

## 2️⃣ Complete Upstash Setup (1 minute)
You're on the region selection screen:
1. **Click the dropdown** under "Primary Region"
2. **Select**: `Ohio, USA (us-east-2)` ← IMPORTANT!
3. **Click**: "Next" button (bottom right)
4. **Click**: "Create" on the next screen
5. Copy REST URL and Token when displayed

## 3️⃣ Quick Commands to Run

Once you have both connection strings:

```bash
# 1. Navigate to project
cd /Users/nileshkumar/gh/prism/prism-core

# 2. Set up credentials (interactive)
./scripts/setup-credentials.sh

# 3. Verify connections work
python scripts/verify-connections.py

# 4. You're ready to deploy!
```

## 4️⃣ Initialize Database (3 minutes)

In Neon SQL Editor:
1. Click "SQL Editor" in left sidebar
2. Copy the ENTIRE SQL from `DEPLOYMENT_FINAL_CONFIG.md` (Step 3)
3. Paste and click "Run"
4. Should see: "Database initialized successfully! 🎉"

## 5️⃣ Deploy Backend to Render (5 minutes)

1. Go to [render.com](https://render.com)
2. Click **"New +"** → **"Web Service"**
3. **Connect GitHub** → Select your repo
4. Fill in:
   - Name: `prism-backend`
   - Region: **Ohio (US East)** ← Match your DB!
   - Branch: `main`
   - Runtime: **Docker**
5. Click **"Advanced"** → Add environment variables
6. Click **"Create Web Service"**

## 6️⃣ Deploy Frontend to Vercel (3 minutes)

1. Go to [vercel.com](https://vercel.com)
2. Click **"Add New..."** → **"Project"**
3. **Import** your GitHub repo
4. **IMPORTANT**: Set Root Directory to `frontend`
5. Add environment variables
6. Click **"Deploy"**

## ⏱️ Total Time: ~15 minutes

That's it! You'll have PRISM running for $0/month! 🚀