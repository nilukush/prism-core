# 🔧 PRISM Free Tier Deployment Troubleshooting

This guide helps you resolve common issues when deploying PRISM on free tier services.

## 🚨 Common Issues & Solutions

### 1. Render Backend Issues

#### ❌ "Application failed to respond"
**Symptoms**: 
- Render shows "Deploy failed" 
- Logs show "exec /app/start.sh: no such file or directory"

**Solution**:
```bash
# Check Dockerfile exists in root
ls -la Dockerfile

# Ensure render.yaml specifies Docker runtime
runtime: docker

# Check build logs in Render dashboard
# Look for Docker build errors
```

#### ❌ "Port binding failed"
**Symptoms**: 
- "Error: bind: address already in use"
- Backend crashes immediately

**Solution**:
```bash
# Add to Render environment variables:
PORT=8000

# Or use dynamic port in backend:
# backend/src/main.py
port = int(os.getenv("PORT", 8000))
```

#### ❌ Database connection timeout
**Symptoms**:
- "could not connect to server: Connection timed out"
- "SSL SYSCALL error: EOF detected"

**Solution**:
1. Check DATABASE_URL format:
   ```
   postgresql://user:pass@host/db?sslmode=require
   ```
2. Ensure Neon database is active (not suspended)
3. Add connection parameters:
   ```python
   # backend/src/database.py
   engine = create_engine(
       DATABASE_URL,
       connect_args={
           "connect_timeout": 10,
           "options": "-c statement_timeout=30000"
       }
   )
   ```

### 2. Vercel Frontend Issues

#### ❌ "Module not found" during build
**Symptoms**:
- Build fails with missing dependencies
- "Cannot find module 'xyz'"

**Solution**:
```bash
# Ensure package.json is in frontend/
cd frontend
npm install
npm run build  # Test locally first

# Check Vercel root directory setting:
Root Directory: frontend  # Not ./frontend or /frontend
```

#### ❌ API calls return CORS errors
**Symptoms**:
- "Access to fetch at ... from origin ... has been blocked by CORS"
- Frontend can't communicate with backend

**Solution**:
1. Update backend CORS settings:
   ```bash
   # In Render environment variables:
   CORS_ALLOWED_ORIGINS=https://your-app.vercel.app,https://www.your-app.vercel.app
   ```

2. Restart Render service after updating

3. Check frontend API URL:
   ```bash
   # frontend/.env.production
   NEXT_PUBLIC_API_URL=https://prism-backend.onrender.com  # No trailing slash
   ```

#### ❌ "Invalid environment variables"
**Symptoms**:
- Build succeeds but app shows errors
- "Missing required environment variable"

**Solution**:
```bash
# In Vercel dashboard:
1. Go to Settings → Environment Variables
2. Add all from frontend/.env.production
3. Redeploy (Deployments → ... → Redeploy)

# Required variables:
NEXT_PUBLIC_API_URL
NEXT_PUBLIC_APP_URL
NEXTAUTH_URL
NEXTAUTH_SECRET
```

### 3. Database (Neon) Issues

#### ❌ "Database does not exist"
**Symptoms**:
- Migration fails
- "FATAL: database 'xyz' does not exist"

**Solution**:
1. Check Neon dashboard for correct database name
2. Update DATABASE_URL to match
3. Create database if missing:
   ```sql
   -- In Neon SQL editor
   CREATE DATABASE prism;
   ```

#### ❌ Migrations fail
**Symptoms**:
- "alembic.util.exc.CommandError"
- "Can't locate revision identified by"

**Solution**:
```bash
# From Render shell:
cd backend

# Reset migrations (careful in production!)
rm -rf alembic/versions/*

# Create fresh migration
alembic revision --autogenerate -m "Initial"
alembic upgrade head
```

### 4. Redis (Upstash) Issues

#### ❌ "NOAUTH Authentication required"
**Symptoms**:
- Redis operations fail
- Session storage not working

**Solution**:
1. Check Upstash credentials:
   ```bash
   # Must use REST URL, not Redis URL
   UPSTASH_REDIS_REST_URL=https://xxx.upstash.io  # NOT redis://
   UPSTASH_REDIS_REST_TOKEN=AX3sACQg...
   ```

2. Test connection:
   ```python
   # From Render shell
   python -c "
   import httpx
   url = 'YOUR_UPSTASH_URL'
   token = 'YOUR_TOKEN'
   headers = {'Authorization': f'Bearer {token}'}
   response = httpx.post(url, json=['PING'], headers=headers)
   print(response.json())  # Should show {'result': 'PONG'}
   "
   ```

### 5. Authentication Issues

#### ❌ "Invalid token" or "Unauthorized"
**Symptoms**:
- Can't login
- Get logged out immediately
- API returns 401

**Solution**:
1. Ensure secrets match:
   ```bash
   # Backend (Render)
   JWT_SECRET_KEY=same-value-here

   # Frontend (Vercel)
   NEXTAUTH_SECRET=different-value-here  # Different from JWT!
   ```

2. Clear browser data:
   - Cookies for your domain
   - Local storage
   - Try incognito mode

3. Check token expiration:
   ```python
   # backend/src/core/config.py
   ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Increase if needed
   ```

#### ❌ Default login not working
**Symptoms**:
- admin@example.com doesn't work
- "Invalid credentials"

**Solution**:
```python
# From Render shell, recreate user:
cd backend
python -c "
from src.database import SessionLocal
from src.models.user import User
from src.core.security import hash_password

db = SessionLocal()
# Delete existing
db.query(User).filter(User.email=='admin@example.com').delete()
# Create new
admin = User(
    email='admin@example.com',
    username='admin',
    password_hash=hash_password('Admin123!@#'),
    full_name='Admin User',
    is_active=True,
    is_superuser=True,
    email_verified=True
)
db.add(admin)
db.commit()
print('Admin user recreated!')
"
```

### 6. Performance Issues

#### ❌ Backend takes 30-60 seconds to respond
**Symptoms**:
- First request after idle is very slow
- Subsequent requests are fast

**Solution**:
1. This is normal for Render free tier (cold starts)
2. Set up warm-up ping:
   ```bash
   # Use UptimeRobot (free)
   # Monitor: https://prism-backend.onrender.com/health
   # Interval: 14 minutes
   ```

3. Add client-side handling:
   ```javascript
   // Show loading state
   setLoading(true);
   setLoadingMessage("Waking up the server...");
   ```

#### ❌ "Rate limit exceeded"
**Symptoms**:
- Upstash returns 429 errors
- Redis operations fail after ~10k

**Solution**:
1. Check daily usage in Upstash dashboard
2. Implement caching fallback:
   ```python
   try:
       result = await redis.get(key)
   except Exception:
       # Fallback to database
       result = await get_from_db(key)
   ```

3. Reduce cache usage:
   - Shorter TTLs
   - Cache only critical data
   - Batch operations

### 7. Deployment Script Issues

#### ❌ "No such file or directory"
**Symptoms**:
- Scripts won't run
- "Permission denied"

**Solution**:
```bash
# Make executable
chmod +x scripts/*.sh

# Run from correct directory
cd /path/to/prism-core
./scripts/deploy-to-free-tier.sh
```

#### ❌ Environment file issues
**Symptoms**:
- "No .env.production file"
- Variables not loading

**Solution**:
```bash
# Create manually if needed
cp .env.example .env.production
# Edit with your values

# Check file permissions
ls -la .env.production  # Should be readable
```

## 🔍 Debugging Tools

### 1. Check Service Health
```bash
# Backend health
curl -v https://your-backend.onrender.com/health

# Frontend health  
curl -v https://your-app.vercel.app

# Database connection
psql $DATABASE_URL -c "SELECT 1"

# Redis connection
curl -H "Authorization: Bearer $TOKEN" \
  -X POST $UPSTASH_URL \
  -d '["PING"]'
```

### 2. View Logs
- **Render**: Dashboard → Services → Logs
- **Vercel**: Dashboard → Functions → Logs
- **Neon**: Dashboard → Monitoring
- **Upstash**: Dashboard → Logs

### 3. Test Endpoints
```bash
# Test auth
curl -X POST https://your-backend.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=Admin123!@#"

# Test CORS
curl -H "Origin: https://your-app.vercel.app" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: X-Requested-With" \
  -X OPTIONS https://your-backend.onrender.com/api/v1/health
```

## 🆘 Getting Help

### Before Asking for Help
1. Check all environment variables are set correctly
2. Verify services are running (not suspended)
3. Look at logs for specific errors
4. Try the solutions above

### Where to Get Help
1. **GitHub Issues**: For bugs and feature requests
2. **Discussions**: For questions and community help
3. **Service Support**:
   - Render: https://render.com/docs
   - Vercel: https://vercel.com/support
   - Neon: https://neon.tech/docs
   - Upstash: https://docs.upstash.com

### Providing Information
When asking for help, include:
- [ ] Error messages (full text)
- [ ] Service logs (relevant parts)
- [ ] Environment (free tier services)
- [ ] What you've tried
- [ ] Expected vs actual behavior

## 🎯 Prevention Tips

1. **Test Locally First**
   ```bash
   docker-compose up
   npm run dev
   ```

2. **Check Free Tier Limits**
   - Monitor usage dashboards
   - Set up alerts
   - Plan for scaling

3. **Keep Backups**
   - Database exports
   - Environment configs
   - Deployment notes

4. **Document Changes**
   - Track what works
   - Note custom configurations
   - Update team docs

---

Remember: Free tier services have limitations. Most issues come from these limits, not bugs. Plan accordingly!