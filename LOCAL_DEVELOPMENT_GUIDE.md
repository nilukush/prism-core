# PRISM Local Development Guide

## Overview

This guide explains how to set up PRISM for local development with enterprise features enabled for testing, while maintaining developer-friendly defaults.

## Quick Start

```bash
# 1. Copy development environment file
cp .env.development .env

# 2. Start all services with development configuration
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 3. Start frontend development server
cd frontend
npm install
PORT=3100 npm run dev

# 4. Access the application
# Frontend: http://localhost:3100
# Backend API: http://localhost:8100
# API Docs: http://localhost:8100/docs
```

## Development Stack

### Core Services
- **Backend**: FastAPI with hot-reload enabled
- **Frontend**: Next.js with development server
- **Database**: PostgreSQL with query logging
- **Cache**: Redis with persistence and debugging
- **Session Storage**: Redis-backed enterprise sessions

### Optional Development Tools
```bash
# Start with debugging tools
docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile debug up -d

# This enables:
# - Redis Commander: http://localhost:8081
# - PGAdmin: http://localhost:5050
#   - Email: admin@local.dev
#   - Password: admin

# Start with email testing
docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile email up -d

# This enables:
# - MailHog: http://localhost:8025
```

## Key Differences from Production

### 1. **Security Settings**
- Fixed development secrets (never use in production)
- Relaxed CORS policies
- Disabled HSTS
- Permissive CSP headers

### 2. **Session Management**
- Shorter TTLs for faster testing:
  - Access tokens: 5 minutes (vs 30 min)
  - Refresh tokens: 1 hour (vs 7 days)
  - Sessions: 1 hour (vs 7 days)
- Session persistence enabled for testing

### 3. **Rate Limiting**
- Very permissive limits:
  - General: 100/sec, 1000/min
  - Auth: 10/sec, 100/min
  - AI: 5/sec, 50/min
- DDoS protection disabled

### 4. **Developer Features**
- Hot reload for backend and frontend
- Debug logging enabled
- Query logging for PostgreSQL
- Redis event notifications for debugging
- Source code mounted as volumes

## Why Use Enterprise Features Locally?

### ✅ **Enabled Features**
1. **Persistent Sessions**: Test session survival across restarts
2. **Token Rotation**: Verify refresh token security
3. **Rate Limiting**: Test API limits (with relaxed thresholds)
4. **Audit Logging**: Track security events
5. **Enterprise Auth Flow**: Test production authentication

### 🚫 **Disabled Features**
1. **External Monitoring**: Sentry, OpenTelemetry, Prometheus
2. **Email Verification**: Console output instead
3. **DDoS Protection**: Not needed locally
4. **SSL/TLS**: Use HTTP locally
5. **Multi-tenancy**: Simplified for development

## Common Development Tasks

### 1. **Reset Database**
```bash
# Stop services
docker compose -f docker-compose.yml -f docker-compose.dev.yml down

# Remove database volume
docker volume rm prism-core_postgres_data_dev

# Restart services (migrations run automatically)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### 2. **Clear Redis Cache**
```bash
docker exec -it prism-redis redis-cli -a redis_dev FLUSHALL
```

### 3. **View Backend Logs**
```bash
# All logs
docker compose logs -f backend

# Filter by level
docker compose logs backend | grep -E "(ERROR|WARNING)"

# Structured logs with jq
docker compose logs backend | jq 'select(.level=="error")'
```

### 4. **Test Session Persistence**
```bash
# Login
curl -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=nilukush@gmail.com&password=n1i6Lu!8"

# Restart backend
docker compose restart backend

# Token should still work after restart
```

### 5. **Debug Redis Sessions**
```bash
# Connect to Redis
docker exec -it prism-redis redis-cli -a redis_dev

# List all sessions
KEYS session:*

# View specific session
GET session:<session_id>

# Monitor Redis commands in real-time
MONITOR
```

### 6. **Add Test Data**
```bash
# Run seed script
docker compose exec backend python backend/scripts/seed_dev_data.py
```

## Environment Variables

### Essential for Local Development
```bash
# Already set in .env.development:
USE_PERSISTENT_SESSIONS=true    # Test enterprise features
DEBUG=true                      # Enable debug mode
LOG_LEVEL=DEBUG                 # Verbose logging
EMAIL_ENABLED=false             # No email in dev
RATE_LIMIT_ENABLED=true         # Test rate limiting
```

### Optional API Keys
```bash
# Add to .env if you want to test AI features:
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

## Troubleshooting

### Backend Won't Start
```bash
# Check logs
docker compose logs backend

# Common issues:
# - Database not ready: Wait a few seconds
# - Port conflict: Check if 8100 is in use
# - Migration error: Reset database
```

### Frontend Connection Issues
```bash
# Ensure backend is healthy
curl http://localhost:8100/health

# Check CORS settings
docker compose exec backend env | grep CORS

# Verify frontend env
cd frontend && cat .env.local
```

### Session/Auth Issues
```bash
# Clear all auth data
docker exec -it prism-redis redis-cli -a redis_dev
> FLUSHDB

# Check session config
curl http://localhost:8100/api/v1/auth/session/status \
  -H "Authorization: Bearer $TOKEN"
```

### Redis Connection Issues
```bash
# Test Redis connection
docker exec -it prism-redis redis-cli -a redis_dev PING

# Check Redis logs
docker compose logs redis
```

## Best Practices

1. **Always use `.env.development` as base** - Don't modify for personal settings
2. **Create `.env.local` for personal overrides** - Git ignored
3. **Test with realistic data** - Use seed scripts
4. **Verify enterprise features work** - Test session persistence
5. **Keep Docker images updated** - Run `docker compose pull` regularly
6. **Clean up regularly** - Remove unused volumes and images

## Moving to Production

When you're ready for production:

1. **Get a domain name**
2. **Generate real secrets**: `./scripts/generate-secrets.sh`
3. **Update `.env.production`** with your domain
4. **Use production compose files**:
   ```bash
   docker compose -f docker-compose.yml \
     -f docker-compose.enterprise.yml \
     -f docker-compose.production.yml up -d
   ```
5. **Enable SSL/TLS** with Let's Encrypt
6. **Configure monitoring** (Sentry, etc.)
7. **Set up backups** for PostgreSQL and Redis

## Summary

The development setup provides:
- ✅ Full enterprise features for testing
- ✅ Developer-friendly defaults
- ✅ Fast iteration with hot reload
- ✅ Debugging tools when needed
- ✅ Production-like behavior
- ✅ Simple commands

This approach follows enterprise best practices:
- **12-factor app principles**
- **Environment-based configuration**
- **Production parity where it matters**
- **Developer productivity optimizations**
- **Security-first mindset**

You get the best of both worlds: a development environment that's easy to use but closely mirrors production behavior for critical features like authentication and session management.