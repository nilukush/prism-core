#!/bin/bash

# PRISM Quick Start Script
# This script sets up and launches PRISM for testing

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Banner
echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════╗"
echo "║          PRISM Quick Start Setup                  ║"
echo "║   AI-Powered Product Management Platform          ║"
echo "╚═══════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check prerequisites
print_info "Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker Desktop."
    exit 1
fi

# Check Docker Compose (v2 is included with Docker Desktop)
if ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not available. Please ensure Docker Desktop is installed and running."
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    print_error "Docker is not running. Please start Docker Desktop."
    exit 1
fi

print_success "Prerequisites check passed!"

# Setup environment
print_info "Setting up environment..."

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    print_success "Created .env file from .env.example"
    
    # Generate NEXTAUTH_SECRET if not set
    if ! grep -q "NEXTAUTH_SECRET=" .env || grep -q "NEXTAUTH_SECRET=$" .env || grep -q "NEXTAUTH_SECRET=your-nextauth-secret-here" .env; then
        print_info "Generating NEXTAUTH_SECRET..."
        SECRET=$(openssl rand -base64 32)
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s/NEXTAUTH_SECRET=.*/NEXTAUTH_SECRET=$SECRET/" .env
        else
            sed -i "s/NEXTAUTH_SECRET=.*/NEXTAUTH_SECRET=$SECRET/" .env
        fi
        print_success "Generated NEXTAUTH_SECRET"
    fi
else
    print_info ".env file already exists"
fi

# Source .env file if it exists to get port configuration
if [ -f .env ]; then
    export $(grep -E '^[A-Z_]+_PORT=' .env | xargs)
fi

# Check for required ports
print_info "Checking port availability..."
# Read ports from .env or use defaults
FRONTEND_PORT=${FRONTEND_PORT:-3100}
API_PORT=${API_PORT:-8100}
POSTGRES_PORT=${POSTGRES_PORT:-5433}
REDIS_PORT=${REDIS_PORT:-6380}
QDRANT_PORT=${QDRANT_PORT:-6334}
PORTS=($FRONTEND_PORT $API_PORT $POSTGRES_PORT $REDIS_PORT $QDRANT_PORT)
PORTS_IN_USE=()

for PORT in "${PORTS[@]}"; do
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        PORTS_IN_USE+=($PORT)
    fi
done

if [ ${#PORTS_IN_USE[@]} -ne 0 ]; then
    print_warning "The following ports are already in use: ${PORTS_IN_USE[*]}"
    print_warning "Please stop the services using these ports or change the ports in .env"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Stop any existing containers
print_info "Stopping any existing PRISM containers..."
docker compose down 2>/dev/null || true

# Build and start services
print_info "Building and starting services..."
print_info "This may take a few minutes on first run..."

docker compose up -d --build

# Wait for services to be healthy
print_info "Waiting for services to be healthy..."
SERVICES=("postgres" "redis" "backend")
MAX_WAIT=120
WAIT_TIME=0

while [ $WAIT_TIME -lt $MAX_WAIT ]; do
    ALL_HEALTHY=true
    for SERVICE in "${SERVICES[@]}"; do
        if ! docker compose ps $SERVICE | grep -q "healthy"; then
            ALL_HEALTHY=false
            break
        fi
    done
    
    if $ALL_HEALTHY; then
        break
    fi
    
    echo -ne "\rWaiting for services... ${WAIT_TIME}s / ${MAX_WAIT}s"
    sleep 5
    WAIT_TIME=$((WAIT_TIME + 5))
done

echo
if [ $WAIT_TIME -ge $MAX_WAIT ]; then
    print_error "Services did not become healthy in time"
    print_info "Check logs with: docker compose logs"
    exit 1
fi

print_success "All services are healthy!"

# Run migrations
print_info "Running database migrations..."
docker compose exec -T backend alembic upgrade head || {
    print_warning "Migration failed. Creating initial migration..."
    docker compose exec -T backend alembic revision --autogenerate -m "Initial schema" || true
    docker compose exec -T backend alembic upgrade head || true
}

# Optional: Seed data
read -p "Would you like to seed sample data? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Seeding sample data..."
    docker compose exec -T backend python scripts/seed_data.py || print_warning "Seeding failed or script not found"
fi

# Display access information
echo
print_success "PRISM is ready for testing!"
echo
echo -e "${GREEN}Access Points:${NC}"
echo "  • Frontend UI:        http://localhost:${FRONTEND_PORT:-3100}"
echo "  • Backend API:        http://localhost:${API_PORT:-8100}"
echo "  • API Documentation:  http://localhost:${API_PORT:-8100}/api/v1/docs"
echo "  • pgAdmin:           http://localhost:${PGADMIN_PORT:-5051}"
echo "    - Email: admin@prism.ai"
echo "    - Password: admin"
echo "  • RedisInsight:      http://localhost:${REDISINSIGHT_PORT:-8002}"
echo
echo -e "${YELLOW}Quick Commands:${NC}"
echo "  • View logs:         docker compose logs -f [service]"
echo "  • Stop all:          docker compose down"
echo "  • Restart service:   docker compose restart [service]"
echo "  • Shell access:      docker compose exec backend bash"
echo
echo -e "${BLUE}Next Steps:${NC}"
echo "  1. Open http://localhost:${FRONTEND_PORT:-3100} in your browser"
echo "  2. Click 'Sign Up' to create an account"
echo "  3. Explore the features!"
echo
echo "For detailed testing instructions, see TESTING_GUIDE.md"
echo

# Optional: Open browser
if command -v open &> /dev/null; then
    read -p "Open PRISM in your browser? (Y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        open http://localhost:${FRONTEND_PORT:-3100}
    fi
elif command -v xdg-open &> /dev/null; then
    read -p "Open PRISM in your browser? (Y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        xdg-open http://localhost:${FRONTEND_PORT:-3100}
    fi
fi

print_success "Setup complete! Happy testing! 🚀"