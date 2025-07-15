# 🚀 Free Tier Deployment Guide for PRISM

This guide helps you deploy PRISM completely free using various cloud services' free tiers. Perfect for startups, MVPs, and personal projects.

## 📋 Table of Contents
- [Quick Start](#quick-start)
- [Recommended Stack](#recommended-stack)
- [Step-by-Step Deployment](#step-by-step-deployment)
- [Alternative Options](#alternative-options)
- [Performance Optimization](#performance-optimization)
- [Monitoring & Maintenance](#monitoring--maintenance)

## 🎯 Quick Start

**Time Required**: ~30 minutes  
**Cost**: $0  
**No Credit Card Required**: ✅

### Prerequisites
- GitHub account
- Basic command line knowledge
- PRISM repository forked/cloned

## 🏗️ Recommended Stack

| Service | Purpose | Free Tier Limits |
|---------|---------|------------------|
| **Render.com** | Backend (FastAPI) | 750 hours/month, 512MB RAM |
| **Vercel** | Frontend (Next.js) | 100GB bandwidth, unlimited sites |
| **Neon** | PostgreSQL | 3GB storage, 1GB RAM |
| **Upstash** | Redis | 10K commands/day, 256MB |
| **GitHub Actions** | CI/CD | 2000 minutes/month |

## 📖 Step-by-Step Deployment

### Step 1: Database Setup (Neon PostgreSQL)

1. **Sign up at [neon.tech](https://neon.tech)**
   - No credit card required
   - Use GitHub OAuth for quick signup

2. **Create a new project**
   ```
   Project name: prism-db
   Region: Choose closest to your users
   PostgreSQL version: 15 (latest stable)
   ```

3. **Copy your connection string**
   ```
   postgresql://username:password@host/neondb?sslmode=require
   ```

4. **Initialize database schema**
   ```bash
   # Using Neon's SQL editor or psql
   psql $DATABASE_URL < backend/scripts/init.sql
   ```

### Step 2: Redis Setup (Upstash)

1. **Sign up at [upstash.com](https://upstash.com)**
   - GitHub OAuth available
   - No credit card required

2. **Create Redis database**
   ```
   Name: prism-cache
   Region: Global (recommended)
   Type: Regional (for free tier)
   ```

3. **Get connection details**
   - Copy REST URL and token
   - Note: Upstash uses REST API, not standard Redis protocol

### Step 3: Backend Deployment (Render)

1. **Sign up at [render.com](https://render.com)**
   - Use GitHub OAuth
   - No credit card required

2. **Create Web Service**
   - Click "New +" → "Web Service"
   - Connect GitHub repository
   - Select `prism-core` repo

3. **Configure service**
   ```yaml
   Name: prism-backend
   Region: Oregon (US West)
   Branch: main
   Root Directory: ./
   Runtime: Docker
   Build Command: docker build -t prism-backend -f Dockerfile .
   Start Command: (leave blank - uses Dockerfile CMD)
   ```

4. **Environment Variables**
   ```bash
   # Database
   DATABASE_URL=postgresql://...  # From Neon
   
   # Redis (Upstash REST)
   UPSTASH_REDIS_REST_URL=https://...
   UPSTASH_REDIS_REST_TOKEN=...
   
   # Security
   SECRET_KEY=<generate-random-32-char>
   JWT_SECRET_KEY=<generate-random-32-char>
   
   # Environment
   ENVIRONMENT=production
   BACKEND_URL=https://prism-backend.onrender.com
   FRONTEND_URL=https://prism-app.vercel.app
   
   # AI (optional - for mock service)
   DEFAULT_LLM_PROVIDER=mock
   ```

5. **Create render.yaml** in project root:
   ```yaml
   services:
     - type: web
       name: prism-backend
       runtime: docker
       dockerfilePath: ./Dockerfile
       dockerContext: ./
       envVars:
         - key: DATABASE_URL
           fromDatabase:
             name: prism-db
             property: connectionString
         - key: PORT
           value: 8000
   ```

### Step 4: Frontend Deployment (Vercel)

1. **Sign up at [vercel.com](https://vercel.com)**
   - Use GitHub OAuth
   - No credit card required

2. **Import Project**
   - Click "Add New..." → "Project"
   - Import `prism-core` repository

3. **Configure Project**
   ```
   Framework Preset: Next.js
   Root Directory: ./frontend
   Build Command: npm run build
   Output Directory: .next
   Install Command: npm install
   ```

4. **Environment Variables**
   ```bash
   NEXT_PUBLIC_API_URL=https://prism-backend.onrender.com
   NEXT_PUBLIC_APP_URL=https://prism-app.vercel.app
   NEXTAUTH_URL=https://prism-app.vercel.app
   NEXTAUTH_SECRET=<generate-random-32-char>
   ```

5. **Deploy**
   - Click "Deploy"
   - Wait for build to complete (~3-5 minutes)

### Step 5: Update Backend with Frontend URL

1. Go to Render dashboard
2. Update environment variable:
   ```
   FRONTEND_URL=https://prism-app.vercel.app
   ```
3. Redeploy service

### Step 6: Configure GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy PRISM

on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Render
        env:
          RENDER_API_KEY: ${{ secrets.RENDER_API_KEY }}
        run: |
          curl -X POST \
            https://api.render.com/v1/services/${{ secrets.RENDER_SERVICE_ID }}/deploys \
            -H "Authorization: Bearer $RENDER_API_KEY" \
            -H "Content-Type: application/json" \
            -d '{"clearCache": "do_not_clear"}'

  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Vercel
        run: |
          npm i -g vercel
          vercel --prod --token=${{ secrets.VERCEL_TOKEN }}
```

## 🔄 Alternative Options

### Option 1: Railway.app (All-in-One)
- **Pros**: Single platform, easy setup
- **Cons**: $5/month credit limit
- **Best for**: Quick prototypes

### Option 2: Fly.io
- **Free tier**: 3 shared-cpu-1x VMs, 3GB storage
- **Pros**: Global deployment, persistent storage
- **Cons**: Requires credit card

### Option 3: Self-Hosted
- **Oracle Cloud**: Always free tier with 4 ARM cores
- **Google Cloud**: $300 credit for 90 days
- **AWS**: 12 months free tier

## ⚡ Performance Optimization

### 1. Handle Cold Starts

Create `frontend/src/components/ColdStartHandler.tsx`:
```typescript
import { useEffect } from 'react';

export function ColdStartHandler() {
  useEffect(() => {
    // Ping backend to prevent cold start
    const interval = setInterval(() => {
      fetch(`${process.env.NEXT_PUBLIC_API_URL}/health`)
        .catch(() => {}); // Ignore errors
    }, 5 * 60 * 1000); // Every 5 minutes

    return () => clearInterval(interval);
  }, []);

  return null;
}
```

### 2. Optimize for Free Tier Limits

**Backend optimizations:**
```python
# Use caching aggressively
from functools import lru_cache
import redis
from upstash_redis import Redis

# Initialize Upstash Redis
redis_client = Redis(
    url=settings.UPSTASH_REDIS_REST_URL,
    token=settings.UPSTASH_REDIS_REST_TOKEN
)

@lru_cache(maxsize=100)
def get_cached_data(key: str):
    return redis_client.get(key)
```

**Frontend optimizations:**
```javascript
// next.config.js
module.exports = {
  images: {
    domains: ['prism-backend.onrender.com'],
    minimumCacheTTL: 60 * 60 * 24, // 24 hours
  },
  compress: true,
  poweredByHeader: false,
}
```

### 3. Database Connection Pooling

```python
# backend/src/database.py
from sqlalchemy.pool import NullPool

# For serverless/free tier
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=NullPool,  # Don't maintain connections
    connect_args={
        "connect_timeout": 10,
        "options": "-c statement_timeout=30000"  # 30s timeout
    }
)
```

## 📊 Monitoring & Maintenance

### Free Monitoring Tools

1. **UptimeRobot** (free tier)
   - Monitor endpoints
   - Email alerts
   - Public status page

2. **Sentry** (free tier)
   - Error tracking
   - Performance monitoring
   - 5K errors/month free

3. **LogDNA** (free tier)
   - Centralized logging
   - 1 day retention
   - Search and alerts

### Health Check Endpoints

Configure monitoring for these endpoints:
- Backend: `https://prism-backend.onrender.com/health`
- Frontend: `https://prism-app.vercel.app/api/health`

## 🚨 Important Limitations

### Free Tier Constraints

1. **Render.com**
   - Services sleep after 15 min inactivity
   - 512MB RAM limit
   - No persistent storage

2. **Vercel**
   - 10 second function timeout
   - 100GB bandwidth/month
   - No websocket support

3. **Neon**
   - 3GB storage limit
   - Compute autosuspends after 5 min

4. **Upstash**
   - 10K commands/day
   - 256MB max storage

### Mitigation Strategies

1. **Use CDN**: Cloudflare free tier for assets
2. **Implement caching**: Reduce database queries
3. **Optimize images**: Use Next.js Image component
4. **Monitor usage**: Set up alerts before limits

## 🎯 Next Steps

### When to Upgrade

Consider paid tiers when:
- Daily active users > 100
- Storage needs > 3GB
- Need websockets/real-time
- Require 99.9% uptime

### Migration Path

1. **First upgrade**: Database (most critical)
2. **Second**: Backend hosting (for performance)
3. **Third**: Add CDN and monitoring
4. **Fourth**: Multi-region deployment

## 📚 Additional Resources

- [Render Docs](https://render.com/docs)
- [Vercel Docs](https://vercel.com/docs)
- [Neon Docs](https://neon.tech/docs)
- [Upstash Docs](https://docs.upstash.com)

## 🆘 Troubleshooting

### Common Issues

1. **"Application Error" on Render**
   - Check logs: Dashboard → Logs
   - Verify environment variables
   - Ensure Dockerfile builds correctly

2. **"500 Error" on Vercel**
   - Check function logs
   - Verify API URL is correct
   - Check CORS settings

3. **Database Connection Failed**
   - Verify connection string
   - Check if DB is suspended
   - Ensure SSL mode is correct

### Support Channels

- GitHub Issues: Report bugs
- Discord: Community support
- Stack Overflow: Tag with `prism-pm`

---

**Remember**: This setup is perfect for MVPs and early-stage projects. As your startup grows, gradually migrate to paid tiers for better performance and reliability.

Good luck with your deployment! 🚀