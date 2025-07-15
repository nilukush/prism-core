#!/bin/bash
# Local Development Build Script
# Optimized for developer experience, not production performance

set -euo pipefail

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Local Development Build Script${NC}"
echo -e "${YELLOW}Optimized for fast iteration and hot-reloading${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# Check Docker
if ! docker version > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

# Build options for local development
BUILD_OPTIONS=(
    "--target" "development"
    "--tag" "prism-backend:dev"
)

# Check if we should use BuildKit (recommended but not required for local dev)
if docker buildx version > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Using BuildKit for faster builds${NC}"
    BUILD_CMD="docker buildx build"
    BUILD_OPTIONS+=("--load")  # Load into local Docker
else
    echo -e "${YELLOW}ℹ Using standard Docker build${NC}"
    BUILD_CMD="docker build"
    export DOCKER_BUILDKIT=1
fi

# Use the standard Dockerfile, not the enterprise one for local dev
if [ -f "Dockerfile" ]; then
    echo -e "${GREEN}✓ Using standard Dockerfile${NC}"
    BUILD_OPTIONS+=("-f" "Dockerfile")
else
    echo -e "${RED}Error: Dockerfile not found${NC}"
    exit 1
fi

echo
echo -e "${YELLOW}Building development image...${NC}"
echo "This build is optimized for:"
echo "  • Fast rebuilds with layer caching"
echo "  • Volume mounts for hot-reloading"
echo "  • Development tools included"
echo "  • Debug-friendly configuration"
echo

# Execute build
$BUILD_CMD "${BUILD_OPTIONS[@]}" . || {
    echo -e "${RED}Build failed!${NC}"
    echo
    echo "Troubleshooting tips:"
    echo "1. Check Docker Desktop memory (Settings > Resources)"
    echo "2. Try clearing Docker cache: docker system prune -a"
    echo "3. Check for syntax errors in Dockerfile"
    exit 1
}

echo
echo -e "${GREEN}✅ Development build complete!${NC}"
echo
echo "Next steps:"
echo "1. Start services: docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d"
echo "2. View logs: docker compose logs -f backend"
echo "3. Code changes will hot-reload automatically"
echo
echo -e "${BLUE}Development tips:${NC}"
echo "• Your code is mounted as a volume - changes reflect instantly"
echo "• Backend runs with --reload flag for auto-restart"
echo "• Debug tools (ipdb, pdb) work with stdin"
echo "• Use docker compose exec backend bash to access container"