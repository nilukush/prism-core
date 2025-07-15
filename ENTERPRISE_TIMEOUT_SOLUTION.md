# Enterprise-Grade Solution: Long-Running AI API Timeout Issue

## Executive Summary

The current system experiences frontend timeouts when using Claude AI for PRD generation due to mismatched timeout configurations (30s) versus actual API response times (40-60s). This document provides a comprehensive, production-ready solution following enterprise best practices.

## Root Cause Analysis

### Timeout Chain Investigation
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Browser   │────▶│  Frontend   │────▶│   Backend   │────▶│  Claude AI  │
│  (Default)  │ 30s │ (api-client)│ 30s │  (FastAPI)  │ 30s │   (40-60s)  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                           ❌                   ❌                    ✓
                      Times out            Times out            Completes
```

### Configuration Points Identified
1. **Frontend**: `api-client.ts` - hardcoded 30s timeout
2. **Backend**: `config.py` - `LLM_REQUEST_TIMEOUT = 30`
3. **Docker**: No explicit timeout (uses defaults)
4. **Kubernetes**: Ingress nginx proxy timeouts set to 30s
5. **Load Balancer**: Cloud provider defaults (typically 60s)

## Solution Architecture

### Phase 1: Immediate Fix (1 Hour Implementation)

#### 1.1 Frontend Timeout Increase
```typescript
// frontend/src/lib/api-client.ts
interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean>
  data?: any
  timeout?: number
}

class ApiClient {
  // Add endpoint-specific timeout configuration
  private getTimeoutForEndpoint(endpoint: string): number {
    const longRunningEndpoints = [
      '/api/v1/ai/generate/prd',
      '/api/v1/ai/generate/stories',
      '/api/v1/ai/analyze/velocity'
    ];
    
    return longRunningEndpoints.some(ep => endpoint.includes(ep)) 
      ? 120000  // 2 minutes for AI endpoints
      : 30000;  // 30 seconds default
  }

  async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const makeRequest = async (): Promise<T> => {
      const defaultTimeout = this.getTimeoutForEndpoint(endpoint);
      const { params, data, timeout = defaultTimeout, ...requestOptions } = options;
      // ... rest of implementation
    }
  }
}
```

#### 1.2 Backend Configuration Update
```python
# backend/src/core/config.py
class Settings(BaseSettings):
    # AI Configuration - Increased timeouts for production
    LLM_REQUEST_TIMEOUT: int = Field(default=120, description="Timeout for LLM API requests in seconds")
    LLM_REQUEST_TIMEOUT_ANTHROPIC: int = Field(default=180, description="Specific timeout for Anthropic API")
    LLM_REQUEST_TIMEOUT_OPENAI: int = Field(default=120, description="Specific timeout for OpenAI API")
    
    # Add timeout multiplier for development vs production
    TIMEOUT_MULTIPLIER: float = Field(
        default=1.0 if ENVIRONMENT == "production" else 1.5,
        description="Multiply all timeouts by this factor"
    )
```

#### 1.3 Kubernetes Ingress Update
```yaml
# k8s/base/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: prism-ingress
  annotations:
    # Global timeout increase
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "120"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "120"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "120"
    
    # Specific configuration for AI endpoints
    nginx.ingress.kubernetes.io/server-snippet: |
      location ~ ^/api/v1/ai/ {
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        proxy_buffering off;
        proxy_request_buffering off;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
      }
```

### Phase 2: Asynchronous Processing Pattern (1 Week Implementation)

#### 2.1 Database Schema for Job Tracking
```sql
-- Create job tracking table
CREATE TABLE ai_generation_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(id) NOT NULL,
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    request_data JSONB NOT NULL,
    result_data JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    CONSTRAINT valid_status CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled'))
);

-- Indexes for performance
CREATE INDEX idx_ai_jobs_user_status ON ai_generation_jobs(user_id, status);
CREATE INDEX idx_ai_jobs_created_at ON ai_generation_jobs(created_at DESC);
CREATE INDEX idx_ai_jobs_status ON ai_generation_jobs(status) WHERE status IN ('pending', 'processing');
```

#### 2.2 Celery Task Implementation
```python
# backend/src/workers/tasks/ai_generation_tasks.py
from celery import shared_task, Task
from celery.exceptions import SoftTimeLimitExceeded
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import json

class AIGenerationTask(Task):
    """Base task with built-in monitoring and error handling"""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        job_id = kwargs.get('job_id')
        if job_id:
            update_job_status(job_id, 'failed', error_message=str(exc))
        
        # Send notification
        send_failure_notification(
            user_id=kwargs.get('user_id'),
            job_type=self.name,
            error=str(exc)
        )
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Log retry attempts"""
        logger.warning(f"Task {task_id} retry: {exc}")
    
    def on_success(self, retval, task_id, args, kwargs):
        """Handle successful completion"""
        logger.info(f"Task {task_id} completed successfully")

@shared_task(
    base=AIGenerationTask,
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    time_limit=600,  # Hard limit: 10 minutes
    soft_time_limit=540,  # Soft limit: 9 minutes
    retry_backoff=True,
    retry_jitter=True
)
def generate_prd_task(
    self,
    job_id: str,
    user_id: int,
    product_name: str,
    description: str,
    target_audience: str,
    key_features: List[str],
    constraints: Optional[List[str]] = None,
    provider: Optional[str] = None
) -> Dict[str, Any]:
    """
    Asynchronous PRD generation with comprehensive error handling.
    """
    try:
        # Update job status
        update_job_status(job_id, 'processing', started_at=datetime.utcnow())
        
        # Get AI service (convert async to sync for Celery)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def _generate():
            ai_service = await AIServiceFactory.get_service(provider)
            
            prompt = PromptTemplate.prd_generation(
                product_name=product_name,
                description=description,
                target_audience=target_audience,
                key_features=key_features,
                constraints=constraints
            )
            
            ai_request = AIRequest(
                prompt=prompt,
                system_prompt=PromptTemplate.system_prompt(),
                temperature=0.7,
                max_tokens=4000
            )
            
            return await ai_service.generate(ai_request)
        
        # Execute with timeout handling
        try:
            response = loop.run_until_complete(
                asyncio.wait_for(_generate(), timeout=500)
            )
        except asyncio.TimeoutError:
            raise SoftTimeLimitExceeded("AI generation timeout")
        finally:
            loop.close()
        
        # Store result
        result_data = {
            "prd": response.content,
            "metadata": {
                "model": response.model,
                "provider": response.provider,
                "tokens_used": response.usage.get("total_tokens", 0),
                "generated_at": datetime.utcnow().isoformat()
            }
        }
        
        update_job_status(
            job_id,
            'completed',
            result_data=result_data,
            completed_at=datetime.utcnow()
        )
        
        # Send completion notification
        send_completion_notification(user_id, job_id, product_name)
        
        return {"job_id": job_id, "status": "completed"}
        
    except SoftTimeLimitExceeded:
        logger.error(f"Job {job_id} exceeded time limit")
        raise self.retry(countdown=120, max_retries=1)
    
    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}")
        update_job_status(job_id, 'failed', error_message=str(e))
        
        # Retry with exponential backoff
        raise self.retry(exc=e)

def update_job_status(job_id: str, status: str, **kwargs):
    """Update job status in database"""
    from backend.src.core.database import get_db_sync
    
    db = next(get_db_sync())
    try:
        update_data = {"status": status, **kwargs}
        db.execute(
            """
            UPDATE ai_generation_jobs 
            SET status = :status, 
                started_at = :started_at,
                completed_at = :completed_at,
                result_data = :result_data,
                error_message = :error_message,
                metadata = metadata || :metadata
            WHERE id = :job_id
            """,
            {
                "job_id": job_id,
                "status": status,
                "started_at": kwargs.get("started_at"),
                "completed_at": kwargs.get("completed_at"),
                "result_data": json.dumps(kwargs.get("result_data")) if kwargs.get("result_data") else None,
                "error_message": kwargs.get("error_message"),
                "metadata": json.dumps(kwargs.get("metadata", {}))
            }
        )
        db.commit()
    finally:
        db.close()
```

#### 2.3 Enhanced API Endpoints
```python
# backend/src/api/v1/ai_async.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sse_starlette.sse import EventSourceResponse
import asyncio
import uuid

router = APIRouter(prefix="/ai/async", tags=["AI Async"])

@router.post("/generate/prd")
async def start_prd_generation(
    request: PRDGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Start asynchronous PRD generation.
    Returns immediately with job ID for polling/streaming.
    """
    # Create job record
    job_id = str(uuid.uuid4())
    
    job = AIGenerationJob(
        id=job_id,
        user_id=current_user.id,
        job_type='prd_generation',
        status='pending',
        request_data={
            "product_name": request.product_name,
            "description": request.description,
            "target_audience": request.target_audience,
            "key_features": request.key_features,
            "constraints": request.constraints
        }
    )
    db.add(job)
    await db.commit()
    
    # Queue the task
    generate_prd_task.apply_async(
        kwargs={
            "job_id": job_id,
            "user_id": current_user.id,
            "product_name": request.product_name,
            "description": request.description,
            "target_audience": request.target_audience,
            "key_features": request.key_features,
            "constraints": request.constraints,
            "provider": request.provider
        },
        queue='ai_generation',
        priority=get_user_priority(current_user)
    )
    
    return {
        "job_id": job_id,
        "status": "pending",
        "status_url": f"/api/v1/ai/async/jobs/{job_id}",
        "stream_url": f"/api/v1/ai/async/jobs/{job_id}/stream",
        "estimated_time": estimate_generation_time(request)
    }

@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get job status and result if completed."""
    job = await db.get(AIGenerationJob, job_id)
    
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    
    response = {
        "job_id": job.id,
        "status": job.status,
        "created_at": job.created_at.isoformat(),
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "progress": calculate_progress(job)
    }
    
    if job.status == 'completed' and job.result_data:
        response["result"] = job.result_data
    elif job.status == 'failed':
        response["error"] = job.error_message
    
    return response

@router.get("/jobs/{job_id}/stream")
async def stream_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Server-Sent Events stream for real-time job updates.
    """
    # Verify job ownership
    job = await db.get(AIGenerationJob, job_id)
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    
    async def event_generator():
        """Generate SSE events for job status updates."""
        last_status = None
        retry_count = 0
        max_retries = 360  # 30 minutes max (5 second intervals)
        
        while retry_count < max_retries:
            # Refresh job from database
            await db.refresh(job)
            
            # Send update if status changed
            if job.status != last_status:
                event_data = {
                    "status": job.status,
                    "progress": calculate_progress(job),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                if job.status == 'completed' and job.result_data:
                    event_data["result"] = job.result_data
                elif job.status == 'failed':
                    event_data["error"] = job.error_message
                
                yield {
                    "event": "status_update",
                    "data": json.dumps(event_data),
                    "retry": 5000  # Reconnect after 5 seconds if connection drops
                }
                
                last_status = job.status
                
                # Exit loop if job is done
                if job.status in ['completed', 'failed', 'cancelled']:
                    yield {
                        "event": "close",
                        "data": json.dumps({"reason": "job_finished"})
                    }
                    break
            
            # Send heartbeat every 30 seconds
            if retry_count % 6 == 0:
                yield {
                    "event": "heartbeat",
                    "data": json.dumps({"timestamp": datetime.utcnow().isoformat()})
                }
            
            await asyncio.sleep(5)
            retry_count += 1
        
        # Timeout reached
        if retry_count >= max_retries:
            yield {
                "event": "error",
                "data": json.dumps({"error": "Stream timeout", "job_id": job_id})
            }
    
    return EventSourceResponse(event_generator())

def calculate_progress(job: AIGenerationJob) -> float:
    """Calculate estimated progress based on elapsed time."""
    if job.status == 'completed':
        return 100.0
    elif job.status == 'failed':
        return 0.0
    elif job.status == 'pending':
        return 0.0
    elif job.status == 'processing' and job.started_at:
        # Estimate based on typical duration (45 seconds)
        elapsed = (datetime.utcnow() - job.started_at).total_seconds()
        estimated_duration = 45.0
        progress = min((elapsed / estimated_duration) * 100, 95.0)
        return round(progress, 2)
    return 0.0

def estimate_generation_time(request: PRDGenerationRequest) -> int:
    """Estimate generation time in seconds based on request complexity."""
    base_time = 30
    
    # Add time based on content length
    complexity_factors = [
        len(request.description) / 100,  # Longer descriptions take more time
        len(request.key_features) * 2,   # Each feature adds complexity
        len(request.constraints or []) * 1.5  # Constraints require careful consideration
    ]
    
    estimated_time = base_time + sum(complexity_factors)
    
    # Cap at 2 minutes
    return min(int(estimated_time), 120)

def get_user_priority(user: User) -> int:
    """Determine queue priority based on user tier."""
    priority_map = {
        'enterprise': 9,
        'premium': 7,
        'standard': 5,
        'free': 3
    }
    return priority_map.get(user.subscription_tier, 5)
```

### Phase 3: Frontend Implementation with Progressive Enhancement

#### 3.1 React Hook for Async Job Management
```typescript
// frontend/src/hooks/useAsyncJob.ts
import { useState, useEffect, useCallback, useRef } from 'react'
import { EventSourcePolyfill } from 'event-source-polyfill'

interface AsyncJobOptions {
  pollingInterval?: number
  maxPollingAttempts?: number
  onProgress?: (progress: number) => void
  onStatusChange?: (status: string) => void
  useSSE?: boolean
}

interface AsyncJobResult<T> {
  status: 'idle' | 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  result?: T
  error?: string
  startTime?: Date
  endTime?: Date
}

export function useAsyncJob<T>(
  startJobFn: () => Promise<{ job_id: string; status_url: string; stream_url?: string }>,
  options: AsyncJobOptions = {}
) {
  const {
    pollingInterval = 5000,
    maxPollingAttempts = 60,
    onProgress,
    onStatusChange,
    useSSE = true
  } = options

  const [state, setState] = useState<AsyncJobResult<T>>({
    status: 'idle',
    progress: 0
  })

  const [jobId, setJobId] = useState<string | null>(null)
  const eventSourceRef = useRef<EventSource | null>(null)
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null)

  // Start job
  const startJob = useCallback(async () => {
    try {
      setState({ status: 'pending', progress: 0, startTime: new Date() })
      
      const { job_id, status_url, stream_url } = await startJobFn()
      setJobId(job_id)
      
      // Use SSE if available and supported
      if (useSSE && stream_url && typeof EventSource !== 'undefined') {
        startSSEConnection(stream_url)
      } else {
        // Fallback to polling
        startPolling(status_url)
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        status: 'failed',
        error: error instanceof Error ? error.message : 'Failed to start job',
        endTime: new Date()
      }))
    }
  }, [startJobFn, useSSE])

  // SSE connection
  const startSSEConnection = (streamUrl: string) => {
    const token = getAuthToken() // Implement based on your auth
    
    eventSourceRef.current = new EventSourcePolyfill(streamUrl, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    eventSourceRef.current.addEventListener('status_update', (event: any) => {
      const data = JSON.parse(event.data)
      updateState(data)
    })

    eventSourceRef.current.addEventListener('heartbeat', () => {
      // Keep connection alive
    })

    eventSourceRef.current.addEventListener('close', () => {
      eventSourceRef.current?.close()
      eventSourceRef.current = null
    })

    eventSourceRef.current.addEventListener('error', (event: any) => {
      console.error('SSE error:', event)
      // Fallback to polling
      eventSourceRef.current?.close()
      if (jobId) {
        startPolling(`/api/v1/ai/async/jobs/${jobId}`)
      }
    })
  }

  // Polling fallback
  const startPolling = (statusUrl: string) => {
    let attempts = 0

    const poll = async () => {
      try {
        const response = await fetch(statusUrl, {
          headers: {
            'Authorization': `Bearer ${getAuthToken()}`
          }
        })
        
        if (!response.ok) {
          throw new Error('Failed to fetch job status')
        }

        const data = await response.json()
        updateState(data)

        if (data.status === 'completed' || data.status === 'failed') {
          // Stop polling
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current)
            pollingIntervalRef.current = null
          }
        } else if (attempts >= maxPollingAttempts) {
          // Timeout
          setState(prev => ({
            ...prev,
            status: 'failed',
            error: 'Job timed out',
            endTime: new Date()
          }))
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current)
          }
        }

        attempts++
      } catch (error) {
        console.error('Polling error:', error)
        // Continue polling unless max attempts reached
        if (attempts >= maxPollingAttempts) {
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current)
          }
          setState(prev => ({
            ...prev,
            status: 'failed',
            error: 'Failed to get job status',
            endTime: new Date()
          }))
        }
      }
    }

    // Start polling
    poll() // Initial poll
    pollingIntervalRef.current = setInterval(poll, pollingInterval)
  }

  // Update state based on job data
  const updateState = (data: any) => {
    const newState: AsyncJobResult<T> = {
      status: data.status,
      progress: data.progress || 0
    }

    if (data.status === 'completed' && data.result) {
      newState.result = data.result as T
      newState.endTime = new Date()
    } else if (data.status === 'failed') {
      newState.error = data.error || 'Job failed'
      newState.endTime = new Date()
    }

    setState(prev => ({ ...prev, ...newState }))

    // Callbacks
    if (onProgress && newState.progress !== state.progress) {
      onProgress(newState.progress)
    }
    if (onStatusChange && newState.status !== state.status) {
      onStatusChange(newState.status)
    }
  }

  // Cleanup
  useEffect(() => {
    return () => {
      eventSourceRef.current?.close()
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current)
      }
    }
  }, [])

  return {
    ...state,
    startJob,
    jobId,
    isLoading: state.status === 'pending' || state.status === 'processing',
    duration: state.startTime && state.endTime 
      ? state.endTime.getTime() - state.startTime.getTime() 
      : undefined
  }
}

// Helper function - implement based on your auth setup
function getAuthToken(): string {
  // Return the current auth token
  return localStorage.getItem('authToken') || ''
}
```

#### 3.2 Enhanced PRD Generation Component
```tsx
// frontend/src/app/app/prds/new/AsyncPRDGeneration.tsx
import { useAsyncJob } from '@/hooks/useAsyncJob'
import { Progress } from '@/components/ui/progress'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { CheckCircle2, Loader2, AlertCircle, Clock } from 'lucide-react'

export function AsyncPRDGeneration({ formData, onComplete }) {
  const {
    status,
    progress,
    result,
    error,
    startJob,
    duration
  } = useAsyncJob(
    async () => {
      const response = await api.ai.generatePRDAsync(formData)
      return response
    },
    {
      useSSE: true,
      onProgress: (progress) => {
        console.log(`Generation progress: ${progress}%`)
      },
      onStatusChange: (status) => {
        console.log(`Status changed to: ${status}`)
      }
    }
  )

  // Auto-save when completed
  useEffect(() => {
    if (status === 'completed' && result) {
      onComplete(result)
    }
  }, [status, result, onComplete])

  return (
    <div className="space-y-4">
      {/* Status Display */}
      <div className="flex items-center gap-3">
        {status === 'pending' && (
          <>
            <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
            <span>Initializing PRD generation...</span>
          </>
        )}
        {status === 'processing' && (
          <>
            <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
            <span>Generating PRD with AI...</span>
          </>
        )}
        {status === 'completed' && (
          <>
            <CheckCircle2 className="h-5 w-5 text-green-500" />
            <span>PRD generated successfully!</span>
          </>
        )}
        {status === 'failed' && (
          <>
            <AlertCircle className="h-5 w-5 text-red-500" />
            <span>Generation failed</span>
          </>
        )}
      </div>

      {/* Progress Bar */}
      {(status === 'pending' || status === 'processing') && (
        <div className="space-y-2">
          <Progress value={progress} className="h-2" />
          <p className="text-sm text-muted-foreground">
            {progress.toFixed(0)}% complete
            {progress > 0 && progress < 100 && (
              <span className="ml-2">
                • Estimated time remaining: {estimateTimeRemaining(progress)}
              </span>
            )}
          </p>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Success Display */}
      {status === 'completed' && result && (
        <div className="space-y-3">
          <Alert variant="default" className="border-green-200 bg-green-50">
            <CheckCircle2 className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-800">
              PRD generated successfully in {formatDuration(duration)}
            </AlertDescription>
          </Alert>
          
          <Card>
            <CardHeader>
              <CardTitle>Generated PRD</CardTitle>
              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                <span>Provider: {result.metadata?.provider}</span>
                <span>Model: {result.metadata?.model}</span>
                <span>Tokens: {result.metadata?.tokens_used}</span>
              </div>
            </CardHeader>
            <CardContent>
              <div className="prose prose-sm max-w-none">
                <pre className="whitespace-pre-wrap">{result.prd}</pre>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Retry Button */}
      {status === 'failed' && (
        <Button onClick={startJob} variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />
          Retry Generation
        </Button>
      )}
    </div>
  )
}

function estimateTimeRemaining(progress: number): string {
  if (progress === 0) return 'calculating...'
  
  // Assume 45 seconds average
  const estimatedTotal = 45
  const elapsed = (progress / 100) * estimatedTotal
  const remaining = estimatedTotal - elapsed
  
  if (remaining < 10) return 'a few seconds'
  if (remaining < 30) return `${Math.round(remaining)} seconds`
  return `${Math.round(remaining / 60)} minute${remaining > 60 ? 's' : ''}`
}

function formatDuration(ms?: number): string {
  if (!ms) return ''
  
  const seconds = Math.floor(ms / 1000)
  if (seconds < 60) return `${seconds} seconds`
  
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}m ${remainingSeconds}s`
}
```

### Phase 4: Monitoring and Observability

#### 4.1 Prometheus Metrics
```python
# backend/src/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge, Info

# AI Generation Metrics
ai_generation_requests = Counter(
    'ai_generation_requests_total',
    'Total number of AI generation requests',
    ['job_type', 'provider', 'status']
)

ai_generation_duration = Histogram(
    'ai_generation_duration_seconds',
    'AI generation duration in seconds',
    ['job_type', 'provider'],
    buckets=[5, 10, 20, 30, 45, 60, 90, 120, 180, 300]
)

ai_generation_queue_size = Gauge(
    'ai_generation_queue_size',
    'Current size of AI generation queue',
    ['queue_name', 'priority']
)

ai_generation_active_jobs = Gauge(
    'ai_generation_active_jobs',
    'Number of currently processing AI generation jobs',
    ['job_type']
)

ai_generation_timeouts = Counter(
    'ai_generation_timeouts_total',
    'Total number of AI generation timeouts',
    ['job_type', 'provider', 'timeout_type']
)

# Cost Tracking
ai_generation_cost = Counter(
    'ai_generation_cost_dollars',
    'Estimated cost of AI generation in dollars',
    ['provider', 'model', 'user_tier']
)

ai_tokens_used = Counter(
    'ai_tokens_used_total',
    'Total tokens used for AI generation',
    ['provider', 'model', 'token_type']
)
```

#### 4.2 Grafana Dashboard Configuration
```json
{
  "dashboard": {
    "title": "AI Generation Performance",
    "panels": [
      {
        "title": "Request Success Rate",
        "targets": [{
          "expr": "rate(ai_generation_requests_total{status='completed'}[5m]) / rate(ai_generation_requests_total[5m])"
        }]
      },
      {
        "title": "P95 Generation Time",
        "targets": [{
          "expr": "histogram_quantile(0.95, rate(ai_generation_duration_seconds_bucket[5m]))"
        }]
      },
      {
        "title": "Active Jobs by Type",
        "targets": [{
          "expr": "ai_generation_active_jobs"
        }]
      },
      {
        "title": "Timeout Rate",
        "targets": [{
          "expr": "rate(ai_generation_timeouts_total[5m])"
        }]
      },
      {
        "title": "Cost per Hour",
        "targets": [{
          "expr": "increase(ai_generation_cost_dollars[1h])"
        }]
      }
    ]
  }
}
```

### Phase 5: Cost Optimization

#### 5.1 Intelligent Caching Layer
```python
# backend/src/services/ai_cache.py
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

class AIResponseCache:
    """
    Intelligent caching for AI responses with similarity matching.
    """
    
    def __init__(self, redis_client, similarity_threshold: float = 0.85):
        self.redis = redis_client
        self.similarity_threshold = similarity_threshold
    
    async def get_cached_response(
        self, 
        request_type: str,
        request_data: Dict[str, Any],
        max_age_hours: int = 24
    ) -> Optional[Dict[str, Any]]:
        """
        Check for cached similar responses.
        """
        # Generate cache key
        cache_key = self._generate_cache_key(request_type, request_data)
        
        # Try exact match first
        cached = await self.redis.get(f"ai_cache:{cache_key}")
        if cached:
            data = json.loads(cached)
            if self._is_cache_valid(data, max_age_hours):
                return data
        
        # Try fuzzy matching for similar requests
        if request_type == 'prd_generation':
            similar = await self._find_similar_prd(request_data)
            if similar:
                return similar
        
        return None
    
    async def store_response(
        self,
        request_type: str,
        request_data: Dict[str, Any],
        response_data: Dict[str, Any]
    ):
        """Store response in cache with metadata."""
        cache_key = self._generate_cache_key(request_type, request_data)
        
        cache_data = {
            "request": request_data,
            "response": response_data,
            "cached_at": datetime.utcnow().isoformat(),
            "hit_count": 0
        }
        
        # Store with 7-day expiration
        await self.redis.setex(
            f"ai_cache:{cache_key}",
            7 * 24 * 3600,
            json.dumps(cache_data)
        )
        
        # Store in similarity index
        if request_type == 'prd_generation':
            await self._index_for_similarity(request_data, cache_key)
    
    def _generate_cache_key(self, request_type: str, request_data: Dict[str, Any]) -> str:
        """Generate deterministic cache key."""
        # Sort keys for consistency
        sorted_data = json.dumps(request_data, sort_keys=True)
        return hashlib.sha256(f"{request_type}:{sorted_data}".encode()).hexdigest()
    
    def _is_cache_valid(self, cache_data: Dict[str, Any], max_age_hours: int) -> bool:
        """Check if cached data is still valid."""
        cached_at = datetime.fromisoformat(cache_data['cached_at'])
        age = datetime.utcnow() - cached_at
        return age < timedelta(hours=max_age_hours)
    
    async def _find_similar_prd(self, request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find similar PRD requests using vector similarity."""
        # This would use embeddings for similarity matching
        # Simplified version using keyword matching
        
        keywords = set()
        keywords.update(request_data.get('product_name', '').lower().split())
        keywords.update(request_data.get('target_audience', '').lower().split())
        
        # Search for cached PRDs with similar keywords
        pattern = f"ai_cache:*"
        cursor = 0
        best_match = None
        best_score = 0
        
        while cursor != 0 or best_match is None:
            cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
            
            for key in keys:
                cached = await self.redis.get(key)
                if cached:
                    data = json.loads(cached)
                    if self._is_cache_valid(data, 168):  # 7 days for similar matches
                        score = self._calculate_similarity(keywords, data['request'])
                        if score > best_score and score > self.similarity_threshold:
                            best_score = score
                            best_match = data
            
            if cursor == 0:
                break
        
        return best_match
    
    def _calculate_similarity(self, keywords: set, request_data: Dict[str, Any]) -> float:
        """Calculate simple keyword similarity score."""
        request_keywords = set()
        request_keywords.update(request_data.get('product_name', '').lower().split())
        request_keywords.update(request_data.get('target_audience', '').lower().split())
        
        if not keywords or not request_keywords:
            return 0.0
        
        intersection = keywords & request_keywords
        union = keywords | request_keywords
        
        return len(intersection) / len(union)
```

## Implementation Checklist

### Week 1 - Immediate Fixes
- [ ] Update frontend timeout to 120 seconds
- [ ] Update backend LLM timeout configuration
- [ ] Update Kubernetes ingress timeouts
- [ ] Deploy and test with Claude AI
- [ ] Monitor error rates and success metrics

### Week 2 - Asynchronous Infrastructure
- [ ] Create database schema for job tracking
- [ ] Implement Celery tasks for AI generation
- [ ] Create async API endpoints
- [ ] Implement basic polling in frontend
- [ ] Deploy to staging environment

### Week 3 - Real-time Updates
- [ ] Implement SSE endpoints
- [ ] Add WebSocket support
- [ ] Create React hooks for real-time updates
- [ ] Implement progress tracking
- [ ] Add retry mechanisms

### Week 4 - Monitoring & Optimization
- [ ] Deploy Prometheus metrics
- [ ] Create Grafana dashboards
- [ ] Implement caching layer
- [ ] Add cost tracking
- [ ] Performance optimization

## Success Metrics

1. **Availability**: 99.9% uptime for AI generation service
2. **Performance**: P95 response time < 60 seconds
3. **Success Rate**: > 95% successful PRD generations
4. **Cost Efficiency**: 30% reduction through caching
5. **User Satisfaction**: < 5% timeout-related complaints

## Risk Mitigation

1. **Timeout Cascades**: Implement circuit breakers
2. **Cost Overruns**: Set per-user daily limits
3. **Queue Backlogs**: Auto-scaling workers
4. **API Rate Limits**: Request queuing and retry
5. **Data Loss**: Persistent job storage