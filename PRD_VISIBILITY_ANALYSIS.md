# PRD Visibility & Anthropic API Usage Analysis

## Executive Summary

Two critical issues have been identified:
1. **PRDs not appearing after generation** - User workflow issue, not a bug
2. **Unexpected Anthropic API costs** - Multiple potential causes identified

## Issue 1: PRDs Not Visible After Generation

### Root Cause
PRDs are **successfully generated** but **not automatically saved** to the database. The system requires a manual "Save as Draft" action.

### Current User Flow
1. User fills form and clicks "Generate PRD" ✅
2. Backend generates PRD using Anthropic API ✅
3. PRD is displayed in the UI ✅
4. **User must click "Save as Draft"** ❌ (Often missed)
5. Only saved PRDs appear in the PRD list

### Evidence
- Frontend code shows the save button only appears after generation
- The `saveDraft` function explicitly creates a database record
- No auto-save functionality exists

### Solutions

#### Immediate (User Education)
Display a prominent notification after generation:
```javascript
toast({
  title: 'PRD Generated!',
  description: 'Remember to click "Save as Draft" to keep your PRD.',
  duration: 10000, // Show for 10 seconds
})
```

#### Short-term (Auto-save)
Add auto-save functionality after successful generation:
```javascript
if (response.success) {
  setGeneratedPRD(response.prd)
  // Auto-save after 2 seconds
  setTimeout(() => {
    if (!hasSaved) {
      saveDraft()
    }
  }, 2000)
}
```

#### Long-term (UX Redesign)
- Combine generation and saving into a single action
- Add "Generate and Save" button option
- Show unsaved indicator clearly

## Issue 2: Unexpected Anthropic API Costs

### Identified Causes

#### 1. **Request Timeouts & Retries**
- Backend timeout: 30 seconds (was), now 120 seconds
- Anthropic requests take 40-50 seconds typically
- Timeout causes error → User retries → Multiple API calls

#### 2. **Authentication Retry Logic**
- Auth interceptor retries failed requests up to 3 times
- If token refresh coincides with PRD generation, could trigger multiple attempts
- Exponential backoff: 1s, 2s, 4s between retries

#### 3. **User Behavior Pattern**
- Users don't see PRD in list (not saved)
- Assume generation failed
- Try multiple times
- Each attempt costs ~2,837 tokens

#### 4. **No Request Deduplication**
- Multiple rapid clicks on "Generate PRD" create multiple requests
- No client-side debouncing
- No server-side request deduplication

### Cost Analysis
- Average PRD generation: ~2,837 tokens
- Claude 3 Sonnet pricing: $3/1M input, $15/1M output
- Estimated cost per PRD: ~$0.04
- 100 unnecessary retries = $4.00 wasted

### Solutions

#### Immediate Actions

1. **Add Loading State Management**
```javascript
const [isGenerating, setIsGenerating] = useState(false)

const generatePRD = async () => {
  if (isGenerating) return // Prevent double-clicks
  setIsGenerating(true)
  // ... generation logic
  setIsGenerating(false)
}
```

2. **Add Request ID for Deduplication**
```javascript
const requestId = crypto.randomUUID()
// Include in request headers
headers['X-Request-ID'] = requestId
```

3. **Better Error Messages**
```javascript
if (error.message.includes('timeout')) {
  toast({
    title: 'Generation Taking Longer Than Expected',
    description: 'Large PRDs can take 1-2 minutes. Please wait...',
    duration: 30000,
  })
}
```

#### Backend Improvements

1. **Request Deduplication Middleware**
```python
class RequestDeduplicationMiddleware:
    def __init__(self):
        self.pending_requests = {}
    
    async def __call__(self, request: Request, call_next):
        request_id = request.headers.get('X-Request-ID')
        if request_id and request_id in self.pending_requests:
            # Return cached response
            return self.pending_requests[request_id]
```

2. **Add Detailed Logging**
```python
logger.info(
    "ai_request_start",
    user_id=current_user.id,
    request_id=request_id,
    endpoint=request.url.path,
    provider=provider,
    estimated_tokens=estimated_tokens,
    timestamp=datetime.utcnow()
)
```

3. **Implement Cost Tracking**
```python
# Track costs per user
await db.execute(
    """
    INSERT INTO ai_usage_logs (user_id, provider, model, tokens, cost, timestamp)
    VALUES (:user_id, :provider, :model, :tokens, :cost, :timestamp)
    """,
    values={...}
)
```

## Monitoring & Prevention

### 1. **Add Prometheus Metrics Dashboard**
```yaml
- name: AI Request Rate
  query: rate(ai_requests_total[5m])
  
- name: AI Costs by User
  query: sum by (user_id) (ai_tokens_used_total * 0.000015)
  
- name: Failed AI Requests
  query: rate(ai_requests_total{status="error"}[5m])
```

### 2. **Rate Limiting Per User**
```python
@rate_limit(
    requests_per_minute=5,  # Max 5 PRD generations per minute
    requests_per_hour=50,   # Max 50 per hour
    cost_per_hour=5.00      # Max $5 per hour
)
```

### 3. **Alert Configuration**
```yaml
alerts:
  - name: HighAIUsage
    expr: sum(rate(ai_tokens_used_total[5m])) > 100000
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High AI token usage detected"
```

## Immediate Action Items

1. **User Communication**
   - Send notification about "Save as Draft" requirement
   - Add tooltip on Generate button about processing time

2. **Code Changes Priority**
   - [ ] Add request deduplication (Frontend)
   - [ ] Implement auto-save after generation
   - [ ] Add better loading states and progress indicators
   - [ ] Add cost tracking and user limits

3. **Monitoring**
   - [ ] Set up Grafana dashboard for AI usage
   - [ ] Configure alerts for abnormal usage
   - [ ] Daily cost report email

## Estimated Impact

- **Reduce unnecessary API calls by 80%**
- **Save approximately $50-100/month** in API costs
- **Improve user satisfaction** with auto-save
- **Better cost visibility** and control

## Testing Recommendations

1. **Load Testing**
```bash
# Test concurrent PRD generation
for i in {1..10}; do
  curl -X POST http://localhost:8100/api/v1/ai/generate/prd \
    -H "Authorization: Bearer $TOKEN" \
    -d @prd_request.json &
done
```

2. **Monitor During Testing**
```bash
# Watch API calls in real-time
docker compose logs -f backend | grep anthropic_request
```

3. **Cost Simulation**
- Generate 10 PRDs
- Check Anthropic dashboard
- Verify cost matches expected (~$0.40)