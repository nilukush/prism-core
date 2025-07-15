#!/bin/bash
# Docker Build Fix Script for Poetry EOF Error
# This script implements enterprise-grade solutions for the BuildKit EOF error

echo "=== Docker Build Fix for Poetry Installation ==="
echo

# Solution 1: Disable BuildKit (most reliable)
echo "1. Disabling BuildKit..."
export DOCKER_BUILDKIT=0
echo "   DOCKER_BUILDKIT=0 set"

# Solution 2: Clear Docker cache
echo
echo "2. Clearing Docker build cache..."
docker builder prune -a -f 2>/dev/null || echo "   Note: Docker may need to be restarted"

# Solution 3: Increase Docker Desktop resources
echo
echo "3. Docker Desktop Resource Recommendations:"
echo "   - Memory: Minimum 4GB (8GB recommended)"
echo "   - CPUs: Minimum 2 (4 recommended)"
echo "   - Disk: Ensure at least 10GB free space"
echo "   - Check: Docker Desktop > Settings > Resources"

# Solution 4: Build with optimized settings
echo
echo "4. Building with optimized settings..."
echo

# Check if Docker is running
if ! docker ps >/dev/null 2>&1; then
    echo "ERROR: Docker is not running!"
    echo "Please start Docker Desktop and run this script again."
    exit 1
fi

# Build command with all optimizations
docker compose -f docker-compose.yml -f docker-compose.dev.yml build \
    --no-cache \
    --progress=plain \
    backend

echo
echo "Build complete! If the error persists, try these additional steps:"
echo "1. Restart Docker Desktop"
echo "2. On Windows/WSL2: Run 'wsl --shutdown' then restart Docker"
echo "3. Use the optimized Dockerfile provided in docker-build-optimized.Dockerfile"