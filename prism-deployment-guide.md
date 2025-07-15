# PRISM Deployment Guide - Neon PostgreSQL & Upstash Redis

This guide provides step-by-step instructions for deploying PRISM with Neon PostgreSQL and Upstash Redis cloud services.

## Prerequisites

- Node.js 18+ and npm/yarn installed
- Python 3.11+ installed
- Docker and Docker Compose installed (for local development)
- GitHub account (for repository access)
- Neon account (https://neon.tech)
- Upstash account (https://upstash.com)

## Step 1: Database Setup with Neon

### 1.1 Create Neon Project

Based on your setup:
- **Project Name**: `prism-db`
- **Region**: AWS US East 1 (N. Virginia) - `aws-us-east-1`
- **PostgreSQL Version**: 16 (recommended)

### 1.2 Get Database Connection Details

After creating your Neon project, you'll receive:

```bash
# Connection string format:
postgresql://[user]:[password]@[endpoint]/[database]?sslmode=require

# Example (replace with your actual values):
DATABASE_URL="postgresql://prism_user:abc123xyz@ep-cool-dawn-123456.us-east-1.aws.neon.tech/prism_db?sslmode=require"
```

### 1.3 Database Schema Setup

Connect to your Neon database and run the following schema:

```sql
-- Create tables for PRISM
CREATE SCHEMA IF NOT EXISTS prism;

-- Users table
CREATE TABLE prism.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Organizations table
CREATE TABLE prism.organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    plan VARCHAR(50) DEFAULT 'free',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Projects table
CREATE TABLE prism.projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES prism.organizations(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Stories table
CREATE TABLE prism.user_stories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES prism.projects(id),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    acceptance_criteria JSONB,
    priority VARCHAR(50),
    status VARCHAR(50) DEFAULT 'backlog',
    created_by UUID REFERENCES prism.users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- PRDs table
CREATE TABLE prism.prds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES prism.projects(id),
    title VARCHAR(500) NOT NULL,
    content TEXT,
    version VARCHAR(50) DEFAULT '1.0.0',
    status VARCHAR(50) DEFAULT 'draft',
    created_by UUID REFERENCES prism.users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_projects_org ON prism.projects(organization_id);
CREATE INDEX idx_stories_project ON prism.user_stories(project_id);
CREATE INDEX idx_prds_project ON prism.prds(project_id);
```

## Step 2: Redis Setup with Upstash

### 2.1 Create Upstash Redis Database

Based on your setup:
- **Database Name**: `prism-cache`
- **Region**: Select the same region as your Neon database (US-EAST-1)
- **Type**: Regional (for better performance)

### 2.2 Get Redis Connection Details

After creating your Upstash Redis database, you'll receive:

```bash
# Redis URL format:
redis://default:[password]@[endpoint]:[port]

# Example (replace with your actual values):
REDIS_URL="redis://default:AX3aAAIncDEwNjY3ZT@us1-sacred-monkey-40123.upstash.io:40123"

# Or use the REST API endpoint for serverless:
UPSTASH_REDIS_REST_URL="https://us1-sacred-monkey-40123.upstash.io"
UPSTASH_REDIS_REST_TOKEN="AX3aAAIncDEwNjY3ZT..."
```

## Step 3: Environment Configuration

### 3.1 Create `.env` file

Create a `.env` file in your project root:

```bash
# Database Configuration
DATABASE_URL="postgresql://[user]:[password]@[endpoint]/[database]?sslmode=require"

# Redis Configuration
REDIS_URL="redis://default:[password]@[endpoint]:[port]"
UPSTASH_REDIS_REST_URL="https://[endpoint]"
UPSTASH_REDIS_REST_TOKEN="[token]"

# Application Configuration
NODE_ENV=production
PORT=8000
SECRET_KEY="your-secret-key-here-generate-a-secure-one"

# AI Provider Keys
OPENAI_API_KEY="sk-..."
ANTHROPIC_API_KEY="sk-ant-..."

# OAuth Configuration (optional)
GOOGLE_CLIENT_ID="your-google-client-id"
GOOGLE_CLIENT_SECRET="your-google-client-secret"

# Feature Flags
ENABLE_CACHE=true
ENABLE_RATE_LIMITING=true
```

### 3.2 Generate Secure Secret Key

```bash
# Generate a secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Step 4: Application Deployment

### 4.1 Local Development with Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - ./:/app
    command: uvicorn prism.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 4.2 Production Deployment Options

#### Option A: Deploy to Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project
railway init

# Link to GitHub repo
railway link

# Deploy
railway up
```

#### Option B: Deploy to Render

1. Connect your GitHub repository to Render
2. Create a new Web Service
3. Set environment variables in Render dashboard
4. Deploy automatically on push to main

#### Option C: Deploy to AWS/GCP/Azure

Use the provided Kubernetes manifests in the repository.

## Step 5: Post-Deployment Setup

### 5.1 Run Database Migrations

```bash
# Using Alembic (if configured)
alembic upgrade head

# Or run setup script
python scripts/setup_database.py
```

### 5.2 Create Admin User

```python
# scripts/create_admin.py
from prism.models import User
from prism.database import get_db

async def create_admin():
    db = get_db()
    admin = User(
        email="admin@prism.dev",
        name="Admin User",
        role="admin"
    )
    db.add(admin)
    db.commit()
    print(f"Admin user created: {admin.email}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(create_admin())
```

### 5.3 Test the Deployment

```bash
# Health check
curl https://your-app-url/health

# API documentation
open https://your-app-url/docs
```

## Step 6: Monitoring and Maintenance

### 6.1 Set up Monitoring

1. **Neon Monitoring**:
   - Monitor query performance in Neon dashboard
   - Set up alerts for slow queries
   - Enable query insights

2. **Upstash Monitoring**:
   - Monitor Redis usage in Upstash dashboard
   - Set up alerts for memory usage
   - Track command latency

3. **Application Monitoring**:
   - Use Sentry for error tracking
   - Set up logging with CloudWatch/Datadog
   - Configure uptime monitoring

### 6.2 Backup Strategy

```bash
# Neon backups are automatic, but you can also:
# Create manual backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Restore from backup
psql $DATABASE_URL < backup_20240315.sql
```

## Step 7: Security Checklist

- [ ] Enable SSL/TLS for all connections
- [ ] Set up firewall rules (allow only necessary IPs)
- [ ] Enable 2FA on Neon and Upstash accounts
- [ ] Rotate API keys regularly
- [ ] Use environment-specific secrets
- [ ] Enable audit logging
- [ ] Set up CORS properly
- [ ] Implement rate limiting

## Troubleshooting

### Common Issues

1. **Connection Timeout to Neon**:
   ```bash
   # Check if SSL is required
   DATABASE_URL="...?sslmode=require"
   ```

2. **Redis Connection Issues**:
   ```bash
   # Test Redis connection
   redis-cli -u $REDIS_URL ping
   ```

3. **Environment Variables Not Loading**:
   ```bash
   # Check .env file is loaded
   python -c "import os; print(os.getenv('DATABASE_URL'))"
   ```

## Cost Optimization

### Neon PostgreSQL
- Free tier: 0.5 GB storage, 1 compute hour/day
- Pro: $19/month for 10 GB storage, autoscaling compute
- Scale compute down during off-hours

### Upstash Redis
- Free tier: 10,000 commands/day, 256 MB
- Pay-as-you-go: $0.2 per 100K commands
- Use Redis for session storage and caching only

## Next Steps

1. Set up CI/CD pipeline
2. Configure automated backups
3. Implement monitoring dashboards
4. Set up staging environment
5. Configure auto-scaling policies

## Support Resources

- Neon Documentation: https://neon.tech/docs
- Upstash Documentation: https://docs.upstash.com
- PRISM Issues: https://github.com/yourusername/prism/issues
- Community Discord: [Add your Discord invite link]