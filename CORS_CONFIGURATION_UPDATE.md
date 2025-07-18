# CORS Configuration Update for PRISM Backend

## Overview

This document provides instructions for updating the CORS configuration on the PRISM backend to support multiple frontend URLs on Vercel.

## Current Setup

- **Backend URL**: https://prism-backend-bwfx.onrender.com
- **Frontend URLs**:
  - New Production: https://prism-9z5biinym-nilukushs-projects.vercel.app
  - Old Domain: https://prism-frontend-kappa.vercel.app
  - Local Development: http://localhost:3000

## Required Changes

### 1. Environment Variable Update

The backend uses the `CORS_ORIGINS` environment variable (not `CORS_ALLOWED_ORIGINS`). Update this in Render dashboard:

```
CORS_ORIGINS=https://prism-9z5biinym-nilukushs-projects.vercel.app,https://prism-frontend-kappa.vercel.app,http://localhost:3000,http://localhost:3100
```

### 2. Update via Render Dashboard

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Select the `prism-backend` service
3. Navigate to the **Environment** tab
4. Find or add `CORS_ORIGINS` variable
5. Set the value to include all allowed origins (comma-separated)
6. Click **Save Changes**
7. The service will automatically redeploy

### 3. Alternative: Use Render CLI

If you have Render CLI installed:

```bash
# Run the update script
./scripts/update-cors-configuration.sh

# Or manually:
render env:set CORS_ORIGINS="https://prism-9z5biinym-nilukushs-projects.vercel.app,https://prism-frontend-kappa.vercel.app,http://localhost:3000,http://localhost:3100" --service prism-backend
```

## Enterprise-Grade CORS Configuration

The backend already implements enterprise-grade CORS features:

1. **Configurable Origins**: Supports multiple origins via comma-separated list
2. **Credentials Support**: `allow_credentials=True` for authenticated requests
3. **Method Control**: Allows GET, POST, PUT, DELETE, OPTIONS, PATCH
4. **Header Control**: Allows all headers with `["*"]`
5. **Security Middleware**: CORS is applied after security checks

### Security Best Practices Implemented

- ✅ Origin validation (only specified origins allowed)
- ✅ Credentials support for authenticated requests
- ✅ Proper preflight handling (OPTIONS method)
- ✅ Applied after DDoS and rate limiting middleware
- ✅ Works with TrustedHost middleware in production

## Testing the Configuration

### 1. Test CORS Preflight Request

```bash
# Test from new production URL
curl -H 'Origin: https://prism-9z5biinym-nilukushs-projects.vercel.app' \
     -H 'Access-Control-Request-Method: GET' \
     -H 'Access-Control-Request-Headers: X-Requested-With' \
     -X OPTIONS https://prism-backend-bwfx.onrender.com/health -v

# Expected response headers:
# Access-Control-Allow-Origin: https://prism-9z5biinym-nilukushs-projects.vercel.app
# Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS, PATCH
# Access-Control-Allow-Headers: *
# Access-Control-Allow-Credentials: true
```

### 2. Test Actual Request

```bash
# Test GET request
curl -H 'Origin: https://prism-9z5biinym-nilukushs-projects.vercel.app' \
     https://prism-backend-bwfx.onrender.com/health -v

# Test from old domain
curl -H 'Origin: https://prism-frontend-kappa.vercel.app' \
     https://prism-backend-bwfx.onrender.com/health -v
```

### 3. Browser Console Test

From your frontend application console:

```javascript
// Test from browser console
fetch('https://prism-backend-bwfx.onrender.com/health', {
  method: 'GET',
  credentials: 'include',
  headers: {
    'Content-Type': 'application/json',
  }
})
.then(response => response.json())
.then(data => console.log('Success:', data))
.catch(error => console.error('Error:', error));
```

## Monitoring and Troubleshooting

### Check Current CORS Configuration

1. SSH into your Render service (if available)
2. Check environment variables:
   ```bash
   echo $CORS_ORIGINS
   ```

### Common Issues and Solutions

1. **403 Forbidden on OPTIONS**
   - Ensure `OPTIONS` is in `CORS_ALLOW_METHODS`
   - Check if origin is in allowed list

2. **Missing CORS Headers**
   - Verify environment variable name is `CORS_ORIGINS`
   - Check if service has redeployed after changes

3. **Credentials Error**
   - Ensure `CORS_ALLOW_CREDENTIALS` is `True`
   - Frontend must send `credentials: 'include'`

### Logs to Check

Monitor Render logs for CORS-related issues:
```bash
# Look for CORS initialization
grep "CORS" render-logs.txt

# Check for origin validation errors
grep "Origin" render-logs.txt
```

## Production Considerations

1. **Performance**: CORS checks are lightweight and won't impact performance
2. **Security**: Only allow specific origins, never use `*` in production
3. **Monitoring**: Set up alerts for CORS errors in your monitoring system
4. **Documentation**: Keep CORS origins documented in your deployment guide

## Next Steps

After updating CORS configuration:

1. ✅ Verify both Vercel URLs can access the backend
2. ✅ Test authenticated endpoints with credentials
3. ✅ Update frontend environment variables if needed
4. ✅ Document any custom headers your app uses
5. ✅ Set up monitoring for CORS errors

## References

- [MDN CORS Documentation](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [FastAPI CORS Middleware](https://fastapi.tiangolo.com/tutorial/cors/)
- [Render Environment Variables](https://render.com/docs/environment-variables)