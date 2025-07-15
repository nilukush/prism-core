#!/bin/bash
# Direct build command with BuildKit disabled
# This is the most reliable solution for the EOF error

echo "Building backend with BuildKit disabled..."
echo "This avoids the 'failed to receive status: EOF' error"
echo

# Export BuildKit disabled
export DOCKER_BUILDKIT=0

# Build the backend service directly
docker build \
    --progress=plain \
    --target development \
    -t prism-core-backend \
    -f Dockerfile \
    .

if [ $? -eq 0 ]; then
    echo
    echo "Build successful! Now you can run:"
    echo "docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d"
else
    echo
    echo "Build failed. Try these steps:"
    echo "1. Restart Docker Desktop"
    echo "2. Clear Docker cache: docker system prune -a"
    echo "3. Increase Docker Desktop memory to at least 4GB"
fi