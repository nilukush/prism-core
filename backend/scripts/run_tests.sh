#!/bin/bash
# PRISM Test Runner Script
# Provides various test execution options

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Default values
TEST_TYPE="all"
COVERAGE=true
VERBOSE=false
MARKERS=""
PARALLEL=false
DOCKER=false

# Help function
show_help() {
    echo "PRISM Test Runner"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -t, --type TYPE       Test type: all|unit|integration|e2e (default: all)"
    echo "  -m, --marker MARKER   Run tests with specific marker"
    echo "  -k, --keyword EXPR    Run tests matching keyword expression"
    echo "  -f, --file FILE       Run specific test file"
    echo "  -c, --no-coverage     Disable coverage reporting"
    echo "  -v, --verbose         Enable verbose output"
    echo "  -p, --parallel        Run tests in parallel"
    echo "  -d, --docker          Run tests in Docker container"
    echo "  -h, --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -t unit                    # Run only unit tests"
    echo "  $0 -m slow                    # Run tests marked as slow"
    echo "  $0 -k 'auth or user'          # Run tests matching keywords"
    echo "  $0 -f tests/unit/test_auth.py # Run specific test file"
    echo "  $0 -p -t integration          # Run integration tests in parallel"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            TEST_TYPE="$2"
            shift 2
            ;;
        -m|--marker)
            MARKERS="$2"
            shift 2
            ;;
        -k|--keyword)
            KEYWORD="$2"
            shift 2
            ;;
        -f|--file)
            TEST_FILE="$2"
            shift 2
            ;;
        -c|--no-coverage)
            COVERAGE=false
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -p|--parallel)
            PARALLEL=true
            shift
            ;;
        -d|--docker)
            DOCKER=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Build pytest command
PYTEST_CMD="pytest"

# Add test type marker
case $TEST_TYPE in
    unit)
        PYTEST_CMD="$PYTEST_CMD -m unit"
        ;;
    integration)
        PYTEST_CMD="$PYTEST_CMD -m integration"
        ;;
    e2e)
        PYTEST_CMD="$PYTEST_CMD -m e2e"
        ;;
    all)
        # No marker needed
        ;;
    *)
        echo -e "${RED}Invalid test type: $TEST_TYPE${NC}"
        exit 1
        ;;
esac

# Add custom markers
if [ -n "$MARKERS" ]; then
    if [ "$TEST_TYPE" != "all" ]; then
        PYTEST_CMD="$PYTEST_CMD and $MARKERS"
    else
        PYTEST_CMD="$PYTEST_CMD -m $MARKERS"
    fi
fi

# Add keyword filter
if [ -n "$KEYWORD" ]; then
    PYTEST_CMD="$PYTEST_CMD -k '$KEYWORD'"
fi

# Add specific file
if [ -n "$TEST_FILE" ]; then
    PYTEST_CMD="$PYTEST_CMD $TEST_FILE"
fi

# Add coverage options
if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=src --cov-report=term-missing --cov-report=html --cov-report=xml"
else
    PYTEST_CMD="$PYTEST_CMD --no-cov"
fi

# Add verbose flag
if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -vv"
fi

# Add parallel execution
if [ "$PARALLEL" = true ]; then
    # Detect number of CPUs
    if [[ "$OSTYPE" == "darwin"* ]]; then
        CPUS=$(sysctl -n hw.ncpu)
    else
        CPUS=$(nproc)
    fi
    PYTEST_CMD="$PYTEST_CMD -n $CPUS"
fi

# Function to check services
check_services() {
    echo -e "${BLUE}Checking required services...${NC}"
    
    # Check PostgreSQL
    if ! nc -z localhost 5432 2>/dev/null; then
        echo -e "${YELLOW}Warning: PostgreSQL not running on port 5432${NC}"
        echo "Integration tests may fail. Start with: docker compose up -d postgres"
    fi
    
    # Check Redis
    if ! nc -z localhost 6379 2>/dev/null; then
        echo -e "${YELLOW}Warning: Redis not running on port 6379${NC}"
        echo "Some tests may fail. Start with: docker compose up -d redis"
    fi
}

# Function to run tests locally
run_tests_local() {
    # Check if in backend directory
    if [ ! -f "pyproject.toml" ]; then
        echo -e "${RED}Error: Not in backend directory${NC}"
        echo "Please run from backend/ directory"
        exit 1
    fi
    
    # Check services for integration tests
    if [[ "$TEST_TYPE" == "integration" || "$TEST_TYPE" == "all" ]]; then
        check_services
    fi
    
    # Create test database if needed
    if [[ "$TEST_TYPE" == "integration" || "$TEST_TYPE" == "all" ]]; then
        echo -e "${BLUE}Setting up test database...${NC}"
        export DATABASE_URL="postgresql+asyncpg://prism:prism@localhost:5432/prism_test"
        
        # Create test database if it doesn't exist
        PGPASSWORD=prism psql -h localhost -U prism -d prism -c "CREATE DATABASE prism_test;" 2>/dev/null || true
    fi
    
    # Run tests
    echo -e "${BLUE}Running tests...${NC}"
    echo -e "${BLUE}Command: $PYTEST_CMD${NC}"
    echo ""
    
    # Set test environment variables
    export ENVIRONMENT=test
    export REDIS_URL=redis://localhost:6379/15
    
    # Execute tests
    eval $PYTEST_CMD
    TEST_EXIT_CODE=$?
    
    # Show coverage report location
    if [ "$COVERAGE" = true ] && [ $TEST_EXIT_CODE -eq 0 ]; then
        echo ""
        echo -e "${GREEN}Coverage report generated:${NC}"
        echo "  - Terminal: See above"
        echo "  - HTML: file://$(pwd)/htmlcov/index.html"
        echo "  - XML: coverage.xml"
    fi
    
    return $TEST_EXIT_CODE
}

# Function to run tests in Docker
run_tests_docker() {
    echo -e "${BLUE}Running tests in Docker...${NC}"
    
    # Build test command for Docker
    DOCKER_CMD="docker compose run --rm"
    
    # Add environment variables
    DOCKER_CMD="$DOCKER_CMD -e ENVIRONMENT=test"
    DOCKER_CMD="$DOCKER_CMD -e DATABASE_URL=postgresql+asyncpg://prism:prism@postgres:5432/prism_test"
    DOCKER_CMD="$DOCKER_CMD -e REDIS_URL=redis://redis:6379/15"
    
    # Add the service and command
    DOCKER_CMD="$DOCKER_CMD backend $PYTEST_CMD"
    
    echo -e "${BLUE}Command: $DOCKER_CMD${NC}"
    echo ""
    
    # Ensure services are running
    docker compose up -d postgres redis
    
    # Wait for services to be ready
    echo -e "${BLUE}Waiting for services to be ready...${NC}"
    sleep 5
    
    # Create test database
    docker compose exec -T postgres psql -U prism -c "CREATE DATABASE prism_test;" 2>/dev/null || true
    
    # Run tests
    eval $DOCKER_CMD
    TEST_EXIT_CODE=$?
    
    # Copy coverage reports if generated
    if [ "$COVERAGE" = true ] && [ $TEST_EXIT_CODE -eq 0 ]; then
        docker compose cp backend:/app/htmlcov ./htmlcov 2>/dev/null || true
        docker compose cp backend:/app/coverage.xml ./coverage.xml 2>/dev/null || true
        
        echo ""
        echo -e "${GREEN}Coverage report generated:${NC}"
        echo "  - HTML: file://$(pwd)/htmlcov/index.html"
        echo "  - XML: coverage.xml"
    fi
    
    return $TEST_EXIT_CODE
}

# Main execution
echo ""
echo "================================"
echo "    PRISM Test Runner"
echo "================================"
echo ""

# Run tests
if [ "$DOCKER" = true ]; then
    run_tests_docker
else
    run_tests_local
fi

EXIT_CODE=$?

# Summary
echo ""
echo "================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}    Tests Passed! ✓${NC}"
else
    echo -e "${RED}    Tests Failed! ✗${NC}"
fi
echo "================================"
echo ""

exit $EXIT_CODE