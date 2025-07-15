# IMMEDIATE FIX: PRD Not Displaying with Claude

## Root Cause Identified
**Frontend timeout: 30 seconds**
**Claude response time: 40-60 seconds**
**Result: Request aborts before Claude finishes, UI shows nothing**

## Fix #1: Increase Frontend Timeout (Immediate)

### Step 1: Update API Client Timeout
Edit `/frontend/src/lib/api-client.ts` line 114:

```typescript
// CHANGE THIS:
const { params, data, timeout = 30000, ...requestOptions } = options

// TO THIS:
const { params, data, timeout = 120000, ...requestOptions } = options
//                               ^^^^^^^ 120 seconds instead of 30
```

### Step 2: Add Timeout Override for AI Endpoints
Edit `/frontend/src/app/app/prds/new/page.tsx` line 225:

```typescript
// CHANGE THIS:
const response = await apiClient.post('/api/v1/ai/generate/prd', {
  product_name: formData.productName,
  // ... rest of data
})

// TO THIS:
const response = await apiClient.post('/api/v1/ai/generate/prd', {
  product_name: formData.productName,
  // ... rest of data
}, {
  timeout: 120000  // 2 minutes for AI generation
})
```

### Step 3: Restart Frontend
```bash
cd frontend
# Kill current process (Ctrl+C)
# Restart
PORT=3100 npm run dev
```

## Fix #2: Add Progress Indicator (User Experience)

Add this after line 223 in `page.tsx`:

```typescript
setLoading(true)
// Add progress toast
const progressToast = toast({
  title: '🤖 Generating PRD with Claude AI',
  description: 'This may take 1-2 minutes. Please wait...',
  duration: 60000, // Show for 1 minute
})

try {
  // ... existing code ...
} finally {
  setLoading(false)
  // Dismiss progress toast
  progressToast.dismiss()
}
```

## Fix #3: Add Debug Logging

Add after line 235 to see what's happening:

```typescript
console.log('Raw API Response:', response)
console.log('Response type:', typeof response)
console.log('Response has success?', 'success' in response)
console.log('Response has prd?', 'prd' in response)
console.log('PRD content preview:', response?.prd?.substring(0, 100))
```

## Testing After Fix

1. Open browser DevTools (F12) → Console tab
2. Generate a PRD
3. You should see:
   - Progress toast appears immediately
   - "Generating PRD..." spinner continues for 40-60 seconds
   - Console logs show the response
   - PRD appears below the button

## Why Mock Service Worked

- Mock service responds in 1-2 seconds (< 30s timeout)
- Claude responds in 40-60 seconds (> 30s timeout)
- When timeout hits, the request is aborted
- No error is shown because the catch block handles it silently

## Additional Improvements

### 1. Show Timeout Error
```typescript
} catch (error: any) {
  console.error('Error generating PRD:', error)
  
  // Add specific timeout handling
  if (error.name === 'AbortError' || error.message.includes('timeout')) {
    toast({
      title: '⏱️ Request Timed Out',
      description: 'PRD generation is taking longer than expected. Try increasing the timeout or using a faster model.',
      variant: 'destructive',
      duration: 10000,
    })
    return
  }
  
  // ... existing error handling
}
```

### 2. Add Request Status
```typescript
const [requestStatus, setRequestStatus] = useState('')

// In generatePRD function:
setRequestStatus('Sending request to AI...')
// After 30 seconds:
setTimeout(() => {
  if (loading) {
    setRequestStatus('Still processing... Claude can take up to 60 seconds')
  }
}, 30000)
```

### 3. Consider Streaming Response
For better UX with long-running requests, implement streaming:
- Backend sends chunks as they're generated
- Frontend displays partial content immediately
- User sees progress in real-time

## Verification Steps

1. **Before Fix**: 
   - Generate PRD → Wait 30s → Nothing appears
   - Check console for "AbortError"

2. **After Fix**:
   - Generate PRD → See progress indicator → Wait 40-60s → PRD appears
   - Check console for successful response logs

3. **Check Anthropic Dashboard**:
   - Verify API calls are completing (not being aborted)
   - Token usage should match full PRD generation

## Emergency Fallback

If timeout fix doesn't work, use polling approach:
```typescript
// Start generation
const { task_id } = await apiClient.post('/api/v1/ai/generate/prd/start', data)

// Poll for completion
const pollInterval = setInterval(async () => {
  const { status, result } = await apiClient.get(`/api/v1/ai/tasks/${task_id}`)
  if (status === 'completed') {
    clearInterval(pollInterval)
    setGeneratedPRD(result.prd)
  }
}, 5000)
```