# CORS Configuration Update Action Plan

## 🚨 Immediate Actions Required

### Step 1: Update Environment Variable in Render Dashboard

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click on your `prism-backend` service
3. Navigate to the **Environment** tab
4. Look for `CORS_ORIGINS` (NOT `CORS_ALLOWED_ORIGINS`)
5. Set or update the value to:
   ```
   https://prism-9z5biinym-nilukushs-projects.vercel.app,https://prism-frontend-kappa.vercel.app,http://localhost:3000,http://localhost:3100
   ```
6. Click **Save Changes**
7. Service will auto-redeploy (takes ~5-10 minutes on free tier)

### Step 2: Fix render.yaml for Future Deployments

The `render.yaml` file has been updated to use the correct environment variable name (`CORS_ORIGINS` instead of `CORS_ALLOWED_ORIGINS`).

### Step 3: Verify Configuration After Deployment

Once the service has redeployed, run these tests:

#### Quick Browser Test
Open browser console on your Vercel app and run:
```javascript
fetch('https://prism-backend-bwfx.onrender.com/health')
  .then(res => res.json())
  .then(data => console.log('Success:', data))
  .catch(err => console.error('CORS Error:', err));
```

#### Command Line Test
```bash
# Test from new production URL
curl -X GET https://prism-backend-bwfx.onrender.com/health \
  -H "Origin: https://prism-9z5biinym-nilukushs-projects.vercel.app" \
  -H "Content-Type: application/json"
```

## 📋 Configuration Details

### Current Backend CORS Implementation

The backend uses FastAPI's CORSMiddleware with these settings:
- **Allowed Origins**: Configurable via `CORS_ORIGINS` environment variable
- **Allow Credentials**: `True` (supports authenticated requests)
- **Allowed Methods**: GET, POST, PUT, DELETE, OPTIONS, PATCH
- **Allowed Headers**: * (all headers)

### Environment Variable Mapping

| Variable Name | Purpose | Current Value |
|--------------|---------|---------------|
| `CORS_ORIGINS` | Comma-separated list of allowed origins | Should include both Vercel URLs |
| `CORS_ALLOW_CREDENTIALS` | Enable credentials in CORS | `True` (default) |
| `CORS_ALLOW_METHODS` | Allowed HTTP methods | All standard methods |
| `CORS_ALLOW_HEADERS` | Allowed request headers | `*` (all) |

## 🔧 Troubleshooting

### If CORS is still not working:

1. **Check Service Logs**
   - Go to Render Dashboard → Your Service → Logs
   - Look for "CORS" or "Origin" related messages

2. **Verify Environment Variable**
   - In Render Dashboard, double-check the variable name is `CORS_ORIGINS`
   - Ensure there are no spaces in the comma-separated list
   - No quotes needed around the value

3. **Test Different Origins**
   ```bash
   # Test each origin separately
   for origin in "https://prism-9z5biinym-nilukushs-projects.vercel.app" "https://prism-frontend-kappa.vercel.app"; do
     echo "Testing $origin"
     curl -I -X OPTIONS https://prism-backend-bwfx.onrender.com/health \
       -H "Origin: $origin" \
       -H "Access-Control-Request-Method: GET"
   done
   ```

4. **Backend Health Check**
   - If the backend is down or slow, Render free tier might have spun it down
   - Access https://prism-backend-bwfx.onrender.com/health directly to wake it up

## 🎯 Expected Behavior

After configuration:
- ✅ Both Vercel URLs can make API calls
- ✅ Localhost development still works
- ✅ Authenticated requests with cookies/tokens work
- ✅ All HTTP methods (GET, POST, etc.) are allowed
- ❌ Other origins are blocked

## 📝 Files Updated

1. `/render.yaml` - Fixed environment variable name
2. `/scripts/update-cors-configuration.sh` - Script to update via CLI
3. `/scripts/test-cors-configuration.py` - Python script to test all origins
4. `/CORS_CONFIGURATION_UPDATE.md` - Detailed documentation
5. `/CORS_UPDATE_ACTION_PLAN.md` - This action plan

## 🚀 Next Steps

After updating CORS:
1. Test both frontend URLs
2. Verify authenticated endpoints work
3. Update any hardcoded backend URLs in frontend
4. Monitor for any CORS errors in production

## 📞 Support

If you encounter issues:
1. Check Render service logs
2. Verify environment variables
3. Test with the provided scripts
4. Check if backend is responding (might be sleeping on free tier)