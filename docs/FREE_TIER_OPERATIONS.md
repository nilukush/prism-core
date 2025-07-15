# Free Tier Operations Guide

## 🔍 Monitoring Your Free Deployment

### Service Health Monitoring

#### 1. UptimeRobot Setup (Free)
```bash
# Monitor these endpoints:
Backend Health: https://prism-backend.onrender.com/health
Frontend Home: https://prism-app.vercel.app
API Docs: https://prism-backend.onrender.com/docs

# Alert settings:
- Check interval: 5 minutes
- Alert after 2 failures
- Email notifications
```

#### 2. Built-in Monitoring

**Render Dashboard**
- CPU and Memory usage
- Request logs
- Deploy history
- Environment variables

**Vercel Dashboard**
- Function invocations
- Bandwidth usage
- Build logs
- Real-time analytics

### 📊 Usage Tracking

Create `scripts/check-usage.sh`:
```bash
#!/bin/bash

echo "🔍 Checking Free Tier Usage..."

# Neon Database
echo "📊 Database Usage (Neon):"
psql $DATABASE_URL -c "
SELECT 
    pg_database_size(current_database()) as db_size,
    (SELECT count(*) FROM users) as user_count,
    (SELECT count(*) FROM projects) as project_count,
    (SELECT count(*) FROM documents) as document_count;
"

# Upstash Redis
echo "📊 Cache Usage (Upstash):"
curl -s -H "Authorization: Bearer $UPSTASH_TOKEN" \
  "$UPSTASH_URL/info" | jq '.result'

# Check Vercel usage via API
echo "📊 Frontend Usage (Vercel):"
curl -s -H "Authorization: Bearer $VERCEL_TOKEN" \
  "https://api.vercel.com/v1/usage" | jq '.bandwidth'
```

## 🚨 Handling Service Limits

### When You Hit Limits

#### Database (Neon - 3GB limit)
```sql
-- Check largest tables
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;

-- Clean up old data
DELETE FROM ai_generations WHERE created_at < NOW() - INTERVAL '30 days';
DELETE FROM user_sessions WHERE expires_at < NOW();
VACUUM FULL;
```

#### Redis (Upstash - 10k commands/day)
```python
# Add to backend/src/core/cache.py
import time
from functools import wraps

class RateLimitedCache:
    def __init__(self, redis_client, daily_limit=10000):
        self.redis = redis_client
        self.daily_limit = daily_limit
        self.command_count = 0
        self.last_reset = time.time()
    
    def should_use_cache(self):
        # Reset counter daily
        if time.time() - self.last_reset > 86400:
            self.command_count = 0
            self.last_reset = time.time()
        
        # Use cache only if under 80% of limit
        return self.command_count < (self.daily_limit * 0.8)
    
    @wraps
    async def get(self, key):
        if not self.should_use_cache():
            return None
        self.command_count += 1
        return await self.redis.get(key)
```

#### Frontend Bandwidth (Vercel - 100GB/month)
```javascript
// Add to next.config.js
module.exports = {
  images: {
    // Optimize images to reduce bandwidth
    formats: ['image/avif', 'image/webp'],
    minimumCacheTTL: 60 * 60 * 24 * 30, // 30 days
  },
  
  // Enable static generation where possible
  experimental: {
    isrMemoryCacheSize: 0, // Disable ISR cache to save memory
  },
  
  // Compress all responses
  compress: true,
};
```

## 🔧 Performance Optimization

### 1. Cold Start Mitigation

Create `frontend/src/app/api/warm/route.ts`:
```typescript
import { NextResponse } from 'next/server';

export async function GET() {
  // Warm up backend
  try {
    await fetch(`${process.env.NEXT_PUBLIC_API_URL}/health`);
  } catch (error) {
    console.error('Backend warm-up failed:', error);
  }
  
  return NextResponse.json({ warmed: true });
}
```

Add to `frontend/src/app/layout.tsx`:
```typescript
// Warm up services every 4 minutes
useEffect(() => {
  const warmUp = () => {
    fetch('/api/warm').catch(() => {});
  };
  
  warmUp(); // Initial warm-up
  const interval = setInterval(warmUp, 4 * 60 * 1000);
  
  return () => clearInterval(interval);
}, []);
```

### 2. Database Connection Pooling

Update `backend/src/database.py`:
```python
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
import os

# For free tier with connection limits
if os.getenv('ENVIRONMENT') == 'production':
    engine = create_engine(
        settings.DATABASE_URL,
        # Use StaticPool for serverless
        poolclass=StaticPool,
        connect_args={
            "options": "-c statement_timeout=25000",  # 25 second timeout
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        }
    )
else:
    # Local development
    engine = create_engine(settings.DATABASE_URL)
```

### 3. Caching Strategy

Create `backend/src/core/cache_strategy.py`:
```python
from typing import Optional, Any
import hashlib
import json

class TieredCache:
    """
    Tiered caching strategy for free tier limits
    L1: In-memory (Python dict)
    L2: Redis (Upstash)
    """
    
    def __init__(self, redis_client, max_memory_items=1000):
        self.redis = redis_client
        self.memory_cache = {}
        self.max_memory_items = max_memory_items
    
    def _get_key_hash(self, key: str) -> str:
        """Generate consistent hash for cache key"""
        return hashlib.md5(key.encode()).hexdigest()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get from L1 (memory) first, then L2 (Redis)"""
        key_hash = self._get_key_hash(key)
        
        # Check L1 cache
        if key_hash in self.memory_cache:
            return self.memory_cache[key_hash]
        
        # Check L2 cache
        if self.redis:
            try:
                value = await self.redis.get(key_hash)
                if value:
                    # Promote to L1
                    self._add_to_memory(key_hash, value)
                    return json.loads(value)
            except Exception:
                pass
        
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Set in both L1 and L2 cache"""
        key_hash = self._get_key_hash(key)
        serialized = json.dumps(value, default=str)
        
        # Add to L1
        self._add_to_memory(key_hash, serialized)
        
        # Add to L2 if available
        if self.redis:
            try:
                await self.redis.set(key_hash, serialized, ex=ttl)
            except Exception:
                pass
    
    def _add_to_memory(self, key: str, value: str):
        """Add to memory cache with LRU eviction"""
        if len(self.memory_cache) >= self.max_memory_items:
            # Remove oldest item (simple FIFO for free tier)
            oldest = next(iter(self.memory_cache))
            del self.memory_cache[oldest]
        
        self.memory_cache[key] = value
```

## 📈 Scaling Beyond Free Tier

### When to Upgrade

Monitor these metrics:
```python
# Add to backend/src/api/v1/admin/metrics.py
@router.get("/metrics/usage")
async def get_usage_metrics(
    current_user: User = Depends(require_admin)
):
    return {
        "users": {
            "total": await get_user_count(),
            "daily_active": await get_dau(),
            "upgrade_at": 100  # Suggested threshold
        },
        "storage": {
            "database_gb": await get_db_size_gb(),
            "limit_gb": 3,
            "percent_used": (await get_db_size_gb() / 3) * 100
        },
        "requests": {
            "daily": await get_daily_requests(),
            "redis_commands": await get_redis_command_count(),
            "upgrade_at": 8000  # 80% of Upstash limit
        },
        "bandwidth": {
            "monthly_gb": await get_monthly_bandwidth_gb(),
            "limit_gb": 100,
            "percent_used": (await get_monthly_bandwidth_gb() / 100) * 100
        }
    }
```

### Migration Plan

#### Phase 1: Database (First bottleneck)
```bash
# Option 1: Neon Pro ($19/month)
- 10GB storage
- Autoscaling compute
- Point-in-time recovery

# Option 2: Supabase Pro ($25/month)
- 8GB database
- Unlimited API requests
- Daily backups
```

#### Phase 2: Backend Hosting
```bash
# Option 1: Render Starter ($7/month)
- No sleep
- 512MB RAM
- Custom domains

# Option 2: Railway Hobby ($5/month)
- $5 monthly credit
- Better performance
- Multiple services
```

#### Phase 3: Caching Layer
```bash
# Option 1: Upstash Pay-as-you-go
- $0.2 per 100K commands
- Much more cost effective

# Option 2: Redis Cloud ($0/month up to 30MB)
- 30MB free
- 30 connections
- Better performance
```

## 🛠️ Maintenance Scripts

### Daily Maintenance
Create `scripts/daily-maintenance.sh`:
```bash
#!/bin/bash

echo "🛠️ Running daily maintenance..."

# 1. Database cleanup
psql $DATABASE_URL << EOF
-- Clean expired sessions
DELETE FROM user_sessions WHERE expires_at < NOW();

-- Clean old AI generations (keep 30 days)
DELETE FROM ai_generations 
WHERE created_at < NOW() - INTERVAL '30 days';

-- Update statistics
VACUUM ANALYZE;
EOF

# 2. Check service health
curl -f https://prism-backend.onrender.com/health || echo "Backend unhealthy!"
curl -f https://prism-app.vercel.app || echo "Frontend unhealthy!"

# 3. Clear old logs (if storing locally)
find ./logs -name "*.log" -mtime +7 -delete 2>/dev/null || true

echo "✅ Maintenance complete!"
```

### Weekly Reports
Create `scripts/weekly-report.sh`:
```bash
#!/bin/bash

echo "📊 Weekly PRISM Report"
echo "====================="
date

# User metrics
echo -e "\n👥 User Metrics:"
psql $DATABASE_URL -t << EOF
SELECT 
    'Total Users: ' || COUNT(*) FROM users
UNION ALL
SELECT 
    'New This Week: ' || COUNT(*) 
FROM users 
WHERE created_at > NOW() - INTERVAL '7 days';
EOF

# Project metrics
echo -e "\n📁 Project Metrics:"
psql $DATABASE_URL -t << EOF
SELECT 
    'Total Projects: ' || COUNT(*) FROM projects
UNION ALL
SELECT 
    'Active Projects: ' || COUNT(*) 
FROM projects 
WHERE status = 'active';
EOF

# Document metrics
echo -e "\n📄 Document Metrics:"
psql $DATABASE_URL -t << EOF
SELECT 
    'Total PRDs: ' || COUNT(*) 
FROM documents 
WHERE document_type = 'prd'
UNION ALL
SELECT 
    'Generated This Week: ' || COUNT(*) 
FROM documents 
WHERE created_at > NOW() - INTERVAL '7 days';
EOF

# Resource usage
echo -e "\n💾 Resource Usage:"
echo "Database Size: $(psql $DATABASE_URL -t -c "SELECT pg_size_pretty(pg_database_size(current_database()));")"
echo "Largest Table: $(psql $DATABASE_URL -t -c "SELECT tablename || ': ' || pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) FROM pg_tables ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC LIMIT 1;")"
```

## 🆘 Troubleshooting

### Common Issues

#### 1. Render Service Sleeping
```javascript
// Add to frontend
const wakeBackend = async () => {
  const timeout = new Promise((_, reject) => 
    setTimeout(() => reject(new Error('Timeout')), 5000)
  );
  
  try {
    await Promise.race([
      fetch(`${process.env.NEXT_PUBLIC_API_URL}/health`),
      timeout
    ]);
  } catch {
    // Show loading message
    console.log('Waking up backend service...');
  }
};
```

#### 2. Database Connection Drops
```python
# Add to backend/src/database.py
from sqlalchemy import event
from sqlalchemy.pool import Pool

@event.listens_for(Pool, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Ensure connections are fresh"""
    cursor = dbapi_connection.cursor()
    cursor.execute("SELECT 1")
    cursor.close()
```

#### 3. Redis Command Limit
```python
# Add circuit breaker
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.is_open = False
    
    def call(self, func, *args, **kwargs):
        if self.is_open:
            if time.time() - self.last_failure_time > self.timeout:
                self.is_open = False
                self.failures = 0
            else:
                return None
        
        try:
            result = func(*args, **kwargs)
            self.failures = 0
            return result
        except Exception:
            self.failures += 1
            self.last_failure_time = time.time()
            
            if self.failures >= self.failure_threshold:
                self.is_open = True
            
            return None
```

## 📚 Additional Resources

- [Render Status Page](https://status.render.com)
- [Vercel Status Page](https://www.vercel-status.com)
- [Neon Status Page](https://neonstatus.com)
- [Upstash Status Page](https://status.upstash.com)

Remember: Free tier is perfect for MVPs and proof-of-concepts. Plan your upgrade path early to avoid service disruptions as you grow!