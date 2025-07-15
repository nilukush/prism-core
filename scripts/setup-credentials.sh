#!/bin/bash

# PRISM Credentials Setup Script
# This script helps you quickly set up your Neon and Upstash credentials

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════╗"
echo "║     PRISM Credentials Setup Helper        ║"
echo "╚═══════════════════════════════════════════╝"
echo -e "${NC}"

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    echo -e "${RED}❌ .env.production not found!${NC}"
    echo -e "${YELLOW}Run ./scripts/prepare-deployment.sh first${NC}"
    exit 1
fi

# Function to update env file
update_env() {
    local key=$1
    local value=$2
    local file=$3
    
    if grep -q "^${key}=" "$file"; then
        # Use different delimiter to handle URLs with slashes
        sed -i.bak "s|^${key}=.*|${key}=${value}|" "$file"
        echo -e "${GREEN}✓ Updated ${key}${NC}"
    else
        echo "${key}=${value}" >> "$file"
        echo -e "${GREEN}✓ Added ${key}${NC}"
    fi
}

# Get Neon credentials
echo -e "\n${BLUE}Step 1: Neon PostgreSQL Setup${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${YELLOW}Go to: https://console.neon.tech${NC}"
echo "Copy your connection string from the dashboard"
echo ""
read -p "Paste your Neon connection string: " NEON_URL

if [[ $NEON_URL == postgresql://* ]]; then
    update_env "DATABASE_URL" "$NEON_URL" ".env.production"
    echo -e "${GREEN}✓ Neon credentials saved!${NC}"
else
    echo -e "${RED}❌ Invalid PostgreSQL URL format${NC}"
    exit 1
fi

# Get Upstash credentials
echo -e "\n${BLUE}Step 2: Upstash Redis Setup${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${YELLOW}Go to: https://console.upstash.com${NC}"
echo "From your Redis database details page, copy:"
echo ""
read -p "Paste your Upstash REST URL: " UPSTASH_URL
read -p "Paste your Upstash REST Token: " UPSTASH_TOKEN

if [[ $UPSTASH_URL == https://* ]]; then
    update_env "UPSTASH_REDIS_REST_URL" "$UPSTASH_URL" ".env.production"
    update_env "UPSTASH_REDIS_REST_TOKEN" "$UPSTASH_TOKEN" ".env.production"
    echo -e "${GREEN}✓ Upstash credentials saved!${NC}"
else
    echo -e "${RED}❌ Invalid Upstash URL format${NC}"
    exit 1
fi

# Update backend URL
echo -e "\n${BLUE}Step 3: Deployment URLs (Optional)${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "After deploying to Render and Vercel, update these:"
echo ""
read -p "Backend URL (or press Enter to skip): " BACKEND_URL
if [ -n "$BACKEND_URL" ]; then
    update_env "BACKEND_URL" "$BACKEND_URL" ".env.production"
    update_env "CORS_ALLOWED_ORIGINS" "$BACKEND_URL,http://localhost:3000" ".env.production"
fi

read -p "Frontend URL (or press Enter to skip): " FRONTEND_URL
if [ -n "$FRONTEND_URL" ]; then
    update_env "FRONTEND_URL" "$FRONTEND_URL" ".env.production"
    
    # Update frontend env too
    if [ -f "frontend/.env.production" ]; then
        update_env "NEXT_PUBLIC_API_URL" "${BACKEND_URL:-https://your-app.onrender.com}" "frontend/.env.production"
        update_env "NEXT_PUBLIC_APP_URL" "$FRONTEND_URL" "frontend/.env.production"
        update_env "NEXTAUTH_URL" "$FRONTEND_URL" "frontend/.env.production"
    fi
fi

# Test connections
echo -e "\n${BLUE}Step 4: Test Connections${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━"
read -p "Test connections now? (y/N): " test_conn

if [[ $test_conn =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Testing connections...${NC}"
    python scripts/verify-connections.py
fi

# Summary
echo -e "\n${GREEN}════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Credentials Setup Complete!${NC}"
echo -e "${GREEN}════════════════════════════════════${NC}"
echo ""
echo "Next steps:"
echo "1. Run database migrations in Neon SQL Editor"
echo "2. Deploy backend to Render"
echo "3. Deploy frontend to Vercel"
echo "4. Update URLs and test again"
echo ""
echo -e "${BLUE}Check DEPLOYMENT_FINAL_CONFIG.md for detailed instructions!${NC}"

# Clean up backup files
rm -f .env.production.bak frontend/.env.production.bak 2>/dev/null || true