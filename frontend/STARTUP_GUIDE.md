# PRISM Frontend Startup Guide

## Quick Start (Development)

### Option 1: Direct Node.js (Fastest for Development)

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (if not already done)
npm install

# Start development server
npm run dev

# Or with specific port
PORT=3100 npm run dev

# Or with all environment variables
NEXT_PUBLIC_API_URL=http://localhost:8100 \
NEXT_PUBLIC_APP_URL=http://localhost:3100 \
npm run dev
```

**Access at:** http://localhost:3000 (or next available port)

### Option 2: Docker Development Mode

```bash
# From project root
docker compose --profile frontend up frontend

# Or run in background
docker compose --profile frontend up -d frontend

# View logs
docker compose logs -f frontend
```

**Access at:** http://localhost:3100

### Option 3: PM2 Process Manager (Production-like)

```bash
# Install PM2 globally
npm install -g pm2

# Create ecosystem file
cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [{
    name: 'prism-frontend',
    script: 'npm',
    args: 'start',
    cwd: './frontend',
    instances: 1,
    exec_mode: 'fork',
    env: {
      PORT: 3100,
      NODE_ENV: 'production',
      NEXT_PUBLIC_API_URL: 'http://localhost:8100',
      NEXT_PUBLIC_APP_URL: 'http://localhost:3100'
    }
  }]
};
EOF

# Build the application first
cd frontend && npm run build && cd ..

# Start with PM2
pm2 start ecosystem.config.js

# Monitor
pm2 monit
```

## Production Startup

### Step 1: Build for Production

```bash
cd frontend

# Clean previous builds
rm -rf .next

# Install production dependencies
npm ci --only=production

# Build with production optimizations
npm run build

# Analyze bundle size (optional)
ANALYZE=true npm run build
```

### Step 2: Configure Environment

Create `.env.production.local`:

```env
# API Configuration
NEXT_PUBLIC_API_URL=https://api.prism.yourdomain.com
NEXT_PUBLIC_APP_URL=https://app.prism.yourdomain.com
NEXT_PUBLIC_APP_NAME=PRISM

# Analytics (optional)
NEXT_PUBLIC_GA_MEASUREMENT_ID=G-XXXXXXXXXX
NEXT_PUBLIC_SENTRY_DSN=https://...@sentry.io/...

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_PWA=true
```

### Step 3: Start Production Server

```bash
# Option 1: Direct Node.js
PORT=3100 npm start

# Option 2: With PM2
pm2 start ecosystem.config.js --env production

# Option 3: Docker Production
docker compose -f docker-compose.prod.yml up -d frontend
```

## Health Checks

### 1. Frontend Health Endpoint

Check if frontend is running:
```bash
curl http://localhost:3100/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "prism-frontend",
  "version": "1.0.0",
  "timestamp": "2024-01-08T..."
}
```

### 2. Backend Connectivity Check

Verify frontend can reach backend:
```bash
# From frontend container/server
curl http://localhost:8100/health
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Port Already in Use
```bash
Error: Port 3000 is already in use
```

**Solution:**
```bash
# Find process using port
lsof -i :3000

# Kill process
kill -9 <PID>

# Or use different port
PORT=3100 npm run dev
```

#### 2. Module Not Found Errors
```bash
Error: Cannot find module 'xyz'
```

**Solution:**
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

#### 3. Next.js Build Errors
```bash
Error: Failed to compile
```

**Solution:**
```bash
# Check TypeScript errors
npm run type-check

# Fix linting issues
npm run lint:fix

# Clear Next.js cache
rm -rf .next
```

#### 4. Environment Variables Not Loading
```bash
# Check current environment variables
npm run env:check

# Or create a debug script
node -e "console.log(process.env)" | grep NEXT_PUBLIC
```

#### 5. Docker Build Failures
```bash
# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker compose build --no-cache frontend
```

## Monitoring and Logs

### Development Logs
```bash
# NPM logs
npm run dev --verbose

# Docker logs
docker compose logs -f frontend

# PM2 logs
pm2 logs prism-frontend
```

### Production Monitoring

1. **Application Metrics**
   - Page load times
   - API response times
   - JavaScript errors
   - Core Web Vitals

2. **Infrastructure Metrics**
   - CPU usage
   - Memory consumption
   - Network I/O
   - Disk usage

3. **Setup Monitoring Tools**
   ```bash
   # Install monitoring in pages/_app.tsx
   npm install @sentry/nextjs
   npx @sentry/wizard -i nextjs
   ```

## Performance Optimization

### 1. Enable Caching
```javascript
// next.config.js
module.exports = {
  // Enable build caching
  swcMinify: true,
  
  // Image optimization
  images: {
    formats: ['image/avif', 'image/webp'],
  },
  
  // Compression
  compress: true,
}
```

### 2. Use Production Build
```bash
# Always use production build for performance testing
npm run build
npm start
```

### 3. Enable HTTP/2
```nginx
# nginx.conf
server {
  listen 443 ssl http2;
  # ... rest of config
}
```

## Security Checklist

- [ ] Environment variables properly configured
- [ ] HTTPS enabled in production
- [ ] Security headers configured
- [ ] CORS properly set up
- [ ] Authentication working correctly
- [ ] No sensitive data in client-side code
- [ ] Dependencies up to date
- [ ] No console.logs in production

## Deployment Checklist

- [ ] Build succeeds without errors
- [ ] All tests pass
- [ ] Environment variables set
- [ ] Database migrations run
- [ ] Static assets uploaded to CDN
- [ ] SSL certificates valid
- [ ] Monitoring configured
- [ ] Backup procedures in place
- [ ] Rollback plan ready