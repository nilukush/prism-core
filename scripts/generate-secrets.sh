#!/bin/bash

# PRISM Secret Generation Script
# Generates secure secrets for production deployment

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}PRISM Secret Generation Script${NC}"
echo "================================"
echo ""

# Function to generate secure random string
generate_secret() {
    local length=${1:-32}
    openssl rand -base64 $length | tr -d "=+/" | cut -c1-$length
}

# Function to generate strong password
generate_password() {
    local length=${1:-20}
    # Generate password with uppercase, lowercase, numbers, and special characters
    openssl rand -base64 48 | tr -d "=+/" | cut -c1-$length
}

# Check if .env.production exists
if [ -f .env.production ]; then
    echo -e "${YELLOW}Warning: .env.production already exists${NC}"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting without changes"
        exit 0
    fi
fi

# Copy template if it doesn't exist
if [ ! -f .env.production.template ]; then
    echo -e "${RED}Error: .env.production.template not found${NC}"
    exit 1
fi

cp .env.production.template .env.production

echo "Generating secure secrets..."

# Generate main secrets
SECRET_KEY=$(generate_secret 32)
ENCRYPTION_KEY=$(generate_secret 32)
NEXTAUTH_SECRET=$(generate_secret 32)
WEBHOOK_SECRET=$(generate_secret 32)

# Generate passwords
DB_PASSWORD=$(generate_password 20)
REDIS_PASSWORD=$(generate_password 20)

# Update .env.production with generated values
sed -i.bak "s/SECRET_KEY=CHANGE_ME_GENERATE_UNIQUE_VALUE/SECRET_KEY=$SECRET_KEY/" .env.production
sed -i.bak "s/ENCRYPTION_KEY=CHANGE_ME_GENERATE_UNIQUE_VALUE/ENCRYPTION_KEY=$ENCRYPTION_KEY/" .env.production
sed -i.bak "s/NEXTAUTH_SECRET=CHANGE_ME_GENERATE_UNIQUE_VALUE/NEXTAUTH_SECRET=$NEXTAUTH_SECRET/" .env.production
sed -i.bak "s/WEBHOOK_SECRET=CHANGE_ME_GENERATE_UNIQUE_VALUE/WEBHOOK_SECRET=$WEBHOOK_SECRET/" .env.production

# Update passwords
sed -i.bak "s/:CHANGE_ME@/:$DB_PASSWORD@/" .env.production
sed -i.bak "s/POSTGRES_PASSWORD=CHANGE_ME/POSTGRES_PASSWORD=$DB_PASSWORD/" .env.production
sed -i.bak "s/REDIS_PASSWORD=CHANGE_ME/REDIS_PASSWORD=$REDIS_PASSWORD/" .env.production
sed -i.bak "s/:CHANGE_ME@redis/:$REDIS_PASSWORD@redis/" .env.production

# Clean up backup files
rm -f .env.production.bak

echo -e "${GREEN}✓ Secrets generated successfully${NC}"
echo ""
echo "Generated secrets:"
echo "=================="
echo "SECRET_KEY:      ${SECRET_KEY:0:10}... (hidden)"
echo "ENCRYPTION_KEY:  ${ENCRYPTION_KEY:0:10}... (hidden)"
echo "NEXTAUTH_SECRET: ${NEXTAUTH_SECRET:0:10}... (hidden)"
echo "WEBHOOK_SECRET:  ${WEBHOOK_SECRET:0:10}... (hidden)"
echo "DB_PASSWORD:     ${DB_PASSWORD:0:5}... (hidden)"
echo "REDIS_PASSWORD:  ${REDIS_PASSWORD:0:5}... (hidden)"
echo ""
echo -e "${YELLOW}Important: Please update the following manually:${NC}"
echo "- Domain names (yourdomain.com)"
echo "- Email settings (SMTP credentials)"
echo "- AI service API keys (if using)"
echo "- Monitoring endpoints (Sentry, OTEL)"
echo "- OAuth credentials (if using)"
echo ""
echo -e "${RED}Security reminder:${NC}"
echo "- NEVER commit .env.production to version control"
echo "- Store these secrets in a secure password manager"
echo "- Use different secrets for each environment"
echo "- Rotate secrets regularly"
echo ""

# Create .gitignore entry if not exists
if ! grep -q "^.env.production$" .gitignore 2>/dev/null; then
    echo ".env.production" >> .gitignore
    echo -e "${GREEN}✓ Added .env.production to .gitignore${NC}"
fi

# Create docker-compose override for production
cat > docker-compose.production.yml << 'EOF'
# Production docker-compose override
# Usage: docker compose -f docker-compose.yml -f docker-compose.production.yml up -d

version: '3.8'

services:
  backend:
    env_file:
      - .env.production
    environment:
      - ENVIRONMENT=production
      - NODE_ENV=production
    restart: always
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
  
  postgres:
    env_file:
      - .env.production
    restart: always
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
  
  redis:
    env_file:
      - .env.production
    restart: always
    command: redis-server /usr/local/etc/redis/redis.conf --requirepass ${REDIS_PASSWORD}
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
EOF

echo -e "${GREEN}✓ Created docker-compose.production.yml${NC}"
echo ""
echo "To start production services:"
echo "docker compose -f docker-compose.yml -f docker-compose.production.yml up -d"

# Set proper permissions
chmod 600 .env.production
echo -e "${GREEN}✓ Set secure permissions on .env.production (600)${NC}"

echo ""
echo -e "${GREEN}Secret generation complete!${NC}"