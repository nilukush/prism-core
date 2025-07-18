# 🧪 Quick CORS Test

After updating the CORS_ORIGINS on Render, test from your browser console:

## Test from New URL
Visit: https://prism-9z5biinym-nilukushs-projects.vercel.app

Open browser console (F12) and run:
```javascript
fetch('https://prism-backend-bwfx.onrender.com/api/v1/health')
  .then(res => res.json())
  .then(data => console.log('✅ CORS Working!', data))
  .catch(err => console.error('❌ CORS Failed:', err));
```

## Test from Old URL
Visit: https://prism-frontend-kappa.vercel.app

Run the same test:
```javascript
fetch('https://prism-backend-bwfx.onrender.com/api/v1/health')
  .then(res => res.json())
  .then(data => console.log('✅ CORS Working!', data))
  .catch(err => console.error('❌ CORS Failed:', err));
```

## Expected Result
You should see: `✅ CORS Working! {status: "ok", message: "PRISM API is running"}`

## If CORS Fails
1. Check if backend is awake (free tier sleeps after 15 min)
2. Wait 2-3 minutes for Render redeploy
3. Try again