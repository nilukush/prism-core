# PRD Display Issue: Claude vs Mock Service

## Problem Summary
- Mock service PRDs display correctly below the "Generate PRD" button
- Claude Sonnet PRDs are generated (API costs confirm) but don't display in UI
- Backend returns the same response format for both services

## Investigation Steps

### 1. Check Browser Console
Open browser DevTools (F12) BEFORE generating a PRD and look for:
```javascript
// Expected console logs:
"PRD Generation - Starting request"
"PRD Generation - Sending data: {product_name: ..., description: ...}"
"Raw API Response: {success: true, prd: '...', metadata: {...}}"
"PRD Content Length: 2472"
"PRD Content Preview: # AI-Powered Analytics Dashboard..."

// Possible errors:
- JSON parsing errors
- State update errors
- Component re-render issues
```

### 2. Check Network Tab
In DevTools Network tab, find the `/api/v1/ai/generate/prd` request:
- Status: Should be 200
- Response time: Claude takes 40-60 seconds (vs 1-2 seconds for mock)
- Response body: Should contain `{"success": true, "prd": "...", "metadata": {...}}`

### 3. Common Issues & Solutions

#### Issue 1: Request Timeout
**Symptom**: Network request shows pending for 30+ seconds, then fails
**Cause**: Frontend timeout shorter than backend processing time
**Solution**:
```javascript
// In api-client.ts, increase timeout:
const { params, data, timeout = 120000, ...requestOptions } = options
//                               ^^^^^^ Changed from 30000
```

#### Issue 2: Empty Response Body
**Symptom**: Console shows "PRD Content Length: 0"
**Cause**: Response parsing issue or empty content from API
**Solution**: Check if response body is being consumed elsewhere

#### Issue 3: State Not Updating
**Symptom**: Response is valid but UI doesn't update
**Cause**: React state update issue or error in setState
**Solution**: Add more detailed logging

## Enhanced Debug Version

Create this temporary debug file to isolate the issue:

`frontend/src/app/app/prds/new/debug-page.tsx`:
```tsx
'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

export default function DebugPRDPage() {
  const [status, setStatus] = useState('Ready')
  const [response, setResponse] = useState<any>(null)
  const [error, setError] = useState<any>(null)
  const [prdContent, setPrdContent] = useState('')

  const testGeneration = async () => {
    setStatus('Starting...')
    setError(null)
    setResponse(null)
    setPrdContent('')

    try {
      const startTime = Date.now()
      
      // Direct fetch to bypass any interceptors
      const res = await fetch('/api/v1/ai/generate/prd', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${await getToken()}`,
        },
        body: JSON.stringify({
          product_name: 'Test Product',
          description: 'A test product for debugging',
          target_audience: 'Developers',
          key_features: ['Feature 1', 'Feature 2'],
          constraints: ['Must work']
        })
      })

      const duration = Date.now() - startTime
      setStatus(`Response received in ${duration}ms`)

      const text = await res.text()
      console.log('Raw response text:', text)

      let data
      try {
        data = JSON.parse(text)
        setResponse(data)
        
        if (data.success && data.prd) {
          setPrdContent(data.prd)
          setStatus(`Success! PRD length: ${data.prd.length}`)
        } else {
          setStatus('Response missing PRD content')
        }
      } catch (e) {
        setError({ message: 'JSON parse error', text })
      }

    } catch (err: any) {
      setError(err)
      setStatus(`Error: ${err.message}`)
    }
  }

  // Helper to get auth token
  async function getToken() {
    const session = await fetch('/api/auth/session').then(r => r.json())
    return session?.accessToken || ''
  }

  return (
    <div className="container py-8">
      <h1 className="text-2xl font-bold mb-4">PRD Generation Debug</h1>
      
      <Card className="p-4 mb-4">
        <p className="mb-2">Status: <strong>{status}</strong></p>
        <Button onClick={testGeneration}>Test PRD Generation</Button>
      </Card>

      {error && (
        <Card className="p-4 mb-4 border-red-500">
          <h2 className="font-bold text-red-500">Error</h2>
          <pre className="text-xs">{JSON.stringify(error, null, 2)}</pre>
        </Card>
      )}

      {response && (
        <Card className="p-4 mb-4">
          <h2 className="font-bold">Response Metadata</h2>
          <pre className="text-xs">{JSON.stringify(response.metadata, null, 2)}</pre>
        </Card>
      )}

      {prdContent && (
        <Card className="p-4">
          <h2 className="font-bold mb-2">PRD Content ({prdContent.length} chars)</h2>
          <div className="bg-gray-100 p-4 rounded">
            <pre className="whitespace-pre-wrap text-sm">{prdContent}</pre>
          </div>
        </Card>
      )}
    </div>
  )
}
```

## Testing Protocol

### 1. Test with Mock Service
```bash
# Set mock provider in docker-compose.dev.yml
- DEFAULT_LLM_PROVIDER=mock

# Restart backend
docker compose -f docker-compose.yml -f docker-compose.dev.yml restart backend

# Test generation - should be fast (1-2 seconds)
```

### 2. Test with Claude
```bash
# Set Claude provider
- DEFAULT_LLM_PROVIDER=anthropic

# Restart backend
docker compose -f docker-compose.yml -f docker-compose.dev.yml restart backend

# Test generation - will be slow (40-60 seconds)
```

### 3. Compare Results
Document:
- Response time difference
- Console errors
- Network response differences
- Any timeout errors

## Quick Fixes to Try

### 1. Increase Frontend Timeout
```typescript
// In api-client.ts
const { params, data, timeout = 120000, ...requestOptions } = options
```

### 2. Add Loading State Check
```typescript
// In page.tsx, after setGeneratedPRD
console.log('State updated with PRD:', generatedPRD.substring(0, 100))
// Force re-render
setTimeout(() => {
  console.log('PRD in state after timeout:', generatedPRD.substring(0, 100))
}, 100)
```

### 3. Check for Race Conditions
```typescript
// Add request ID to prevent stale updates
const requestId = useRef(0)

const generatePRD = async () => {
  const currentRequest = ++requestId.current
  // ... make request ...
  
  // Only update state if this is still the latest request
  if (currentRequest === requestId.current) {
    setGeneratedPRD(response.prd)
  }
}
```

## Root Cause Possibilities

1. **Timeout Issue**: Claude takes 40-60s, frontend times out at 30s
2. **Response Size**: Claude responses might be larger, causing parsing issues
3. **Character Encoding**: Special characters in Claude response breaking display
4. **State Race Condition**: Long response time causing React state issues
5. **Memory Issue**: Large response causing browser memory problems

## Monitoring During Debug

Run this in terminal while testing:
```bash
# Watch backend logs
docker compose logs -f backend | grep -E "prd_generation|anthropic"

# Watch frontend console
# Open browser DevTools, Console tab

# Watch network traffic
# Open browser DevTools, Network tab, filter by "prd"
```

## Emergency Workaround

If nothing else works, try this minimal version:
```typescript
// Replace the generatePRD function temporarily
const generatePRD = async () => {
  setLoading(true)
  try {
    // Hardcoded test
    const testPRD = "# Test PRD\n\nIf you see this, the UI is working but the API response is not being processed correctly."
    setGeneratedPRD(testPRD)
    
    // Now try real API
    const response = await apiClient.post('/api/v1/ai/generate/prd', {...})
    console.log('API Response received:', response)
    
    // Override with real content if successful
    if (response?.prd) {
      setGeneratedPRD(response.prd)
    }
  } finally {
    setLoading(false)
  }
}
```