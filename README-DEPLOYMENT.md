# PRISM Deployment Quick Start

This guide helps you deploy PRISM with Neon PostgreSQL and Upstash Redis in minutes.

## Prerequisites

- Python 3.11+
- Node.js 18+ (optional, for frontend)
- Docker (optional, for containerized deployment)
- Neon account (free tier available)
- Upstash account (free tier available)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/prism.git
cd prism/prism-core
```

### 2. Run the Quick Deploy Script

```bash
chmod +x scripts/quick-deploy.sh
./scripts/quick-deploy.sh
```

The script will:
- Check prerequisites
- Create `.env` from template
- Guide you through configuration
- Install dependencies
- Set up the database schema
- Start the application

### 3. Manual Setup (Alternative)

If you prefer manual setup:

#### Step 1: Create Neon Database
1. Go to [Neon Console](https://console.neon.tech)
2. Create project "prism-db" in US-EAST-1
3. Copy the connection string

#### Step 2: Create Upstash Redis
1. Go to [Upstash Console](https://console.upstash.com)
2. Create database "prism-cache"
3. Copy the Redis URL

#### Step 3: Configure Environment
```bash
cp .env.example .env
# Edit .env with your values
```

#### Step 4: Install & Run
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations (if using Alembic)
alembic upgrade head

# Start the server
uvicorn prism.api.main:app --reload
```

## Access Points

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics

## Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Production Deployment

### Option 1: Railway
```bash
railway login
railway init
railway up
```

### Option 2: Render
1. Connect GitHub repo to Render
2. Add environment variables
3. Deploy automatically

### Option 3: Kubernetes
See `k8s/` directory for manifests

## Environment Variables

Key variables to configure:

```bash
# Required
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
SECRET_KEY=your-secret-key

# AI Providers (at least one required)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Optional
ENABLE_CACHE=true
ENABLE_RATE_LIMITING=true
```

## Troubleshooting

### Database Connection Issues
```bash
# Test Neon connection
psql $DATABASE_URL -c "SELECT 1"

# Ensure SSL mode
DATABASE_URL="...?sslmode=require"
```

### Redis Connection Issues
```bash
# Test Upstash connection
redis-cli -u $REDIS_URL ping
```

### Port Already in Use
```bash
# Change port in .env
PORT=8001

# Or kill existing process
lsof -ti:8000 | xargs kill
```

## Cost Management

### Free Tier Limits
- **Neon**: 0.5GB storage, 1 compute hour/day
- **Upstash**: 10K commands/day, 256MB storage

### Optimization Tips
1. Use Redis only for caching and sessions
2. Enable query optimization in Neon
3. Implement request caching
4. Use connection pooling

## Support

- Documentation: `/prism-deployment-guide.md`
- Issues: GitHub Issues
- Community: Discord (coming soon)

## Next Steps

1. Set up monitoring (Sentry, Datadog)
2. Configure CI/CD pipeline
3. Enable automated backups
4. Set up staging environment