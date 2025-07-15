#!/bin/bash

# PRISM Deployment Preparation Script
# This script prepares your environment for free tier deployment

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 PRISM Deployment Preparation${NC}"
echo "================================"
echo ""

# Function to generate secure key
generate_key() {
    if command -v openssl &> /dev/null; then
        openssl rand -hex 32
    else
        # Fallback to urandom
        tr -dc 'a-f0-9' < /dev/urandom | head -c 64
    fi
}

# Check if we're in PRISM root
if [ ! -d "backend" ] || [ ! -d "frontend" ] || [ ! -f "docker-compose.yml" ]; then
    echo -e "${YELLOW}⚠️  Please run from PRISM root directory${NC}"
    exit 1
fi

# Generate secure keys
echo -e "${BLUE}🔐 Generating secure keys...${NC}"
SECRET_KEY=$(generate_key)
JWT_SECRET=$(generate_key)
NEXTAUTH_SECRET=$(generate_key)

# Create .env.production
echo -e "${BLUE}📝 Creating .env.production...${NC}"
cat > .env.production <<EOF
# PRISM Production Environment Configuration
# Generated on: $(date)

# ===== DATABASE (Neon PostgreSQL) =====
# Get this from: https://neon.tech
DATABASE_URL=postgresql://username:password@host/database?sslmode=require

# ===== REDIS (Upstash) =====
# Get these from: https://upstash.com
UPSTASH_REDIS_REST_URL=https://your-instance.upstash.io
UPSTASH_REDIS_REST_TOKEN=your-upstash-token

# ===== SECURITY =====
# Auto-generated secure keys
SECRET_KEY=${SECRET_KEY}
JWT_SECRET_KEY=${JWT_SECRET}

# ===== ENVIRONMENT =====
ENVIRONMENT=production
BACKEND_URL=https://your-app.onrender.com     # Update after Render deployment
FRONTEND_URL=https://your-app.vercel.app      # Update after Vercel deployment

# ===== AI CONFIGURATION =====
DEFAULT_LLM_PROVIDER=mock
DEFAULT_LLM_MODEL=mock-model

# ===== CORS =====
# Update with your Vercel URL
CORS_ALLOWED_ORIGINS=https://your-app.vercel.app,http://localhost:3000

# ===== RATE LIMITING =====
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60

# ===== OTHER SETTINGS =====
LOG_LEVEL=INFO
DOCS_ENABLED=true
EOF

# Create frontend/.env.production
echo -e "${BLUE}📝 Creating frontend/.env.production...${NC}"
cat > frontend/.env.production <<EOF
# PRISM Frontend Production Configuration
# Generated on: $(date)

# ===== API CONFIGURATION =====
# Update with your Render backend URL
NEXT_PUBLIC_API_URL=https://your-app.onrender.com

# ===== APP CONFIGURATION =====
# Update with your Vercel frontend URL
NEXT_PUBLIC_APP_URL=https://your-app.vercel.app
NEXTAUTH_URL=https://your-app.vercel.app

# ===== AUTHENTICATION =====
# Auto-generated secure key
NEXTAUTH_SECRET=${NEXTAUTH_SECRET}

# ===== FEATURES =====
NEXT_PUBLIC_ENABLE_AI=true
NEXT_PUBLIC_ENABLE_ANALYTICS=false
EOF

# Create deployment checklist
echo -e "${BLUE}📋 Creating deployment checklist...${NC}"
cat > DEPLOYMENT_CHECKLIST.txt <<EOF
PRISM FREE TIER DEPLOYMENT CHECKLIST
====================================
Generated on: $(date)

PRE-DEPLOYMENT:
□ Fork repository to your GitHub account
□ Clone your fork locally
□ Run this preparation script ✓

DATABASE SETUP (Neon):
□ Create account at https://neon.tech
□ Create new project "prism-db"
□ Copy connection string
□ Update DATABASE_URL in .env.production

REDIS SETUP (Upstash):
□ Create account at https://upstash.com
□ Create Redis database "prism-cache"
□ Copy REST URL and Token
□ Update UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN

BACKEND DEPLOYMENT (Render):
□ Create account at https://render.com
□ Create new Web Service
□ Connect GitHub repository
□ Set root directory to ./
□ Choose Docker runtime
□ Add all environment variables from .env.production
□ Deploy and copy URL
□ Update BACKEND_URL in .env.production

FRONTEND DEPLOYMENT (Vercel):
□ Create account at https://vercel.com
□ Import repository
□ Set root directory to ./frontend
□ Add environment variables from frontend/.env.production
□ Deploy and copy URL
□ Update all URLs in both .env files

POST-DEPLOYMENT:
□ Initialize database (run migrations)
□ Test login with admin@example.com / Admin123!@#
□ Update backend CORS with frontend URL
□ Set up monitoring (UptimeRobot)
□ Test all features
□ Update README with your URLs

SECURE KEYS GENERATED:
SECRET_KEY: ${SECRET_KEY:0:16}...
JWT_SECRET_KEY: ${JWT_SECRET:0:16}...
NEXTAUTH_SECRET: ${NEXTAUTH_SECRET:0:16}...
EOF

# Create quick reference
echo -e "${BLUE}📄 Creating quick reference...${NC}"
cat > DEPLOYMENT_URLS.txt <<EOF
PRISM DEPLOYMENT QUICK REFERENCE
================================

SERVICES TO SIGN UP:
1. Neon (Database): https://neon.tech
2. Upstash (Redis): https://upstash.com
3. Render (Backend): https://render.com
4. Vercel (Frontend): https://vercel.com

YOUR DEPLOYMENT URLS (Update these):
- Frontend: https://your-app.vercel.app
- Backend: https://your-app.onrender.com
- API Docs: https://your-app.onrender.com/docs

DEFAULT CREDENTIALS:
- Email: admin@example.com
- Password: Admin123!@#

IMPORTANT: Change the default password after first login!
EOF

echo ""
echo -e "${GREEN}✅ Deployment preparation complete!${NC}"
echo ""
echo "Files created:"
echo "  • .env.production"
echo "  • frontend/.env.production"
echo "  • DEPLOYMENT_CHECKLIST.txt"
echo "  • DEPLOYMENT_URLS.txt"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Review the files created"
echo "2. Follow DEPLOYMENT_CHECKLIST.txt"
echo "3. Start with creating accounts on the free services"
echo ""
echo -e "${BLUE}📖 Full guide: DEPLOYMENT_STEP_BY_STEP.md${NC}"
echo ""
echo "Good luck with your deployment! 🚀"