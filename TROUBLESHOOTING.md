# PRISM Troubleshooting Guide

## Frontend Stuck at "Checking backend connectivity..."

### Problem
When running `./start.sh`, the frontend gets stuck at "Checking backend connectivity..." and doesn't proceed.

### Root Causes
1. Backend container is unhealthy due to missing Python dependencies
2. Import errors in the backend code preventing it from starting
3. Frontend trying to use ports that are already in use

### Solution Steps

#### 1. Fix Backend Dependencies
The backend was failing due to missing Python packages required by the new enterprise features:

```bash
# Missing packages that need to be added to pyproject.toml:
aiosmtplib = "^3.0.1"
bleach = "^6.1.0"
jinja2 = "^3.1.3"
psutil = "^5.9.8"
python-json-logger = "^2.0.7"
opentelemetry-instrumentation-asyncpg = "^0.43b0"
opentelemetry-instrumentation-celery = "^0.43b0"
opentelemetry-exporter-otlp-proto-grpc = "^1.22.0"
python-magic = "^0.4.27"
```

#### 2. Fix Code Issues
Several code fixes were required:

1. **Email Service Import Handling**
   - Added graceful handling of optional dependencies in `email_service.py`
   - Created `email_simple.py` as a placeholder when dependencies are missing
   - Updated `auth.py` to fall back to simple email service

2. **Settings Access**
   - Changed `settings.get()` to `getattr(settings, ...)` throughout the codebase
   - Pydantic settings objects don't have a `.get()` method

3. **Missing Imports**
   - Added `import os` to `security.py`

#### 3. Rebuild Backend Container
```bash
# Rebuild the backend container with updated dependencies
docker compose build backend

# Restart the backend
docker compose restart backend

# Check logs
docker logs prism-backend --tail 50
```

#### 4. Fix Frontend Port Issues
The frontend was trying to use ports that were already in use:

1. Updated `package.json` to accept PORT environment variable:
   ```json
   "dev": "next dev -p ${PORT:-3100}",
   ```

2. Kill any processes using the desired port:
   ```bash
   lsof -i :3100
   kill -9 <PID>
   ```

3. Start frontend with specific port:
   ```bash
   cd frontend
   PORT=3100 ./start.sh dev
   ```

### Verification Steps

1. **Check Backend Health**
   ```bash
   curl http://localhost:8100/health
   # Should return: {"status":"healthy","version":"0.1.0","environment":"development"}
   ```

2. **Check Frontend**
   ```bash
   curl -I http://localhost:3100
   # Should return: HTTP/1.1 200 OK
   ```

3. **Check Docker Containers**
   ```bash
   docker ps
   # All containers should show as "healthy" or at least running
   ```

### Quick Fix Script
If you encounter this issue again, run these commands:

```bash
# 1. Restart backend
docker compose restart backend

# 2. Wait for backend to be healthy
sleep 10

# 3. Check backend health
curl http://localhost:8100/health

# 4. Kill any process on port 3100
lsof -i :3100 | grep LISTEN | awk '{print $2}' | xargs kill -9 2>/dev/null

# 5. Start frontend
cd frontend
PORT=3100 ./start.sh dev
```

### Prevention
1. Always check backend logs when frontend can't connect
2. Ensure all Python dependencies are properly defined in pyproject.toml
3. Use environment variables for port configuration
4. Implement proper health checks in both frontend and backend

## Common Docker Issues

### Container Unhealthy
If a container shows as "unhealthy", check its logs:
```bash
docker logs <container-name> --tail 100
```

### Database Connection Issues
If the backend can't connect to the database:
```bash
# Check if postgres is running
docker ps | grep postgres

# Check postgres logs
docker logs prism-postgres --tail 50

# Test connection
docker exec -it prism-postgres psql -U prism -d prism_db -c "SELECT 1"
```

### Redis Connection Issues
```bash
# Check if redis is running
docker ps | grep redis

# Test connection
docker exec -it prism-redis redis-cli ping
# Should return: PONG
```

## Port Conflicts

### Finding What's Using a Port
```bash
# On macOS/Linux
lsof -i :<port-number>

# On Windows
netstat -ano | findstr :<port-number>
```

### Common Port Assignments
- Frontend: 3100 (configurable via PORT env var)
- Backend API: 8100 (maps to container port 8000)
- PostgreSQL: 5433 (maps to container port 5432)
- Redis: 6380 (maps to container port 6379)
- Qdrant: 6334 (HTTP), 6335 (gRPC)

## Environment Variables

### Backend (.env)
Make sure your `.env` file has these essential variables:
```env
DATABASE_URL=postgresql+asyncpg://prism:prism_password@postgres:5432/prism_db
REDIS_URL=redis://:redis_password@redis:6379/0
SECRET_KEY=your-secret-key-here
EMAIL_ENABLED=true
RATE_LIMIT_ENABLED=false
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8100
NEXT_PUBLIC_APP_URL=http://localhost:3100
```