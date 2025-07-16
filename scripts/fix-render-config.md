# Fix Render Configuration Issues

Based on the deployment logs, here are the critical issues that need to be fixed in your Render dashboard:

## 1. DATABASE_URL Format Issue

**Current Error**: `database "neondb&channel_binding=require" does not exist`

The DATABASE_URL appears to have incorrect formatting. The error suggests the URL has `&channel_binding=require` as part of the database name instead of query parameters.

**Fix in Render Dashboard**:
1. Go to your service dashboard: https://dashboard.render.com/web/srv-d1r6j47fte5s73cnonqg
2. Click on "Environment" tab
3. Find `DATABASE_URL` and edit it
4. Ensure it follows this format:
   ```
   postgresql://username:password@host:port/database?sslmode=require
   ```
   Note the `?` before sslmode, not `&`

**Example correct format**:
```
postgresql://nilukush:your_password@ep-example.region.aws.neon.tech:5432/neondb?sslmode=require
```

## 2. Redis Connection Issue

**Current Error**: `Error 111 connecting to localhost:6379. Connection refused.`

The app is trying to connect to localhost for Redis, which won't work in production.

**Fix in Render Dashboard**:
Add these environment variables:
1. `UPSTASH_REDIS_REST_URL` - Get from your Upstash dashboard
2. `UPSTASH_REDIS_REST_TOKEN` - Get from your Upstash dashboard

**Alternative**: If you have a standard Redis instance:
```
REDIS_URL=redis://default:password@your-redis-host:6379
```

## 3. Missing Required Environment Variables

Add these critical variables:
- `SECRET_KEY` - Generate a secure random string
- `JWT_SECRET_KEY` - Generate another secure random string

## 4. Optional Environment Variables

These are not critical but recommended:
- `QDRANT_HOST` - If using Qdrant for vector storage
- `QDRANT_PORT` - Usually 6333
- `QDRANT_API_KEY` - If Qdrant requires auth
- `OPENAI_API_KEY` - For AI features
- `ANTHROPIC_API_KEY` - For Claude integration

## Quick Verification

After updating environment variables:
1. Trigger a manual deploy in Render
2. Check logs with: `render logs -r srv-d1r6j47fte5s73cnonqg -o text --tail`
3. Look for successful connection messages instead of errors

## Generate Secret Keys

To generate secure secret keys, run:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```