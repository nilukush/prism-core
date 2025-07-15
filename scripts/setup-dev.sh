#!/bin/bash
set -euo pipefail

# PRISM Development Environment Setup Script
# Enterprise-grade development environment initialization

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="PRISM"
REQUIRED_DOCKER_VERSION="20.10.0"
REQUIRED_COMPOSE_VERSION="2.0.0"
PYTHON_VERSION="3.12"

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Version comparison
version_ge() {
    test "$(printf '%s\n' "$@" | sort -V | head -n 1)" != "$1"
}

# Check system requirements
check_requirements() {
    log_info "Checking system requirements..."
    
    # Check Docker
    if ! command_exists docker; then
        log_error "Docker is not installed. Please install Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    DOCKER_VERSION=$(docker --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    if ! version_ge "$DOCKER_VERSION" "$REQUIRED_DOCKER_VERSION"; then
        log_error "Docker version $DOCKER_VERSION is too old. Required: $REQUIRED_DOCKER_VERSION+"
        exit 1
    fi
    log_success "Docker $DOCKER_VERSION detected"
    
    # Check Docker Compose
    if command_exists "docker-compose"; then
        COMPOSE_VERSION=$(docker-compose --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    elif docker compose version >/dev/null 2>&1; then
        COMPOSE_VERSION=$(docker compose version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    else
        log_error "Docker Compose is not installed. Please install Docker Compose."
        exit 1
    fi
    
    if ! version_ge "$COMPOSE_VERSION" "$REQUIRED_COMPOSE_VERSION"; then
        log_error "Docker Compose version $COMPOSE_VERSION is too old. Required: $REQUIRED_COMPOSE_VERSION+"
        exit 1
    fi
    log_success "Docker Compose $COMPOSE_VERSION detected"
    
    # Check Git
    if ! command_exists git; then
        log_error "Git is not installed. Please install Git."
        exit 1
    fi
    log_success "Git detected"
}

# Create environment file
create_env_file() {
    log_info "Setting up environment configuration..."
    
    if [ -f .env ]; then
        log_warning ".env file already exists. Backing up to .env.backup"
        cp .env .env.backup
    fi
    
    # Generate secure random values
    generate_secret() {
        openssl rand -base64 32 | tr -d "=+/" | cut -c1-32
    }
    
    cat > .env << EOF
# PRISM Development Environment Configuration
# Generated on $(date)

# Environment
ENVIRONMENT=development
DEBUG=true

# Database
POSTGRES_USER=prism
POSTGRES_PASSWORD=$(generate_secret)
POSTGRES_DB=prism_dev
DATABASE_URL=postgresql+asyncpg://prism:\${POSTGRES_PASSWORD}@postgres:5432/prism_dev

# Redis
REDIS_URL=redis://redis:6379/0

# Security
SECRET_KEY=$(generate_secret)
JWT_SECRET=$(generate_secret)
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Email (using MailHog for development)
EMAIL_BACKEND=smtp
SMTP_HOST=mailhog
SMTP_PORT=1025
SMTP_USERNAME=""
SMTP_PASSWORD=""
SMTP_USE_TLS=false
EMAIL_FROM=noreply@prism.local

# Vector Database
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_API_KEY=""
QDRANT_COLLECTION_NAME=prism_vectors

# Celery
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# API Keys (Add your own for development)
OPENAI_API_KEY=""
ANTHROPIC_API_KEY=""
GOOGLE_API_KEY=""

# Monitoring
ENABLE_METRICS=true
ENABLE_TRACING=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317

# Development Tools
PGADMIN_DEFAULT_EMAIL=admin@prism.local
PGADMIN_DEFAULT_PASSWORD=$(generate_secret)
EOF
    
    log_success "Environment configuration created"
}

# Initialize Docker environment
init_docker() {
    log_info "Initializing Docker environment..."
    
    # Create necessary directories
    mkdir -p logs
    mkdir -p data/postgres
    mkdir -p data/redis
    mkdir -p data/qdrant
    
    # Pull all images
    log_info "Pulling Docker images..."
    docker compose pull
    
    # Build backend image
    log_info "Building backend image..."
    docker compose build backend
    
    log_success "Docker environment initialized"
}

# Start services
start_services() {
    log_info "Starting core services..."
    
    # Start infrastructure services first
    docker compose up -d postgres redis qdrant mailhog
    
    # Wait for PostgreSQL to be ready
    log_info "Waiting for PostgreSQL to be ready..."
    local retries=30
    while [ $retries -gt 0 ]; do
        if docker compose exec -T postgres pg_isready -U prism >/dev/null 2>&1; then
            log_success "PostgreSQL is ready"
            break
        fi
        retries=$((retries - 1))
        sleep 1
    done
    
    if [ $retries -eq 0 ]; then
        log_error "PostgreSQL failed to start"
        exit 1
    fi
    
    # Wait for Redis
    log_info "Waiting for Redis to be ready..."
    retries=30
    while [ $retries -gt 0 ]; do
        if docker compose exec -T redis redis-cli ping >/dev/null 2>&1; then
            log_success "Redis is ready"
            break
        fi
        retries=$((retries - 1))
        sleep 1
    done
    
    if [ $retries -eq 0 ]; then
        log_error "Redis failed to start"
        exit 1
    fi
    
    log_success "Core services started"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    # Run Alembic migrations
    docker compose run --rm backend alembic upgrade head
    
    log_success "Database migrations completed"
}

# Seed initial data
seed_data() {
    log_info "Seeding initial development data..."
    
    # Create seed script
    cat > /tmp/seed_data.py << 'EOF'
import asyncio
import sys
from pathlib import Path

# Add backend source to path
sys.path.insert(0, '/app/src')

from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db, engine
from src.models.user import User
from src.models.organization import Organization
from src.models.workspace import Workspace
from src.models.role import Role, Permission
from src.services.auth import AuthService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed_database():
    """Seed database with initial development data."""
    async with AsyncSession(engine) as session:
        try:
            # Check if data already exists
            existing_user = await session.execute(
                "SELECT 1 FROM users LIMIT 1"
            )
            if existing_user.scalar():
                logger.info("Database already contains data, skipping seed")
                return
            
            # Create roles and permissions
            logger.info("Creating roles and permissions...")
            
            # Permissions
            permissions = [
                Permission(name="users:read", description="Read users"),
                Permission(name="users:write", description="Write users"),
                Permission(name="users:delete", description="Delete users"),
                Permission(name="agents:read", description="Read agents"),
                Permission(name="agents:write", description="Write agents"),
                Permission(name="agents:execute", description="Execute agents"),
                Permission(name="workspaces:read", description="Read workspaces"),
                Permission(name="workspaces:write", description="Write workspaces"),
                Permission(name="workspaces:delete", description="Delete workspaces"),
                Permission(name="analytics:read", description="Read analytics"),
                Permission(name="admin:all", description="Full admin access"),
            ]
            session.add_all(permissions)
            await session.flush()
            
            # Roles
            admin_role = Role(
                name="admin",
                description="Administrator with full access",
                permissions=permissions
            )
            
            developer_role = Role(
                name="developer",
                description="Developer with agent and workspace access",
                permissions=[p for p in permissions if not p.name.startswith("admin") and not p.name.endswith("delete")]
            )
            
            viewer_role = Role(
                name="viewer",
                description="Read-only access",
                permissions=[p for p in permissions if p.name.endswith("read")]
            )
            
            session.add_all([admin_role, developer_role, viewer_role])
            await session.flush()
            
            # Create organizations
            logger.info("Creating organizations...")
            demo_org = Organization(
                name="Demo Organization",
                description="Demo organization for development",
                settings={"trial": False, "max_users": 100}
            )
            session.add(demo_org)
            await session.flush()
            
            # Create users
            logger.info("Creating users...")
            auth_service = AuthService()
            
            # Admin user
            admin_user = User(
                email="admin@prism.local",
                username="admin",
                full_name="Admin User",
                is_active=True,
                is_verified=True,
                is_superuser=True,
                organization_id=demo_org.id,
                roles=[admin_role]
            )
            admin_user.hashed_password = auth_service.hash_password("admin123!")
            
            # Developer user
            dev_user = User(
                email="developer@prism.local",
                username="developer",
                full_name="Developer User",
                is_active=True,
                is_verified=True,
                organization_id=demo_org.id,
                roles=[developer_role]
            )
            dev_user.hashed_password = auth_service.hash_password("dev123!")
            
            # Viewer user
            viewer_user = User(
                email="viewer@prism.local",
                username="viewer",
                full_name="Viewer User",
                is_active=True,
                is_verified=True,
                organization_id=demo_org.id,
                roles=[viewer_role]
            )
            viewer_user.hashed_password = auth_service.hash_password("viewer123!")
            
            session.add_all([admin_user, dev_user, viewer_user])
            await session.flush()
            
            # Create workspaces
            logger.info("Creating workspaces...")
            workspace1 = Workspace(
                name="Development Workspace",
                description="Main development workspace",
                organization_id=demo_org.id,
                created_by_id=admin_user.id,
                settings={"theme": "dark", "notifications": True}
            )
            
            workspace2 = Workspace(
                name="Testing Workspace",
                description="Workspace for testing agents",
                organization_id=demo_org.id,
                created_by_id=dev_user.id,
                settings={"theme": "light", "notifications": False}
            )
            
            session.add_all([workspace1, workspace2])
            
            # Commit all changes
            await session.commit()
            logger.info("Database seeding completed successfully")
            
        except Exception as e:
            logger.error(f"Error seeding database: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(seed_database())
EOF
    
    # Copy seed script to container and run
    docker cp /tmp/seed_data.py prism-backend:/tmp/
    docker compose exec -T backend python /tmp/seed_data.py
    
    rm /tmp/seed_data.py
    
    log_success "Initial data seeded"
}

# Start development services
start_dev_services() {
    log_info "Starting development services..."
    
    # Start backend with hot reload
    docker compose up -d backend
    
    # Start Celery workers
    docker compose up -d celery-worker celery-beat
    
    # Start monitoring tools with development profile
    docker compose --profile dev up -d
    
    log_success "All services started"
}

# Display setup information
display_info() {
    echo ""
    echo "=========================================="
    echo "   PRISM Development Environment Ready!    "
    echo "=========================================="
    echo ""
    echo "Services:"
    echo "  - Backend API:      http://localhost:8000"
    echo "  - API Documentation: http://localhost:8000/docs"
    echo "  - MailHog:          http://localhost:8025"
    echo "  - Flower (Celery):  http://localhost:5555"
    echo "  - pgAdmin:          http://localhost:5050"
    echo "  - RedisInsight:     http://localhost:8001"
    echo ""
    echo "Default Credentials:"
    echo "  - Admin:     admin@prism.local / admin123!"
    echo "  - Developer: developer@prism.local / dev123!"
    echo "  - Viewer:    viewer@prism.local / viewer123!"
    echo ""
    echo "  - pgAdmin:   Check .env file for credentials"
    echo ""
    echo "Commands:"
    echo "  - View logs:        docker compose logs -f [service]"
    echo "  - Run tests:        docker compose exec backend pytest"
    echo "  - Access shell:     docker compose exec backend bash"
    echo "  - Stop all:         docker compose down"
    echo "  - Reset all:        docker compose down -v"
    echo ""
    echo "Next steps:"
    echo "  1. Add your API keys to .env file"
    echo "  2. Access the API docs at http://localhost:8000/docs"
    echo "  3. Start developing!"
    echo ""
}

# Main setup flow
main() {
    echo ""
    echo "======================================"
    echo "   PRISM Development Setup Script     "
    echo "======================================"
    echo ""
    
    # Parse arguments
    SKIP_CHECKS=false
    RESET=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-checks)
                SKIP_CHECKS=true
                shift
                ;;
            --reset)
                RESET=true
                shift
                ;;
            --help)
                echo "Usage: $0 [options]"
                echo ""
                echo "Options:"
                echo "  --skip-checks    Skip system requirement checks"
                echo "  --reset          Reset environment (removes volumes)"
                echo "  --help           Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Reset if requested
    if [ "$RESET" = true ]; then
        log_warning "Resetting development environment..."
        docker compose down -v
        rm -rf data/
        log_success "Environment reset complete"
    fi
    
    # Check requirements
    if [ "$SKIP_CHECKS" = false ]; then
        check_requirements
    fi
    
    # Setup flow
    create_env_file
    init_docker
    start_services
    run_migrations
    seed_data
    start_dev_services
    display_info
    
    log_success "Setup completed successfully!"
}

# Run main function
main "$@"