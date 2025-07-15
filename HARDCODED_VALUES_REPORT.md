# Critical Hardcoded Values Report - PRISM Platform

## Executive Summary

This report identifies all hardcoded values in the PRISM codebase that must be made configurable for enterprise deployment. Critical security issues include hardcoded passwords, secrets, and credentials that pose immediate risks.

## 🚨 CRITICAL SECURITY ISSUES (Immediate Action Required)

### 1. **Hardcoded Redis Password**
- **File**: `redis.conf`
- **Line**: 5
- **Value**: `requirepass redis_password`
- **Risk**: HIGH - Exposed credential in configuration file
- **Solution**: Use environment variable or secrets management
```bash
# redis.conf
requirepass ${REDIS_PASSWORD}

# docker-compose.yml
environment:
  - REDIS_PASSWORD=${REDIS_PASSWORD:-changeme}
```

### 2. **Hardcoded JWT Secret Key**
- **File**: `docker-compose.enterprise.yml`
- **Line**: 12
- **Value**: `SECRET_KEY=gJDZJmMehEKvca9pfj5bfvh-oSrsK7aqSNqNfQXgRvU`
- **Risk**: CRITICAL - Exposed signing key allows token forgery
- **Solution**: Generate unique secret per environment
```yaml
environment:
  - SECRET_KEY=${JWT_SECRET_KEY}  # Must be set in .env file
```

### 3. **Hardcoded Database Credentials**
- **File**: `backend/src/core/config.py`
- **Line**: 51
- **Value**: `postgresql+asyncpg://postgres:postgres@localhost:5432/prism_dev`
- **Risk**: HIGH - Exposed database credentials
- **Solution**: Already uses environment variable, but default is insecure

## 📊 Hardcoded Configuration Values

### Session Management (`backend/src/services/session_manager.py`)
```python
# Current hardcoded values:
self._session_ttl = 86400 * 7  # 7 days
self._token_family_ttl = 86400 * 30  # 30 days
self._blacklist_ttl = 86400 * 7  # 7 days
self._lock_ttl = 30  # 30 seconds
self._session_id_bytes = 32  # 256 bits
max_retries = 5
retry_delay = 1
```

**Enterprise Solution**:
```python
# session_manager.py
class EnterpriseSessionManager:
    def __init__(self, redis_url: Optional[str] = None, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Use configuration with secure defaults
        self._session_ttl = self.config.get('session_ttl', settings.SESSION_TTL)
        self._token_family_ttl = self.config.get('token_family_ttl', settings.TOKEN_FAMILY_TTL)
        self._blacklist_ttl = self.config.get('blacklist_ttl', settings.BLACKLIST_TTL)
        self._lock_ttl = self.config.get('lock_ttl', settings.REDIS_LOCK_TTL)
        self._session_id_bytes = self.config.get('session_id_bytes', settings.SESSION_ID_BYTES)

# config.py additions
SESSION_TTL: int = int(os.getenv('SESSION_TTL', str(86400 * 7)))  # 7 days default
TOKEN_FAMILY_TTL: int = int(os.getenv('TOKEN_FAMILY_TTL', str(86400 * 30)))  # 30 days
BLACKLIST_TTL: int = int(os.getenv('BLACKLIST_TTL', str(86400 * 7)))  # 7 days
REDIS_LOCK_TTL: int = int(os.getenv('REDIS_LOCK_TTL', '30'))  # 30 seconds
SESSION_ID_BYTES: int = int(os.getenv('SESSION_ID_BYTES', '32'))  # 256 bits
REDIS_RETRY_MAX: int = int(os.getenv('REDIS_RETRY_MAX', '5'))
REDIS_RETRY_DELAY: int = int(os.getenv('REDIS_RETRY_DELAY', '1'))
```

### Rate Limiting (`backend/src/middleware/rate_limiting.py`)
```python
# Current hardcoded values:
requests_per_second: int = 10
requests_per_minute: int = 100
requests_per_hour: int = 1000
requests_per_day: int = 10000
burst_size: int = 20
block_duration: int = 3600  # 1 hour

# Auth endpoint limits
auth_limits = RateLimitConfig(
    requests_per_second=2,
    requests_per_minute=10,
    requests_per_hour=100,
    requests_per_day=500,
    burst_size=5
)
```

**Enterprise Solution**:
```python
# config.py
# Rate limiting configuration
RATE_LIMIT_DEFAULT = {
    'requests_per_second': int(os.getenv('RATE_LIMIT_PER_SECOND', '10')),
    'requests_per_minute': int(os.getenv('RATE_LIMIT_PER_MINUTE', '100')),
    'requests_per_hour': int(os.getenv('RATE_LIMIT_PER_HOUR', '1000')),
    'requests_per_day': int(os.getenv('RATE_LIMIT_PER_DAY', '10000')),
    'burst_size': int(os.getenv('RATE_LIMIT_BURST', '20')),
    'block_duration': int(os.getenv('RATE_LIMIT_BLOCK_DURATION', '3600'))
}

RATE_LIMIT_AUTH = {
    'requests_per_second': int(os.getenv('RATE_LIMIT_AUTH_PER_SECOND', '2')),
    'requests_per_minute': int(os.getenv('RATE_LIMIT_AUTH_PER_MINUTE', '10')),
    'requests_per_hour': int(os.getenv('RATE_LIMIT_AUTH_PER_HOUR', '100')),
    'requests_per_day': int(os.getenv('RATE_LIMIT_AUTH_PER_DAY', '500')),
    'burst_size': int(os.getenv('RATE_LIMIT_AUTH_BURST', '5'))
}

RATE_LIMIT_AI = {
    'requests_per_second': int(os.getenv('RATE_LIMIT_AI_PER_SECOND', '1')),
    'requests_per_minute': int(os.getenv('RATE_LIMIT_AI_PER_MINUTE', '5')),
    'requests_per_hour': int(os.getenv('RATE_LIMIT_AI_PER_HOUR', '50')),
    'requests_per_day': int(os.getenv('RATE_LIMIT_AI_PER_DAY', '200')),
    'burst_size': int(os.getenv('RATE_LIMIT_AI_BURST', '3'))
}
```

### Security Headers (`backend/src/middleware/security.py`)
```python
# Current hardcoded CSP domains:
"script-src": "'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://www.googletagmanager.com",
"style-src": "'self' 'unsafe-inline' https://fonts.googleapis.com",
"font-src": "'self' https://fonts.gstatic.com data:",
"connect-src": "'self' https://api.openai.com https://api.anthropic.com wss://localhost:* ws://localhost:*",

# HSTS max-age
hsts_max_age = 31536000  # 1 year
```

**Enterprise Solution**:
```python
# config.py
CSP_DIRECTIVES = {
    'script-src': os.getenv('CSP_SCRIPT_SRC', "'self'"),
    'style-src': os.getenv('CSP_STYLE_SRC', "'self'"),
    'font-src': os.getenv('CSP_FONT_SRC', "'self'"),
    'connect-src': os.getenv('CSP_CONNECT_SRC', "'self'"),
    'img-src': os.getenv('CSP_IMG_SRC', "'self' data: https: blob:"),
    'media-src': os.getenv('CSP_MEDIA_SRC', "'self'"),
    'object-src': os.getenv('CSP_OBJECT_SRC', "'none'"),
    'frame-ancestors': os.getenv('CSP_FRAME_ANCESTORS', "'none'"),
    'base-uri': os.getenv('CSP_BASE_URI', "'self'"),
    'form-action': os.getenv('CSP_FORM_ACTION', "'self'")
}

HSTS_MAX_AGE: int = int(os.getenv('HSTS_MAX_AGE', '31536000'))  # 1 year default
HSTS_INCLUDE_SUBDOMAINS: bool = os.getenv('HSTS_INCLUDE_SUBDOMAINS', 'true').lower() == 'true'
HSTS_PRELOAD: bool = os.getenv('HSTS_PRELOAD', 'false').lower() == 'true'
```

## 🔧 Environment-Specific Values

### Frontend API Client (`frontend/src/lib/api-client.ts`)
```typescript
// Current hardcoded:
timeout = 30000  // 30 seconds
formData.append('grant_type', 'password')
```

**Enterprise Solution**:
```typescript
// config/api.config.ts
export const apiConfig = {
  timeout: {
    default: parseInt(process.env.NEXT_PUBLIC_API_TIMEOUT || '30000'),
    upload: parseInt(process.env.NEXT_PUBLIC_API_UPLOAD_TIMEOUT || '300000'),
    download: parseInt(process.env.NEXT_PUBLIC_API_DOWNLOAD_TIMEOUT || '300000'),
  },
  oauth: {
    grantType: process.env.NEXT_PUBLIC_OAUTH_GRANT_TYPE || 'password',
    clientId: process.env.NEXT_PUBLIC_OAUTH_CLIENT_ID,
    scope: process.env.NEXT_PUBLIC_OAUTH_SCOPE || 'openid profile email',
  },
  retry: {
    attempts: parseInt(process.env.NEXT_PUBLIC_API_RETRY_ATTEMPTS || '3'),
    delay: parseInt(process.env.NEXT_PUBLIC_API_RETRY_DELAY || '1000'),
  }
};
```

### Frontend Auth (`frontend/src/lib/auth.ts`)
```typescript
// Current hardcoded:
Date.now() + 30 * 60 * 1000  // 30 minutes
maxAge: 30 * 24 * 60 * 60  // 30 days
```

**Enterprise Solution**:
```typescript
// config/auth.config.ts
export const authConfig = {
  token: {
    accessExpiry: parseInt(process.env.NEXT_PUBLIC_ACCESS_TOKEN_EXPIRY || '1800') * 1000,
    refreshExpiry: parseInt(process.env.NEXT_PUBLIC_REFRESH_TOKEN_EXPIRY || '2592000') * 1000,
    refreshBuffer: parseInt(process.env.NEXT_PUBLIC_TOKEN_REFRESH_BUFFER || '300') * 1000, // 5 min
  },
  session: {
    maxAge: parseInt(process.env.NEXT_PUBLIC_SESSION_MAX_AGE || '2592000'), // 30 days
    updateAge: parseInt(process.env.NEXT_PUBLIC_SESSION_UPDATE_AGE || '86400'), // 24 hours
  },
  cookie: {
    secure: process.env.NODE_ENV === 'production',
    sameSite: (process.env.NEXT_PUBLIC_COOKIE_SAME_SITE || 'lax') as 'lax' | 'strict' | 'none',
    domain: process.env.NEXT_PUBLIC_COOKIE_DOMAIN,
    path: process.env.NEXT_PUBLIC_COOKIE_PATH || '/',
  }
};
```

## 📋 Complete Environment Variables Template

Create `.env.production` with all required variables:

```bash
# Application
APP_NAME=PRISM
APP_VERSION=0.1.0
APP_ENV=production
NODE_ENV=production

# Security - CRITICAL: Generate unique values per environment
SECRET_KEY=<generate-with-openssl-rand-base64-32>
JWT_SECRET_KEY=${SECRET_KEY}
ENCRYPTION_KEY=<generate-with-openssl-rand-base64-32>
NEXTAUTH_SECRET=<generate-with-openssl-rand-base64-32>

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
DATABASE_POOL_TIMEOUT=30

# Redis
REDIS_URL=redis://:password@redis:6379/0
REDIS_PASSWORD=<strong-password>
REDIS_POOL_SIZE=10
SESSION_TTL=604800  # 7 days
TOKEN_FAMILY_TTL=2592000  # 30 days
BLACKLIST_TTL=604800  # 7 days

# URLs
FRONTEND_URL=https://app.example.com
BACKEND_URL=https://api.example.com
NEXT_PUBLIC_API_URL=https://api.example.com
NEXT_PUBLIC_APP_URL=https://app.example.com

# Rate Limiting
RATE_LIMIT_PER_SECOND=10
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=1000
RATE_LIMIT_PER_DAY=10000
RATE_LIMIT_BURST=20
RATE_LIMIT_BLOCK_DURATION=3600

# Auth Rate Limits (stricter)
RATE_LIMIT_AUTH_PER_SECOND=2
RATE_LIMIT_AUTH_PER_MINUTE=10
RATE_LIMIT_AUTH_PER_HOUR=100
RATE_LIMIT_AUTH_PER_DAY=500

# AI Rate Limits (most restrictive)
RATE_LIMIT_AI_PER_SECOND=1
RATE_LIMIT_AI_PER_MINUTE=5
RATE_LIMIT_AI_PER_HOUR=50
RATE_LIMIT_AI_PER_DAY=200

# Security Headers
CSP_SCRIPT_SRC='self' 'nonce-{nonce}' https://cdn.jsdelivr.net
CSP_STYLE_SRC='self' 'nonce-{nonce}' https://fonts.googleapis.com
CSP_CONNECT_SRC='self' https://api.openai.com https://api.anthropic.com
HSTS_MAX_AGE=63072000  # 2 years
HSTS_INCLUDE_SUBDOMAINS=true
HSTS_PRELOAD=true

# Email
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=<sendgrid-api-key>
SMTP_FROM_EMAIL=noreply@example.com
SMTP_FROM_NAME=PRISM
EMAIL_VERIFICATION_EXPIRE=86400  # 24 hours
PASSWORD_RESET_EXPIRE=3600  # 1 hour

# Feature Flags
FEATURE_ANALYTICS_ENABLED=true
FEATURE_MARKETPLACE_ENABLED=false
FEATURE_ENTERPRISE_SSO_ENABLED=true
FEATURE_MULTI_TENANCY_ENABLED=true

# Monitoring
SENTRY_DSN=https://xxx@sentry.io/xxx
OTEL_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=https://otel-collector.example.com:4317
```

## 🚀 Implementation Priority

1. **Immediate (Security Critical)**:
   - Replace hardcoded Redis password
   - Remove hardcoded JWT secret from docker-compose.enterprise.yml
   - Secure all database connection strings

2. **High Priority (Deployment Blocking)**:
   - Make all TTL values configurable
   - Configure rate limits via environment
   - Set up environment-specific URLs

3. **Medium Priority (Operational)**:
   - Configure security headers
   - Set up feature flags
   - Configure email settings

4. **Low Priority (Enhancement)**:
   - Fine-tune cache TTLs
   - Optimize connection pool sizes
   - Configure monitoring endpoints

## 🔐 Security Best Practices

1. **Secrets Management**:
   ```bash
   # Generate secure secrets
   openssl rand -base64 32  # For SECRET_KEY
   openssl rand -hex 32     # For API keys
   ```

2. **Environment Separation**:
   ```bash
   # Use different values per environment
   .env.development
   .env.staging
   .env.production
   ```

3. **Runtime Validation**:
   ```python
   # Add to startup
   def validate_config():
       required = ['SECRET_KEY', 'DATABASE_URL', 'REDIS_URL']
       missing = [key for key in required if not os.getenv(key)]
       if missing:
           raise ValueError(f"Missing required config: {missing}")
   ```

4. **Secrets Rotation**:
   - Implement key rotation for JWT secrets
   - Rotate database passwords regularly
   - Update Redis passwords periodically

## 📝 Action Items

1. [ ] Create secure `.env.production` file
2. [ ] Update all hardcoded values to use environment variables
3. [ ] Implement configuration validation on startup
4. [ ] Document all configuration options
5. [ ] Set up secrets management system
6. [ ] Create configuration migration guide
7. [ ] Test all environments with new configuration
8. [ ] Update deployment scripts
9. [ ] Create monitoring for configuration issues
10. [ ] Implement configuration hot-reload where applicable