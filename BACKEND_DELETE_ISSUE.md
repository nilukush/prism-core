# Backend DELETE Endpoint Issue Analysis

## 🔴 Current Status

The backend DELETE endpoint is returning:
- **307 Temporary Redirect** - This suggests a URL routing issue
- **401 Unauthorized** - When proper auth headers are sent

## 📊 Root Causes

### 1. Trailing Slash Redirect (307)
The backend is redirecting `/api/v1/organizations/1` to `/api/v1/organizations/1/`
This is common with FastAPI when trailing slashes don't match.

### 2. JWT Token Format Issue
Backend logs show: `"error": "Not enough segments", "event": "jwt_decode_error"`
This happens when:
- Token is malformed or truncated
- Wrong token is being sent (localStorage vs NextAuth session)
- Token contains unexpected characters

### 3. Authorization Header Format
The frontend was mixing two authentication methods:
- `localStorage.getItem('token')` - Old method
- NextAuth session tokens - Current method

## ✅ Fixes Applied

### Frontend (Now Using Correct Auth)
1. **Organizations Page**: Now uses `api.organizations.delete()` which handles auth
2. **Fix Org Modal**: Updated to use API client
3. **Removed**: Direct localStorage token access

### Backend (Needs Verification)
The DELETE endpoint should accept both:
- `/api/v1/organizations/{id}` (without trailing slash)
- `/api/v1/organizations/{id}/` (with trailing slash)

## 🧪 Testing the Fix

### 1. Check Token Format
```javascript
// In browser console
const session = await (await fetch('/api/auth/session')).json()
console.log('Session token:', session.accessToken)
```

### 2. Test DELETE Endpoint Directly
```bash
# Get token from session (not localStorage)
TOKEN="your-session-token"

# Test without trailing slash
curl -X DELETE https://prism-backend-bwfx.onrender.com/api/v1/organizations/1 \
  -H "Authorization: Bearer $TOKEN" \
  -v

# Test with trailing slash
curl -X DELETE https://prism-backend-bwfx.onrender.com/api/v1/organizations/1/ \
  -H "Authorization: Bearer $TOKEN" \
  -v
```

## 🔍 Debugging Steps

1. **Check Session Token**:
   - Open DevTools > Network tab
   - Look for requests with Authorization header
   - Verify it starts with "Bearer " and has valid JWT

2. **Verify Backend Logs**:
   - Look for "jwt_decode_error" entries
   - Check if token is being received correctly

3. **Test with API Client**:
   - The API client handles auth correctly
   - If it still fails, the issue is backend-side

## 💡 Quick Fix Options

### Option 1: Force Backend Redeploy
```bash
# In Render dashboard
Manual Deploy > Clear build cache > Deploy
```

### Option 2: Use SQL Deletion
```sql
DELETE FROM organizations WHERE id = 1;
```

### Option 3: Check Backend Route Definition
The route should be defined as:
```python
@router.delete("/{organization_id}")  # No trailing slash
# or
@router.delete("/{organization_id}/")  # With trailing slash
```

## 📝 Expected Behavior

When working correctly:
1. DELETE request sent with session token
2. Backend validates JWT and checks permissions
3. Returns 204 No Content on success
4. UI updates optimistically
5. Redirects if no orgs left