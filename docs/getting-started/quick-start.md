# Quick Start Guide

Get PRISM up and running in 5 minutes! This guide will help you set up PRISM using Docker Compose for a quick evaluation.

## Prerequisites

- Docker 20.10+ installed
- Docker Compose 2.0+ installed
- 4GB RAM minimum
- 10GB free disk space

## Step 1: Clone the Repository

```bash
git clone https://github.com/prism-ai/prism-core.git
cd prism-core
```

## Step 2: Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your preferred editor
nano .env
```

Minimum required configuration:

```env
# Database (auto-configured with Docker)
DATABASE_URL=postgresql+asyncpg://prism:prism123@postgres:5432/prism_db

# Redis (auto-configured with Docker)
REDIS_URL=redis://redis:6379/0

# Security (generate a secure key)
JWT_SECRET=your-secure-secret-key-here

# AI Provider (choose one)
OPENAI_API_KEY=sk-your-openai-key
# OR
ANTHROPIC_API_KEY=your-anthropic-key
# OR use local Ollama (no key needed)
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

## Step 3: Start PRISM

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f app
```

## Step 4: Access PRISM

Once all services are running:

1. **API Documentation**: http://localhost:8000/api/v1/docs
2. **Health Check**: http://localhost:8000/health
3. **Metrics**: http://localhost:8000/metrics

## Step 5: Create Your First User

```bash
# Using the provided CLI tool
docker-compose exec app python -m backend.cli create-user \
  --email admin@example.com \
  --password yourpassword \
  --role admin

# Or via API
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "yourpassword",
    "name": "Admin User"
  }'
```

## Step 6: Generate Your First User Story

1. **Get Authentication Token**:

```bash
# Login
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "yourpassword"
  }' | jq -r .access_token)
```

2. **Create an Organization**:

```bash
curl -X POST http://localhost:8000/api/v1/organizations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Company",
    "slug": "my-company"
  }'
```

3. **Generate a User Story**:

```bash
curl -X POST http://localhost:8000/api/v1/ai/stories/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "requirement": "Users should be able to reset their password",
    "context": "E-commerce mobile app",
    "priority": "high",
    "acceptance_criteria_count": 5
  }'
```

## Next Steps

### Explore Features

- **Generate PRDs**: Create comprehensive product requirement documents
- **Sprint Planning**: Get AI-powered sprint planning suggestions
- **Integration Setup**: Connect Jira, Slack, and other tools
- **Team Collaboration**: Invite team members and set permissions

### Production Deployment

For production deployment, see:
- [Docker Production Guide](../deployment/docker.md)
- [Kubernetes Deployment](../deployment/kubernetes.md)
- [Security Best Practices](../deployment/security.md)

### Get Help

- 📚 [Full Documentation](../README.md)
- 💬 [Discord Community](https://discord.gg/prism-ai)
- 🐛 [Report Issues](https://github.com/prism-ai/prism-core/issues)

## Troubleshooting

### Common Issues

**Services not starting?**
```bash
# Check logs
docker-compose logs postgres
docker-compose logs redis
docker-compose logs app

# Restart services
docker-compose restart
```

**Database connection errors?**
```bash
# Reset database
docker-compose down -v
docker-compose up -d
```

**AI features not working?**
- Verify your AI provider API key is correct
- Check API rate limits
- Try using Ollama for local testing

### Cleanup

To completely remove PRISM:

```bash
# Stop and remove all containers, volumes
docker-compose down -v

# Remove images (optional)
docker-compose down --rmi all
```