#!/bin/bash
set -euo pipefail

# PRISM Development Helper Script
# Quick commands for common development tasks

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Helper functions
print_usage() {
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  start               Start all services"
    echo "  stop                Stop all services"
    echo "  restart [service]   Restart service(s)"
    echo "  logs [service]      View logs (follow mode)"
    echo "  shell [service]     Access service shell"
    echo "  test [args]         Run tests"
    echo "  migrate             Run database migrations"
    echo "  makemigrations      Create new migration"
    echo "  seed                Seed database"
    echo "  reset               Reset database"
    echo "  lint                Run linters"
    echo "  format              Format code"
    echo "  build               Rebuild images"
    echo "  ps                  List running services"
    echo "  exec [cmd]          Execute command in backend"
    echo ""
}

# Default service
DEFAULT_SERVICE="backend"

# Main command handler
case "${1:-help}" in
    start)
        echo -e "${BLUE}Starting PRISM services...${NC}"
        docker compose up -d
        echo -e "${GREEN}Services started!${NC}"
        docker compose ps
        ;;
    
    stop)
        echo -e "${BLUE}Stopping PRISM services...${NC}"
        docker compose down
        echo -e "${GREEN}Services stopped!${NC}"
        ;;
    
    restart)
        SERVICE="${2:-}"
        if [ -z "$SERVICE" ]; then
            echo -e "${BLUE}Restarting all services...${NC}"
            docker compose restart
        else
            echo -e "${BLUE}Restarting $SERVICE...${NC}"
            docker compose restart "$SERVICE"
        fi
        echo -e "${GREEN}Restart complete!${NC}"
        ;;
    
    logs)
        SERVICE="${2:-}"
        if [ -z "$SERVICE" ]; then
            docker compose logs -f --tail=100
        else
            docker compose logs -f --tail=100 "$SERVICE"
        fi
        ;;
    
    shell)
        SERVICE="${2:-$DEFAULT_SERVICE}"
        if [ "$SERVICE" = "backend" ]; then
            docker compose exec backend bash
        elif [ "$SERVICE" = "postgres" ]; then
            docker compose exec postgres psql -U prism -d prism_dev
        elif [ "$SERVICE" = "redis" ]; then
            docker compose exec redis redis-cli
        else
            docker compose exec "$SERVICE" sh
        fi
        ;;
    
    test)
        shift
        echo -e "${BLUE}Running tests...${NC}"
        docker compose exec -T backend pytest "$@"
        ;;
    
    migrate)
        echo -e "${BLUE}Running migrations...${NC}"
        docker compose exec -T backend alembic upgrade head
        echo -e "${GREEN}Migrations complete!${NC}"
        ;;
    
    makemigrations)
        MESSAGE="${2:-Auto migration}"
        echo -e "${BLUE}Creating migration: $MESSAGE${NC}"
        docker compose exec -T backend alembic revision --autogenerate -m "$MESSAGE"
        echo -e "${GREEN}Migration created!${NC}"
        ;;
    
    seed)
        echo -e "${BLUE}Seeding database...${NC}"
        docker compose exec -T backend python scripts/seed_data.py
        echo -e "${GREEN}Database seeded!${NC}"
        ;;
    
    reset)
        echo -e "${YELLOW}WARNING: This will delete all data!${NC}"
        read -p "Are you sure? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${BLUE}Resetting database...${NC}"
            docker compose down -v
            docker compose up -d postgres
            sleep 5
            docker compose exec -T backend alembic upgrade head
            docker compose exec -T backend python scripts/seed_data.py
            echo -e "${GREEN}Database reset complete!${NC}"
        fi
        ;;
    
    lint)
        echo -e "${BLUE}Running linters...${NC}"
        docker compose exec -T backend ruff check src/ tests/
        docker compose exec -T backend mypy src/
        echo -e "${GREEN}Linting complete!${NC}"
        ;;
    
    format)
        echo -e "${BLUE}Formatting code...${NC}"
        docker compose exec -T backend ruff format src/ tests/
        docker compose exec -T backend ruff check --fix src/ tests/
        echo -e "${GREEN}Formatting complete!${NC}"
        ;;
    
    build)
        echo -e "${BLUE}Building images...${NC}"
        docker compose build
        echo -e "${GREEN}Build complete!${NC}"
        ;;
    
    ps)
        docker compose ps
        ;;
    
    exec)
        shift
        docker compose exec backend "$@"
        ;;
    
    help|--help|-h)
        print_usage
        ;;
    
    *)
        echo -e "${YELLOW}Unknown command: $1${NC}"
        echo ""
        print_usage
        exit 1
        ;;
esac