# PRISM Setup Guide

## Prerequisites

- Docker and Docker Compose v2
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)
- PostgreSQL 15+ (if not using Docker)
- Redis 7+ (if not using Docker)

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd prism-core
   ```

2. **Copy environment file**
   ```bash
   cp .env.example .env
   ```

3. **Start all services**
   ```bash
   docker compose up -d
   ```

   Or start specific services:
   ```bash
   # Core services only (backend, database, redis)
   docker compose up -d postgres redis qdrant backend
   
   # With frontend
   docker compose --profile frontend up -d
   
   # With monitoring tools
   docker compose --profile tools up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:3100
   - Backend API: http://localhost:8100
   - API Documentation: http://localhost:8100/api/v1/docs
   - pgAdmin: http://localhost:5051
   - RedisInsight: http://localhost:8002 (with --profile tools)

## Configuration

### Required API Keys

For production use, you need to configure the following API keys in `.env`:

1. **LLM Providers** (at least one):
   - `OPENAI_API_KEY`: OpenAI API key for GPT models
   - `ANTHROPIC_API_KEY`: Anthropic API key for Claude models
   - Or configure Ollama for local LLM

2. **Security Keys** (generate for production):
   - `SECRET_KEY`: Application secret key (32+ characters)
   - `JWT_SECRET_KEY`: JWT signing key
   - `ENCRYPTION_KEY`: 32-byte encryption key
   - `NEXTAUTH_SECRET`: NextAuth.js secret

3. **Optional Integrations**:
   - Jira: `JIRA_EMAIL`, `JIRA_API_TOKEN`
   - GitHub: `GITHUB_TOKEN`
   - Slack: `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`
   - Email: SMTP configuration

### Port Configuration

Default ports (can be changed in `.env`):
- Frontend: 3100
- Backend API: 8100
- PostgreSQL: 5433
- Redis: 6380
- Qdrant: 6334
- pgAdmin: 5051
- RedisInsight: 8002
- Flower: 5556

## Development Setup

### Backend Development

```bash
# Create virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install poetry
poetry install

# Run migrations
alembic upgrade head

# Start development server
uvicorn backend.src.main:app --reload --port 8100
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Database Setup

### Run Migrations
```bash
docker compose exec backend alembic upgrade head
```

### Create Initial Admin User
```bash
docker compose exec backend python -m backend.scripts.create_admin
```

## Troubleshooting

### Common Issues

1. **Port conflicts**: Change ports in `.env` file
2. **Database connection errors**: Ensure PostgreSQL is running and healthy
3. **Frontend build errors**: Run `npm install` to ensure all dependencies are installed
4. **Import errors**: Restart the backend container after making changes

### Reset Everything

```bash
# Stop all containers
docker compose down -v

# Remove all data
rm -rf postgres_data redis_data qdrant_data

# Rebuild and start
docker compose build --no-cache
docker compose up -d
```

## Production Deployment

For production deployment:

1. Use proper SSL/TLS certificates
2. Set strong, unique values for all secret keys
3. Configure proper CORS origins
4. Enable rate limiting and security features
5. Set up monitoring with Sentry and Prometheus
6. Use managed databases (RDS, Cloud SQL, etc.)
7. Configure proper backup strategies

See `deployment/` directory for production configurations.