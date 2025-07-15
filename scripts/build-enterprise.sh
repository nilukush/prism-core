#!/bin/bash
# Enterprise-Grade Docker Build Script
# Following 2024-2025 best practices from Fortune 500 and FAANG companies

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
DOCKER_REGISTRY="${DOCKER_REGISTRY:-docker.io}"
DOCKER_IMAGE="${DOCKER_IMAGE:-prism-backend}"
VERSION="${VERSION:-latest}"
BUILD_TARGET="${BUILD_TARGET:-production}"
PLATFORM="${PLATFORM:-linux/amd64}"
PYTHON_VERSION="${PYTHON_VERSION:-3.12}"
POETRY_VERSION="${POETRY_VERSION:-1.7.1}"

# Get git commit hash for tagging
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "no-git")

echo -e "${GREEN}🚀 Enterprise Docker Build Script${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Registry: $DOCKER_REGISTRY"
echo "Image: $DOCKER_IMAGE"
echo "Version: $VERSION"
echo "Target: $BUILD_TARGET"
echo "Platform: $PLATFORM"
echo "Git Commit: $GIT_COMMIT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# Check Docker version and BuildKit support
check_docker_version() {
    echo -e "${YELLOW}Checking Docker environment...${NC}"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker is not installed${NC}"
        exit 1
    fi
    
    DOCKER_VERSION=$(docker version --format '{{.Server.Version}}' 2>/dev/null || echo "0.0.0")
    DOCKER_MAJOR=$(echo $DOCKER_VERSION | cut -d. -f1)
    
    if [ "$DOCKER_MAJOR" -lt "23" ]; then
        echo -e "${YELLOW}Warning: Docker version $DOCKER_VERSION detected. Version 23+ recommended for best BuildKit support${NC}"
    else
        echo -e "${GREEN}✓ Docker version $DOCKER_VERSION${NC}"
    fi
    
    # Check if BuildKit is available
    if docker buildx version &> /dev/null; then
        echo -e "${GREEN}✓ Docker BuildKit available${NC}"
        USE_BUILDX=true
    else
        echo -e "${YELLOW}Warning: Docker BuildKit not available. Using legacy builder${NC}"
        USE_BUILDX=false
    fi
}

# Setup BuildKit builder
setup_buildkit() {
    if [ "$USE_BUILDX" = true ]; then
        echo -e "${YELLOW}Setting up BuildKit builder...${NC}"
        
        # Create or use existing builder
        if ! docker buildx ls | grep -q "prism-builder"; then
            docker buildx create --name prism-builder --driver docker-container --bootstrap
        fi
        
        docker buildx use prism-builder
        echo -e "${GREEN}✓ BuildKit builder ready${NC}"
    fi
}

# Build with enterprise features
build_image() {
    echo -e "${YELLOW}Building Docker image...${NC}"
    
    BUILD_ARGS=(
        "--build-arg" "PYTHON_VERSION=$PYTHON_VERSION"
        "--build-arg" "POETRY_VERSION=$POETRY_VERSION"
        "--target" "$BUILD_TARGET"
        "--tag" "$DOCKER_REGISTRY/$DOCKER_IMAGE:$VERSION"
        "--tag" "$DOCKER_REGISTRY/$DOCKER_IMAGE:$GIT_COMMIT"
        "--file" "Dockerfile.enterprise"
    )
    
    # Add cache arguments if using BuildKit
    if [ "$USE_BUILDX" = true ]; then
        BUILD_ARGS+=(
            "--cache-from" "type=registry,ref=$DOCKER_REGISTRY/$DOCKER_IMAGE:buildcache"
            "--cache-to" "type=registry,ref=$DOCKER_REGISTRY/$DOCKER_IMAGE:buildcache,mode=max"
            "--platform" "$PLATFORM"
            "--progress" "plain"
        )
        
        # Add security scanning if available
        if command -v trivy &> /dev/null; then
            BUILD_ARGS+=("--output" "type=docker,name=$DOCKER_IMAGE:scan")
        fi
        
        # Execute build with buildx
        docker buildx build "${BUILD_ARGS[@]}" .
    else
        # Fallback to regular docker build
        export DOCKER_BUILDKIT=1
        docker build "${BUILD_ARGS[@]}" .
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Build successful${NC}"
    else
        echo -e "${RED}✗ Build failed${NC}"
        exit 1
    fi
}

# Security scanning
security_scan() {
    echo -e "${YELLOW}Running security scan...${NC}"
    
    if command -v trivy &> /dev/null; then
        trivy image --severity HIGH,CRITICAL "$DOCKER_REGISTRY/$DOCKER_IMAGE:$VERSION"
        echo -e "${GREEN}✓ Security scan complete${NC}"
    else
        echo -e "${YELLOW}Trivy not installed. Skipping security scan${NC}"
        echo "Install with: brew install aquasecurity/trivy/trivy"
    fi
}

# Image optimization report
optimization_report() {
    echo -e "${YELLOW}Generating optimization report...${NC}"
    
    # Get image size
    SIZE=$(docker image inspect "$DOCKER_REGISTRY/$DOCKER_IMAGE:$VERSION" --format='{{.Size}}' | numfmt --to=iec)
    echo "Image size: $SIZE"
    
    # Analyze layers
    docker history "$DOCKER_REGISTRY/$DOCKER_IMAGE:$VERSION" --no-trunc --format "table {{.CreatedBy}}\t{{.Size}}"
    
    echo -e "${GREEN}✓ Optimization report complete${NC}"
}

# Main execution
main() {
    echo -e "${GREEN}Starting enterprise build process...${NC}"
    echo
    
    # Step 1: Check environment
    check_docker_version
    echo
    
    # Step 2: Setup BuildKit if available
    setup_buildkit
    echo
    
    # Step 3: Build image
    build_image
    echo
    
    # Step 4: Security scan
    security_scan
    echo
    
    # Step 5: Optimization report
    optimization_report
    echo
    
    echo -e "${GREEN}🎉 Enterprise build complete!${NC}"
    echo
    echo "Next steps:"
    echo "1. Test locally: docker run -p 8000:8000 $DOCKER_REGISTRY/$DOCKER_IMAGE:$VERSION"
    echo "2. Push to registry: docker push $DOCKER_REGISTRY/$DOCKER_IMAGE:$VERSION"
    echo "3. Deploy to Kubernetes: kubectl set image deployment/backend backend=$DOCKER_REGISTRY/$DOCKER_IMAGE:$VERSION"
}

# Handle script arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --target)
            BUILD_TARGET="$2"
            shift 2
            ;;
        --version)
            VERSION="$2"
            shift 2
            ;;
        --platform)
            PLATFORM="$2"
            shift 2
            ;;
        --registry)
            DOCKER_REGISTRY="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --target [production|development|testing]  Build target (default: production)"
            echo "  --version VERSION                         Image version tag (default: latest)"
            echo "  --platform PLATFORM                       Target platform (default: linux/amd64)"
            echo "  --registry REGISTRY                       Docker registry (default: docker.io)"
            echo "  --help                                    Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run main function
main