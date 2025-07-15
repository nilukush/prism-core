# PRISM Free Tier Deployment Architecture

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                           User's Browser                             │
│                                                                     │
│  1. User visits: https://prism-app.vercel.app                     │
│  2. Frontend loads from Vercel CDN                                │
│  3. Makes API calls to backend                                    │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Vercel (Frontend)                           │
│                                                                     │
│  • Next.js 14 Application                                          │
│  • Static Generation + Server Components                           │
│  • Global CDN Distribution                                         │
│  • Automatic HTTPS                                                │
│  • Environment Variables:                                          │
│    - NEXT_PUBLIC_API_URL → Render Backend                         │
│    - NEXTAUTH_SECRET → Session Security                           │
│                                                                     │
│  Free Tier: 100GB bandwidth, unlimited deployments                │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼ API Calls (HTTPS)
┌─────────────────────────────────────────────────────────────────────┐
│                         Render (Backend)                            │
│                                                                     │
│  • FastAPI Application (Python 3.11)                              │
│  • Docker Container Deployment                                     │
│  • Auto-scaling (sleeps after 15 min)                            │
│  • Environment Variables:                                          │
│    - DATABASE_URL → Neon PostgreSQL                              │
│    - UPSTASH_REDIS_* → Redis Cache                               │
│    - JWT_SECRET_KEY → Authentication                             │
│                                                                     │
│  Free Tier: 750 hours/month, 512MB RAM                           │
└─────────────────────────────────────────────────────────────────────┘
                    │                                    │
                    ▼                                    ▼
┌─────────────────────────────┐      ┌─────────────────────────────┐
│      Neon (PostgreSQL)      │      │      Upstash (Redis)        │
│                             │      │                             │
│  • Serverless PostgreSQL    │      │  • Serverless Redis         │
│  • Auto-suspend/resume      │      │  • REST API Interface       │
│  • Point-in-time recovery   │      │  • Global replication       │
│  • Connection pooling       │      │  • Used for:                │
│                             │      │    - Session storage        │
│  Stores:                    │      │    - Rate limiting          │
│  - Users & Organizations    │      │    - Caching                │
│  - Projects & Documents     │      │                             │
│  - AI Generation History    │      │  Free: 10k commands/day     │
│                             │      │        256MB storage        │
│  Free: 3GB storage          │      └─────────────────────────────┘
│        1GB RAM (shared)     │
└─────────────────────────────┘
```

## 🔄 Request Flow

### 1. User Authentication Flow
```
Browser → Vercel → NextAuth → Render API → JWT Generation
                                    ↓
                              Validate with DB
                                    ↓
                              Store session in Redis
                                    ↓
                              Return JWT to Frontend
```

### 2. PRD Generation Flow
```
Browser → Vercel → API Request → Render Backend
                                       ↓
                                 Check Redis Cache
                                       ↓
                                 Generate with AI
                                       ↓
                                 Store in PostgreSQL
                                       ↓
                                 Cache in Redis
                                       ↓
                                 Return to Frontend
```

## 🚀 Deployment Steps Overview

### Phase 1: Database & Cache Setup
1. **Neon**: Create PostgreSQL database
2. **Upstash**: Create Redis instance
3. Record connection strings

### Phase 2: Backend Deployment
1. **Render**: Deploy Docker container
2. Configure environment variables
3. Run database migrations
4. Verify health endpoint

### Phase 3: Frontend Deployment
1. **Vercel**: Import repository
2. Set build configuration
3. Add environment variables
4. Deploy and get URL

### Phase 4: Integration
1. Update CORS settings
2. Test authentication
3. Verify all features
4. Set up monitoring

## 🔐 Security Considerations

### Environment Variables
```
Backend (Render):
├── DATABASE_URL          # PostgreSQL connection
├── UPSTASH_REDIS_*       # Redis credentials
├── SECRET_KEY            # App encryption
├── JWT_SECRET_KEY        # Token signing
└── CORS_ALLOWED_ORIGINS  # Frontend URL

Frontend (Vercel):
├── NEXT_PUBLIC_API_URL   # Backend URL (public)
├── NEXTAUTH_URL          # App URL
└── NEXTAUTH_SECRET       # Session encryption
```

### Network Security
- All services use HTTPS/TLS
- Database requires SSL connection
- Redis uses token authentication
- CORS restricted to frontend domain

## 📊 Free Tier Limits & Mitigation

### Render (Backend)
- **Limit**: Sleeps after 15 min inactivity
- **Mitigation**: 
  - Use UptimeRobot to ping every 14 min
  - Implement client-side retry logic
  - Show loading states during wake-up

### Neon (Database)
- **Limit**: 3GB storage, auto-suspend
- **Mitigation**:
  - Regular cleanup of old data
  - Efficient schema design
  - Monitor storage usage

### Upstash (Redis)
- **Limit**: 10k commands/day
- **Mitigation**:
  - Intelligent caching strategy
  - Batch operations where possible
  - Fallback to database if limit reached

### Vercel (Frontend)
- **Limit**: 100GB bandwidth/month
- **Mitigation**:
  - Enable aggressive caching
  - Optimize images and assets
  - Use CDN for static files

## 🔄 Cold Start Handling

### Backend Wake-up Strategy
```typescript
// frontend/src/lib/api-client.ts
async function apiCall(endpoint: string, options: RequestInit) {
  const maxRetries = 3;
  let lastError;
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(endpoint, {
        ...options,
        signal: AbortSignal.timeout(30000) // 30s timeout
      });
      
      if (response.ok) return response;
      
      // If 503, backend is waking up
      if (response.status === 503) {
        await new Promise(r => setTimeout(r, 5000)); // Wait 5s
        continue;
      }
      
      throw new Error(`HTTP ${response.status}`);
    } catch (error) {
      lastError = error;
      if (i < maxRetries - 1) {
        await new Promise(r => setTimeout(r, 2000)); // Wait 2s
      }
    }
  }
  
  throw lastError;
}
```

## 📈 Scaling Path

When you outgrow free tier:

### Step 1: Database (First bottleneck)
- **Neon Pro**: $19/month for 10GB
- **Alternative**: Supabase ($25/month)

### Step 2: Backend Hosting
- **Render Starter**: $7/month (no sleep)
- **Alternative**: Railway ($5/month)

### Step 3: Redis Upgrade
- **Upstash Pay-as-you-go**: $0.2 per 100k commands
- **Alternative**: Redis Cloud (30MB free)

### Step 4: Frontend (Rarely needed)
- **Vercel Pro**: $20/month per user
- **Alternative**: Netlify ($19/month)

## 🛠️ Maintenance Commands

### Database Backup (Monthly)
```bash
# From Render shell
pg_dump $DATABASE_URL | gzip > backup_$(date +%Y%m%d).sql.gz
```

### Cache Clear (If needed)
```python
# From Render shell
python -c "
from backend.src.core.redis_upstash import get_redis
import asyncio
redis = asyncio.run(get_redis())
asyncio.run(redis.flushdb())
"
```

### Health Check
```bash
# Check all services
curl https://prism-backend.onrender.com/health
curl https://prism-app.vercel.app/api/health
```

## 📚 Resources

- [Render Docs](https://render.com/docs)
- [Vercel Docs](https://vercel.com/docs)
- [Neon Docs](https://neon.tech/docs)
- [Upstash Docs](https://docs.upstash.com)

---

This architecture provides a robust, scalable foundation for PRISM while maintaining zero monthly costs. Perfect for startups, MVPs, and proof-of-concepts!