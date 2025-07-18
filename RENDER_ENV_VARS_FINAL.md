# 🔧 Render Environment Variables - Final Configuration

## 🚨 Critical Issues Resolved

1. **CORS Errors** - API calls blocked from frontend
2. **Auto-Activation** - Users need manual activation
3. **User Experience** - Registration to login flow broken

## 📋 Required Environment Variables for Render

Copy and paste these EXACTLY into your Render Environment Variables:

```bash
# Database (Already configured)
DATABASE_URL=your-neon-postgres-url
REDIS_URL=your-upstash-redis-url

# Security
SECRET_KEY=your-existing-secret-key
JWT_SECRET_KEY=your-existing-jwt-key

# CORS - CRITICAL FOR API ACCESS
CORS_ORIGINS=https://prism-frontend-kappa.vercel.app,https://prism-9z5biinym-nilukushs-projects.vercel.app

# Auto-Activation Settings
AUTO_ACTIVATE_USERS=true
EMAIL_VERIFICATION_REQUIRED=false
SKIP_EMAIL_VERIFICATION=true

# AI Provider Keys (if you have them)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# Optional but recommended
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO
RATE_LIMIT_ENABLED=true
```

## 🎯 Step-by-Step Instructions

### 1. Open Render Dashboard
- Go to: https://dashboard.render.com/
- Click on your service: **prism-backend**

### 2. Navigate to Environment
- Click **"Environment"** in the left sidebar
- You'll see existing variables

### 3. Add/Update Variables
Add these ONE BY ONE (Render doesn't support bulk paste):

| Variable | Value |
|----------|-------|
| `CORS_ORIGINS` | `https://prism-frontend-kappa.vercel.app,https://prism-9z5biinym-nilukushs-projects.vercel.app` |
| `AUTO_ACTIVATE_USERS` | `true` |
| `EMAIL_VERIFICATION_REQUIRED` | `false` |
| `SKIP_EMAIL_VERIFICATION` | `true` |

### 4. Save and Deploy
- Click **"Save Changes"**
- Service will automatically redeploy
- Wait 3-5 minutes for deployment

## ✅ Verification Steps

### 1. Test CORS (After deployment completes)
```bash
# Should return access-control-allow-origin header
curl -I https://prism-backend-bwfx.onrender.com/health \
  -H "Origin: https://prism-frontend-kappa.vercel.app"
```

### 2. Test Complete User Flow
```bash
# 1. Register
curl -X POST https://prism-backend-bwfx.onrender.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testflow",
    "email": "testflow@example.com",
    "password": "Test123456@",
    "confirm_password": "Test123456@"
  }'

# 2. Login immediately (no activation needed!)
curl -X POST https://prism-backend-bwfx.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testflow@example.com&password=Test123456@"
```

### 3. Test Frontend
1. Go to: https://prism-frontend-kappa.vercel.app
2. Register new account
3. Login immediately
4. Create project/organization (should work now!)

## 🎉 Expected Results

After applying these environment variables:

1. **CORS Fixed** ✅
   - No more "blocked by CORS policy" errors
   - API calls work from frontend
   - Can create projects and organizations

2. **Auto-Activation Working** ✅
   - Register → Login works immediately
   - No manual activation needed
   - Seamless user experience

3. **Full Functionality** ✅
   - Create organizations
   - Create projects
   - All API endpoints accessible

## 🔍 Troubleshooting

### Still getting CORS errors?
- Make sure you included BOTH Vercel URLs in CORS_ORIGINS
- Check for typos (no spaces after commas)
- Wait for full deployment to complete

### Users still need activation?
- Verify AUTO_ACTIVATE_USERS is set to `true` (lowercase)
- Check deployment logs for the new code
- Try registering a completely new user

### API returns 401/403?
- Clear browser cookies/cache
- Try incognito mode
- Re-login to get fresh JWT token

## 📝 Summary

The code changes are already deployed. You just need to:
1. Add the 4 environment variables to Render
2. Wait for redeployment
3. Enjoy seamless user registration → login flow!

---

**Note**: These settings prioritize user experience over strict security. For production with real users, implement proper email verification later.