# Authentication Troubleshooting Guide

## Common Issues and Solutions

### 1. 401 Unauthorized Errors

**Symptoms:**
- API calls returning 401 despite having a valid token
- "Invalid authentication credentials" errors
- Token expiration errors

**Root Causes:**
- Access token has expired (default: 30 minutes)
- Refresh token mechanism failing
- Token not being included in API requests
- Backend expecting different token format

**Solutions:**

1. **Check Token Status:**
   ```bash
   # Use the debug endpoint to check token validity
   curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/api/v1/auth/debug/token
   ```

2. **Force Token Refresh:**
   - Sign out and sign back in
   - Clear browser storage and re-authenticate
   
3. **Check Token Expiry:**
   - Tokens expire after 30 minutes by default
   - Refresh tokens expire after 30 days
   - The frontend should automatically refresh tokens before expiry

### 2. Rate Limiting (429) Errors

**Symptoms:**
- "Too Many Requests" errors
- IP being blocked
- Suspicious pattern detection warnings

**Root Causes:**
- Exceeding rate limits (10/sec, 100/min, 1000/hr)
- DDoS protection triggering false positives
- Multiple failed authentication attempts

**Solutions:**

1. **Clear Rate Limiting for Specific IP:**
   ```bash
   # Clear rate limiting for a specific IP
   docker exec prism-redis redis-cli -a redis_password \
     DEL "rate_limit:token_bucket:ip:YOUR_IP" \
     "ddos_pattern:/api/v1/ai/generate:YOUR_IP"
   ```

2. **Clear All Rate Limiting:**
   ```bash
   # Run the clear auth cache script
   cd backend
   python scripts/clear_auth_cache.py YOUR_IP
   ```

3. **Check Current Rate Limit Status:**
   ```bash
   # List all rate limit keys
   docker exec prism-redis redis-cli -a redis_password \
     KEYS "rate_limit:*"
   ```

### 3. Refresh Token Errors

**Symptoms:**
- "Invalid or reused refresh token" errors
- Token family revocation
- Authentication loops

**Root Causes:**
- Multiple tabs/windows trying to refresh simultaneously
- Race conditions in token rotation
- Stale refresh tokens being reused

**Solutions:**

1. **Clear All Sessions:**
   - Sign out from all devices/tabs
   - Clear browser storage
   - Sign in again in a single tab

2. **Handle Race Conditions:**
   - The backend now has a 5-second grace period for race conditions
   - Frontend uses a singleton refresh manager to prevent concurrent refreshes

3. **Debug Token Families:**
   ```bash
   # Check refresh token families in Redis
   docker exec prism-redis redis-cli -a redis_password \
     KEYS "refresh_token:family:*"
   ```

## Architecture Overview

### Token Flow

1. **Login:**
   - User provides credentials
   - Backend validates and returns:
     - Access token (30 min expiry)
     - Refresh token (30 day expiry)
   - Tokens stored in NextAuth session

2. **API Requests:**
   - Frontend adds `Authorization: Bearer <access_token>` header
   - Backend validates token on each request
   - Returns 401 if token invalid/expired

3. **Token Refresh:**
   - Frontend detects token expiry (5 min before actual expiry)
   - Sends refresh token to `/api/v1/auth/refresh`
   - Backend validates refresh token and returns new token pair
   - Frontend updates session with new tokens

### Security Features

1. **Refresh Token Rotation:**
   - Each refresh token can only be used once
   - New refresh token issued on each refresh
   - Entire token family revoked on reuse detection

2. **Token Blacklist:**
   - Revoked tokens stored in memory
   - Checked on each request
   - Cleaned up after expiry

3. **Rate Limiting:**
   - Token bucket algorithm for burst protection
   - Sliding window for accurate limiting
   - DDoS pattern detection

## Debugging Steps

1. **Check Logs:**
   ```bash
   # View backend logs
   tail -f logs/prism.log | grep -E "(auth|token|jwt)"
   
   # Check for specific errors
   grep "jwt_decode_error\|refresh_token" logs/prism.log
   ```

2. **Test Authentication Flow:**
   ```bash
   # 1. Login
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=user@example.com&password=password"
   
   # 2. Use access token
   curl -H "Authorization: Bearer ACCESS_TOKEN" \
     http://localhost:8000/api/v1/auth/me
   
   # 3. Refresh token
   curl -X POST http://localhost:8000/api/v1/auth/refresh \
     -H "Content-Type: application/json" \
     -d '{"refresh_token": "REFRESH_TOKEN"}'
   ```

3. **Monitor Redis:**
   ```bash
   # Monitor Redis commands in real-time
   docker exec prism-redis redis-cli -a redis_password MONITOR
   ```

## Prevention

1. **Frontend Best Practices:**
   - Use the auth interceptor for all API calls
   - Implement proper error handling for 401s
   - Don't store tokens in localStorage (use secure cookies)
   - Handle token refresh gracefully

2. **Backend Configuration:**
   - Adjust token expiry times if needed
   - Configure rate limits appropriately
   - Monitor for suspicious patterns
   - Implement proper logging

3. **Production Considerations:**
   - Use Redis-backed token store
   - Implement distributed rate limiting
   - Add monitoring and alerting
   - Regular security audits

## Emergency Actions

If authentication is completely broken:

1. **Clear All Auth Data:**
   ```bash
   # Clear Redis
   docker exec prism-redis redis-cli -a redis_password FLUSHDB
   
   # Restart backend
   docker compose restart backend
   
   # Clear browser data
   # In browser: Settings > Privacy > Clear browsing data
   ```

2. **Reset User Password:**
   ```bash
   # Connect to database and update user password
   docker exec -it prism-postgres psql -U prism -d prism
   
   # In psql:
   UPDATE users SET password_hash = 'NEW_HASH' WHERE email = 'user@example.com';
   ```

3. **Disable Rate Limiting (temporary):**
   - Comment out rate limiting middleware in backend
   - Restart backend service
   - Re-enable after fixing issue

## Contact

For persistent issues:
1. Check GitHub issues
2. Review recent code changes
3. Contact the development team with:
   - Error messages
   - Log excerpts
   - Steps to reproduce
   - Environment details