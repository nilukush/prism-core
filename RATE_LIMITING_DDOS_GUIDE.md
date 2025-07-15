# Enterprise Rate Limiting & DDoS Protection Guide

## Overview

PRISM implements a multi-layered defense strategy combining sophisticated rate limiting with advanced DDoS protection. This enterprise-grade solution protects against various attack vectors while maintaining excellent performance for legitimate users.

## Architecture

### Defense Layers

```
┌─────────────────────────────────────────┐
│         Layer 1: IP Whitelist           │
├─────────────────────────────────────────┤
│         Layer 2: IP Blacklist           │
├─────────────────────────────────────────┤
│      Layer 3: Geographic Filter         │
├─────────────────────────────────────────┤
│    Layer 4: Traffic Pattern Analysis    │
├─────────────────────────────────────────┤
│    Layer 5: Challenge-Response (JS)     │
├─────────────────────────────────────────┤
│      Layer 6: Connection Limiting       │
├─────────────────────────────────────────┤
│      Layer 7: Rate Limiting            │
├─────────────────────────────────────────┤
│         Application Layer               │
└─────────────────────────────────────────┘
```

## Rate Limiting

### Token Bucket Algorithm

The default strategy uses a token bucket algorithm that allows burst traffic while maintaining average rate limits.

**Benefits:**
- Handles legitimate traffic bursts
- Smooth rate limiting
- Memory efficient
- Fair resource allocation

**Configuration:**
```python
# Per-endpoint configuration
AUTH_ENDPOINTS = RateLimitConfig(
    requests_per_second=2,
    requests_per_minute=10,
    requests_per_hour=100,
    requests_per_day=500,
    burst_size=5
)

AI_ENDPOINTS = RateLimitConfig(
    requests_per_second=1,
    requests_per_minute=5,
    requests_per_hour=50,
    requests_per_day=200,
    burst_size=3
)
```

### Sliding Window Algorithm

Alternative strategy for more precise rate limiting.

**Benefits:**
- More accurate rate enforcement
- No fixed window bias
- Better for strict limits

**Trade-offs:**
- Higher memory usage
- More Redis operations

### Rate Limit Headers

All responses include standard rate limit headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1625097600
X-RateLimit-Burst: 20
```

### Client Identification

Rate limits are applied based on a composite key:
1. IP address (considering proxies)
2. Authenticated user ID
3. API key (if provided)

This prevents circumvention through multiple accounts or API keys.

## DDoS Protection

### 1. IP Reputation System

**Whitelist:**
- Trusted IPs bypass most checks
- Internal services
- Known partners

**Blacklist:**
- Malicious IPs blocked immediately
- Temporary blocks with expiration
- Automatic blacklisting on pattern detection

### 2. Geographic Filtering

**Features:**
- Country-based access control
- High-risk country detection
- Configurable allow/block lists

**Configuration:**
```python
GEO_FILTER = {
    "allowed_countries": ["US", "CA", "GB", "DE", "FR"],
    "blocked_countries": ["XX"],  # Explicit blocks
    "high_risk_countries": ["CN", "RU", "KP", "IR"]
}
```

### 3. Traffic Pattern Analysis

**Anomaly Detection:**
- Request flooding (>100 requests/5 min)
- Path scanning (>50 unique paths/5 min)
- Bot-like regular intervals
- Suspicious user agents

**Statistical Analysis:**
- Inter-request timing variance
- Request size patterns
- Method distribution
- Path entropy

### 4. JavaScript Challenge

When suspicious activity is detected, clients receive a computational challenge:

**Process:**
1. Client receives HTML with JavaScript challenge
2. Browser solves proof-of-work puzzle
3. Solution submitted automatically
4. Valid solution grants access

**Benefits:**
- Filters out simple bots
- Minimal impact on real users
- No CAPTCHA friction

### 5. Connection Limiting

Per-IP connection limits prevent resource exhaustion:
- Max 100 connections per minute
- Automatic scaling based on reputation
- Gradual limit increase for good actors

## Configuration

### Environment Variables

```bash
# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_STRATEGY=token_bucket
RATE_LIMIT_DEFAULT=100
RATE_LIMIT_WINDOW=3600

# DDoS Protection
DDOS_PROTECTION_ENABLED=true
DDOS_MAX_CONNECTIONS_PER_IP=100
DDOS_BLACKLIST_DURATION=3600
DDOS_CHALLENGE_ENABLED=true
BEHIND_PROXY=false  # Set true if behind reverse proxy

# Redis (required for distributed rate limiting)
REDIS_URL=redis://localhost:6379/0
```

### Per-Endpoint Configuration

Use decorators for custom limits:

```python
@router.post("/expensive-operation")
@rate_limit(requests_per_minute=5, strategy="sliding_window")
async def expensive_operation():
    ...
```

## Monitoring & Metrics

### Prometheus Metrics

```
# Rate limiting
rate_limit_hits_total{endpoint="/api/v1/auth/login", limit_type="token_bucket"}
rate_limit_requests_duration_seconds{endpoint="/api/v1/users"}

# DDoS protection
ddos_blocks_total{defense_layer="blacklist", reason="ip_blacklisted"}
ddos_challenges_total{challenge_type="javascript"}
traffic_anomalies_total{anomaly_type="request_flooding"}
blocked_ips_total{reason="suspicious_pattern"}
```

### Grafana Dashboards

Import the provided dashboards for real-time monitoring:
- Rate Limit Overview
- DDoS Attack Detection
- Geographic Traffic Analysis
- API Performance Impact

## Best Practices

### 1. Gradual Rollout

Start with generous limits and tighten based on analysis:
```
Week 1: 1000 requests/hour
Week 2: 500 requests/hour (analyze impact)
Week 3: 200 requests/hour (production limit)
```

### 2. User Communication

Provide clear feedback in rate limit responses:
```json
{
  "error": "Too many requests",
  "message": "Rate limit exceeded. Please retry after 60 seconds",
  "retry_after": 60,
  "upgrade_url": "https://prism.example.com/pricing"
}
```

### 3. Bypass Mechanisms

Implement bypass for critical services:
- Health checks
- Monitoring endpoints
- Internal service communication
- Emergency access tokens

### 4. Testing

Regular testing ensures protection works:
```bash
# Test rate limiting
for i in {1..100}; do
  curl -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"test"}'
done

# Test DDoS protection
ab -n 1000 -c 100 http://localhost:8000/api/v1/users
```

## Troubleshooting

### Common Issues

**1. Legitimate Users Blocked**
- Check IP whitelist
- Review rate limit thresholds
- Analyze traffic patterns
- Consider geographic restrictions

**2. Redis Connection Issues**
- Verify Redis is running
- Check connection string
- Monitor Redis memory usage
- Review Redis persistence settings

**3. High Memory Usage**
- Switch from sliding window to token bucket
- Reduce pattern analysis window
- Implement Redis key expiration
- Use Redis memory optimization

### Debug Mode

Enable detailed logging:
```python
RATE_LIMIT_DEBUG=true
DDOS_DEBUG_MODE=true
LOG_LEVEL=DEBUG
```

## Performance Impact

### Benchmarks

| Protection Level | Latency Impact | CPU Impact | Memory Impact |
|-----------------|----------------|------------|---------------|
| None | 0ms | 0% | 0MB |
| Rate Limit Only | 1-2ms | 1% | 10MB |
| Full DDoS Protection | 3-5ms | 5% | 50MB |
| Under Attack | 5-10ms | 15% | 200MB |

### Optimization Tips

1. **Use Redis Pipeline**: Batch operations for efficiency
2. **Cache GeoIP Lookups**: 24-hour TTL reduces API calls
3. **Async Everything**: Non-blocking operations throughout
4. **Connection Pooling**: Reuse Redis connections

## Integration Examples

### Nginx Configuration

```nginx
# Pass real IP to application
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

# Rate limiting at edge
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req zone=api burst=20 nodelay;
```

### CloudFlare Integration

```javascript
// Worker script for edge protection
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  const ip = request.headers.get('CF-Connecting-IP')
  
  // Check CloudFlare threat score
  if (request.headers.get('CF-Threat-Score') > 40) {
    return new Response('Access Denied', { status: 403 })
  }
  
  return fetch(request)
}
```

## Advanced Features

### 1. Adaptive Rate Limiting

Automatically adjust limits based on:
- Time of day
- System load
- User reputation
- Historical patterns

### 2. Machine Learning Integration

Future enhancement for pattern detection:
- Anomaly detection models
- Behavioral analysis
- Predictive blocking
- False positive reduction

### 3. Distributed Rate Limiting

For multi-region deployments:
- Global rate limit synchronization
- Regional limit policies
- Cross-region attack coordination
- Edge computing integration

## Compliance & Legal

### GDPR Compliance
- IP addresses treated as PII
- Automatic data expiration
- Right to erasure support
- Audit trail maintenance

### Industry Standards
- OWASP Rate Limiting Guidelines
- NIST DDoS Mitigation
- PCI DSS Requirements
- SOC 2 Controls

## Support

### Getting Help
- **Documentation**: Internal wiki
- **Slack Channel**: #security-ops
- **On-Call**: Security team rotation
- **Escalation**: security@prism.example.com

---

Last Updated: 2025-07-08
Version: 1.0.0