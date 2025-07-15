#!/bin/bash

# PRISM Quick Deploy Script
# This script helps you quickly deploy PRISM with Neon and Upstash

set -e

echo "🚀 PRISM Quick Deploy Script"
echo "============================"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command_exists python3; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

if ! command_exists node; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    exit 1
fi

if ! command_exists docker; then
    echo -e "${YELLOW}⚠️  Docker is not installed (optional for local development)${NC}"
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"
echo ""

# Check if .env exists
if [ -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file already exists. Backing up to .env.backup${NC}"
    cp .env .env.backup
fi

# Copy .env.example to .env if it doesn't exist
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo "📝 Creating .env file from template..."
        cp .env.example .env
    else
        echo -e "${RED}❌ .env.example not found${NC}"
        exit 1
    fi
fi

echo ""
echo "🔧 Configuration Setup"
echo "====================="
echo ""
echo "Please provide your configuration values:"
echo ""

# Function to update .env file
update_env() {
    local key=$1
    local value=$2
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|^${key}=.*|${key}=\"${value}\"|" .env
    else
        # Linux
        sed -i "s|^${key}=.*|${key}=\"${value}\"|" .env
    fi
}

# Get Neon database URL
echo -e "${YELLOW}📊 Neon PostgreSQL Configuration${NC}"
echo "Get your connection string from: https://console.neon.tech"
echo -n "Enter your Neon DATABASE_URL: "
read -r DATABASE_URL
update_env "DATABASE_URL" "$DATABASE_URL"

echo ""
echo -e "${YELLOW}🗄️  Upstash Redis Configuration${NC}"
echo "Get your connection details from: https://console.upstash.com"
echo -n "Enter your Upstash REDIS_URL: "
read -r REDIS_URL
update_env "REDIS_URL" "$REDIS_URL"

echo -n "Enter your Upstash REST URL (optional, press Enter to skip): "
read -r UPSTASH_REDIS_REST_URL
if [ ! -z "$UPSTASH_REDIS_REST_URL" ]; then
    update_env "UPSTASH_REDIS_REST_URL" "$UPSTASH_REDIS_REST_URL"
fi

echo -n "Enter your Upstash REST Token (optional, press Enter to skip): "
read -r UPSTASH_REDIS_REST_TOKEN
if [ ! -z "$UPSTASH_REDIS_REST_TOKEN" ]; then
    update_env "UPSTASH_REDIS_REST_TOKEN" "$UPSTASH_REDIS_REST_TOKEN"
fi

# Generate secret key
echo ""
echo "🔐 Generating secure secret key..."
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
update_env "SECRET_KEY" "$SECRET_KEY"
echo -e "${GREEN}✅ Secret key generated${NC}"

# AI Provider configuration
echo ""
echo -e "${YELLOW}🤖 AI Provider Configuration${NC}"
echo -n "Enter your OpenAI API Key (optional, press Enter to skip): "
read -rs OPENAI_API_KEY
echo ""
if [ ! -z "$OPENAI_API_KEY" ]; then
    update_env "OPENAI_API_KEY" "$OPENAI_API_KEY"
fi

echo -n "Enter your Anthropic API Key (optional, press Enter to skip): "
read -rs ANTHROPIC_API_KEY
echo ""
if [ ! -z "$ANTHROPIC_API_KEY" ]; then
    update_env "ANTHROPIC_API_KEY" "$ANTHROPIC_API_KEY"
fi

echo ""
echo -e "${GREEN}✅ Configuration completed!${NC}"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
echo ""

# Python dependencies
if [ -f requirements.txt ]; then
    echo "Installing Python dependencies..."
    pip3 install -r requirements.txt
    echo -e "${GREEN}✅ Python dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  requirements.txt not found, skipping Python dependencies${NC}"
fi

# Node dependencies (if frontend exists)
if [ -f package.json ]; then
    echo "Installing Node dependencies..."
    npm install
    echo -e "${GREEN}✅ Node dependencies installed${NC}"
fi

echo ""
echo "🗄️  Setting up database..."
echo ""

# Create database schema
cat > setup_db.py << 'EOF'
import os
import psycopg2
from urllib.parse import urlparse

# Parse database URL
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("❌ DATABASE_URL not found in environment")
    exit(1)

url = urlparse(DATABASE_URL)

try:
    # Connect to database
    conn = psycopg2.connect(
        host=url.hostname,
        port=url.port,
        user=url.username,
        password=url.password,
        database=url.path[1:],
        sslmode='require'
    )
    
    cursor = conn.cursor()
    
    # Read and execute schema
    schema_file = 'prism-deployment-guide.md'
    if os.path.exists(schema_file):
        with open(schema_file, 'r') as f:
            content = f.read()
            # Extract SQL from markdown
            import re
            sql_blocks = re.findall(r'```sql\n(.*?)\n```', content, re.DOTALL)
            
            for sql in sql_blocks:
                if 'CREATE' in sql:
                    try:
                        cursor.execute(sql)
                        conn.commit()
                        print("✅ Database schema created successfully")
                    except Exception as e:
                        if 'already exists' in str(e):
                            print("ℹ️  Schema already exists")
                        else:
                            print(f"⚠️  Schema creation warning: {e}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Database connection error: {e}")
    exit(1)
EOF

# Load environment variables and run setup
export $(cat .env | grep -v '^#' | xargs)
python3 setup_db.py
rm setup_db.py

echo ""
echo "🏃 Starting the application..."
echo ""

# Check if running with Docker
if command_exists docker && [ -f docker-compose.yml ]; then
    echo "Starting with Docker Compose..."
    docker-compose up -d
    echo -e "${GREEN}✅ Application started with Docker${NC}"
    echo "Access the application at: http://localhost:8000"
    echo "View logs with: docker-compose logs -f"
else
    # Start with Python directly
    if [ -f prism/api/main.py ] || [ -f main.py ]; then
        echo "Starting FastAPI application..."
        echo -e "${GREEN}✅ Run the following command to start the server:${NC}"
        echo ""
        echo "  uvicorn prism.api.main:app --reload --host 0.0.0.0 --port 8000"
        echo ""
        echo "Or if using a different structure:"
        echo "  python main.py"
    else
        echo -e "${YELLOW}⚠️  Could not find main application file${NC}"
    fi
fi

echo ""
echo "🎉 Deployment setup complete!"
echo ""
echo "📚 Next steps:"
echo "  1. Access the API documentation at: http://localhost:8000/docs"
echo "  2. Check the health endpoint at: http://localhost:8000/health"
echo "  3. Review logs for any errors"
echo "  4. Set up monitoring dashboards"
echo ""
echo "📖 For more information, see:"
echo "  - Deployment Guide: ./prism-deployment-guide.md"
echo "  - Environment Variables: .env"
echo "  - Neon Dashboard: https://console.neon.tech"
echo "  - Upstash Dashboard: https://console.upstash.com"
echo ""
echo "Need help? Check the troubleshooting section in the deployment guide."