# PRISM End-to-End Testing Guide

This guide will help you launch and test the PRISM AI-Powered Product Management Platform.

## Prerequisites

Before starting, ensure you have the following installed:
- Docker Desktop (with Docker Compose)
- Git
- A text editor (for editing .env files)
- At least 8GB of free RAM
- Ports 3000, 8000, 5432, 6379, 6333 available

## Quick Start (5 minutes)

### 1. Clone and Setup Environment

```bash
# If you haven't already cloned the repository
git clone https://github.com/prism-ai/prism-core.git
cd prism-core

# Copy environment file
cp .env.example .env

# Edit .env file and add your API keys (optional for basic testing)
# At minimum, set:
# - NEXTAUTH_SECRET (generate with: openssl rand -base64 32)
# - DATABASE_URL (default should work)
```

### 2. Launch All Services

```bash
# Start all services with Docker Compose
docker compose up -d

# Wait for services to be healthy (about 60 seconds)
docker compose ps

# Check logs if needed
docker compose logs -f backend
```

### 3. Run Database Migrations

```bash
# Create initial database schema
docker compose exec backend alembic upgrade head

# Seed sample data (optional)
docker compose exec backend python scripts/seed_data.py
```

### 4. Access the Application

Once all services are running:

1. **Frontend (UI)**: http://localhost:3000
2. **Backend API**: http://localhost:8000
3. **API Documentation**: http://localhost:8000/api/v1/docs
4. **pgAdmin**: http://localhost:5050 (email: admin@prism.ai, password: admin)
5. **RedisInsight**: http://localhost:8001

## Testing Checklist

### 1. Health Check
```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend health
curl http://localhost:3000/api/health
```

### 2. User Registration and Authentication
1. Navigate to http://localhost:3000
2. Click "Sign Up" or "Get Started"
3. Register with:
   - Email: test@example.com
   - Password: TestPassword123!
   - Name: Test User
4. Check your console logs for the verification email (if email service not configured)
5. Login with your credentials

### 3. Core Features Testing

#### A. Create a Project
1. Click "New Project" from dashboard
2. Enter project details:
   - Name: "My First Product"
   - Description: "Testing PRISM features"
3. Save the project

#### B. AI-Powered Story Generation
1. Navigate to your project
2. Click "Generate Story with AI"
3. Enter a prompt: "As a user, I want to login with social media accounts"
4. Review the generated story and acceptance criteria
5. Save the story

#### C. PRD Generation
1. From your project, click "Generate PRD"
2. Provide context about your product
3. Review the AI-generated PRD
4. Export as PDF or Markdown

#### D. Team Collaboration
1. Go to Settings → Team
2. Invite a team member (use another email)
3. Switch accounts and accept the invitation
4. Collaborate on the same project

### 4. API Testing

Test the API directly using curl or the Swagger UI:

```bash
# Register a user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "api@test.com",
    "password": "TestPassword123!",
    "full_name": "API Test User"
  }'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=api@test.com&password=TestPassword123!"

# Use the returned access token for authenticated requests
```

### 5. Performance Testing

Monitor system performance:

```bash
# View resource usage
docker stats

# Check response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health
```

## Troubleshooting

### Services Won't Start

```bash
# Check port conflicts
lsof -i :3000 -i :8000 -i :5432 -i :6379

# Reset everything
docker compose down -v
docker compose up -d
```

### Database Connection Issues

```bash
# Check PostgreSQL logs
docker compose logs postgres

# Test connection
docker compose exec postgres psql -U prism -d prism_db -c "SELECT 1;"
```

### Frontend Build Issues

```bash
# Rebuild frontend
docker compose build frontend
docker compose up -d frontend

# Check frontend logs
docker compose logs -f frontend
```

### Backend API Issues

```bash
# Check backend logs
docker compose logs -f backend

# Restart backend
docker compose restart backend
```

## Advanced Testing

### Load Testing with Locust

```bash
# Run load tests
cd backend
poetry run locust -f tests/performance/locustfile.py --host http://localhost:8000
```

### E2E Testing with Playwright

```bash
# Run frontend E2E tests
cd frontend
npm install
npm run e2e
```

### Database Inspection

```bash
# Connect to PostgreSQL
docker compose exec postgres psql -U prism -d prism_db

# List tables
\dt

# Describe a table
\d users
```

## Monitoring Services

### View All Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend frontend
```

### Check Service Health
```bash
# Health status
docker compose ps

# Detailed health
docker inspect prism-backend | jq '.[0].State.Health'
```

## Cleanup

When you're done testing:

```bash
# Stop all services
docker compose down

# Remove all data (careful!)
docker compose down -v

# Remove all images
docker compose down --rmi all
```

## Next Steps

1. **Configure Email**: Add SMTP settings in .env for email functionality
2. **Add AI Keys**: Add OpenAI/Anthropic API keys for AI features
3. **Enable Monitoring**: Uncomment monitoring services in docker compose.yml
4. **Production Setup**: See DEPLOYMENT.md for production configuration

## Support

If you encounter issues:
1. Check logs: `docker compose logs [service-name]`
2. Verify .env configuration
3. Ensure all ports are available
4. Check Docker resources (memory/disk)
5. Create an issue on GitHub with error details

Happy testing! 🚀