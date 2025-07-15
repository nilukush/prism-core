# Urgent Fixes for PRD Visibility & API Cost Issues

## Quick Summary

1. **PRDs don't appear** because they're not being saved after generation
2. **API costs increasing** due to retries, timeouts, and user confusion

## Immediate Actions (Do Now)

### 1. Monitor Current Usage
```bash
# Run the monitoring script
./monitor_ai_usage.sh

# Choose option 1 for summary
# Choose option 3 to check for suspicious patterns
# Choose option 4 to see estimated costs
```

### 2. Apply Auto-Save Fix
```bash
# Apply the patch to add auto-save
cd frontend
patch -p2 < src/app/app/prds/new/AutoSavePRD.patch

# Or manually add these changes to page.tsx:
# 1. Add autoSaveTriggered state
# 2. Add 3-second auto-save after generation
# 3. Add visual indicator for auto-save
# 4. Prevent double-clicks with isGenerating flag
```

### 3. Add Request Deduplication (Backend)

Create file: `backend/src/middleware/deduplication.py`
```python
from typing import Dict, Optional
import hashlib
import json
from datetime import datetime, timedelta
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as aioredis

class DeduplicationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_url: str):
        super().__init__(app)
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None
        
    async def dispatch(self, request: Request, call_next):
        # Only deduplicate AI endpoints
        if "/ai/generate" not in request.url.path:
            return await call_next(request)
            
        # Get request ID from header
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            return await call_next(request)
            
        # Check if we've seen this request
        cache_key = f"dedup:{request_id}"
        
        if not self.redis:
            self.redis = await aioredis.from_url(self.redis_url)
            
        # Check for existing response
        cached = await self.redis.get(cache_key)
        if cached:
            return Response(
                content=cached,
                media_type="application/json",
                headers={"X-Deduplicated": "true"}
            )
            
        # Process request
        response = await call_next(request)
        
        # Cache successful responses for 5 minutes
        if response.status_code == 200:
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            await self.redis.setex(cache_key, 300, body)
            
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
            
        return response
```

### 4. Add Frontend Request ID
```javascript
// In api-client.ts, modify the request method:
async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const requestId = crypto.randomUUID()
  
  const makeRequest = async (): Promise<T> => {
    // ... existing code ...
    
    const response = await fetch(this.buildUrl(endpoint, params), {
      ...requestOptions,
      headers: {
        ...headers,
        ...authHeaders,
        'X-Request-ID': requestId, // Add this
        ...(requestOptions.headers || {}),
      },
      // ... rest of config
    })
  }
  // ... rest of method
}
```

## Cost Control Measures

### 1. Add User Rate Limiting
```python
# In backend/src/api/v1/ai.py
from backend.src.services.rate_limiter import user_cost_limit

@router.post("/generate/prd")
@rate_limit(requests_per_minute=3, requests_per_hour=30)
@user_cost_limit(max_cost_per_hour=5.00)  # $5/hour limit
async def generate_prd(...):
    # ... existing code
```

### 2. Track Costs in Database
```sql
-- Add this table
CREATE TABLE ai_usage_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    provider VARCHAR(50),
    model VARCHAR(100),
    operation VARCHAR(100),
    tokens_used INTEGER,
    estimated_cost DECIMAL(10, 4),
    request_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for queries
CREATE INDEX idx_ai_usage_user_time ON ai_usage_logs(user_id, created_at);
```

### 3. Add Cost Tracking Function
```python
async def track_ai_usage(
    db: AsyncSession,
    user_id: int,
    provider: str,
    model: str,
    operation: str,
    tokens: int,
    request_id: str
):
    # Calculate cost based on model
    cost_per_token = {
        "claude-3-sonnet-20240229": 0.000015,  # $15/1M output tokens
        "claude-3-haiku-20240307": 0.0000025,  # $2.50/1M output tokens
        "gpt-4-turbo-preview": 0.00003,        # $30/1M output tokens
    }
    
    estimated_cost = tokens * cost_per_token.get(model, 0.00002)
    
    await db.execute(
        """
        INSERT INTO ai_usage_logs 
        (user_id, provider, model, operation, tokens_used, estimated_cost, request_id)
        VALUES (:user_id, :provider, :model, :operation, :tokens, :cost, :request_id)
        """,
        {
            "user_id": user_id,
            "provider": provider,
            "model": model,
            "operation": operation,
            "tokens": tokens,
            "cost": estimated_cost,
            "request_id": request_id
        }
    )
    await db.commit()
```

## User Communication Template

### Email to Users
```
Subject: Important: How to Save Your Generated PRDs

Hi [User],

We've noticed some PRDs aren't being saved properly. Here's what you need to know:

1. After clicking "Generate PRD", wait for the PRD to appear
2. **Important**: Click "Save as Draft" to keep your PRD
3. Only saved PRDs appear in your PRD list

We're implementing auto-save to make this easier. In the meantime, please remember to save your work.

If you're experiencing issues, please let us know.

Best regards,
The PRISM Team
```

### In-App Notification
```javascript
// Add to the PRD generation success handler
if (!localStorage.getItem('prd-save-tip-shown')) {
  toast({
    title: '💡 Pro Tip',
    description: 'Remember to click "Save as Draft" after generation to keep your PRD!',
    duration: 15000,
  })
  localStorage.setItem('prd-save-tip-shown', 'true')
}
```

## Monitoring Dashboard

### Grafana Query Examples
```promql
# Requests per minute by user
sum by (user_id) (rate(ai_requests_total[1m]))

# Error rate
rate(ai_requests_total{status="error"}[5m]) / rate(ai_requests_total[5m])

# Cost per hour
sum(rate(ai_tokens_used_total[1h]) * 0.000015)

# Timeout errors
increase(http_request_duration_seconds_count{status="408"}[1h])
```

## Next Steps Priority

1. **Today**:
   - [ ] Apply auto-save patch
   - [ ] Run monitoring script to understand current usage
   - [ ] Send user communication about saving PRDs

2. **This Week**:
   - [ ] Implement request deduplication
   - [ ] Add cost tracking to database
   - [ ] Set up monitoring dashboard
   - [ ] Add user rate limits

3. **Next Sprint**:
   - [ ] Redesign UX to combine generate + save
   - [ ] Add progress indicators for long operations
   - [ ] Implement cost alerts
   - [ ] Add cheaper model options (Claude Haiku)

## Emergency Contacts

If costs spike unexpectedly:
1. Disable AI features: Set `AI_ENABLED=false` in backend env
2. Check Anthropic dashboard for usage details
3. Run `./monitor_ai_usage.sh` option 3 for suspicious patterns
4. Contact Anthropic support if you suspect unauthorized usage