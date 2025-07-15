#!/bin/bash

# Detect and set the appropriate docker compose command
# This script handles both Docker Compose v1 and v2

# Try Docker Compose v2 first (recommended)
if docker compose version &> /dev/null; then
    export DOCKER_COMPOSE_CMD="docker compose"
    export DOCKER_COMPOSE_VERSION=$(docker compose version | grep -oE 'v[0-9]+\.[0-9]+\.[0-9]+')
    echo "Using Docker Compose v2: $DOCKER_COMPOSE_VERSION"
# Fall back to Docker Compose v1 if available
elif command -v docker-compose &> /dev/null; then
    export DOCKER_COMPOSE_CMD="docker-compose"
    export DOCKER_COMPOSE_VERSION=$(docker-compose version --short)
    echo "Using Docker Compose v1: $DOCKER_COMPOSE_VERSION (Consider upgrading to v2)"
else
    echo "Error: Docker Compose is not installed."
    echo "Please install Docker Desktop which includes Docker Compose v2."
    exit 1
fi