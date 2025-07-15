#!/bin/bash

# PRISM Deploy to Render Script
# This script helps you deploy PRISM to Render with all required environment variables

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════╗"
echo "║      PRISM Deploy to Render               ║"
echo "╚═══════════════════════════════════════════╝"
echo -e "${NC}"

# Check if render CLI is installed
if ! command -v render &> /dev/null; then
    echo -e "${YELLOW}Render CLI not found. Install it with:${NC}"
    echo "brew tap render-oss/render"
    echo "brew install render"
    echo ""
    echo "Or deploy manually at https://dashboard.render.com"
    echo ""
fi

# Security check
echo -e "${RED}⚠️  SECURITY CHECK${NC}"
echo "Have you removed API keys from .env.production? (y/n)"
read -p "> " security_check

if [[ ! $security_check =~ ^[Yy]$ ]]; then
    echo -e "${RED}Please remove API keys from files before deploying!${NC}"
    echo "Add them directly in Render dashboard instead."
    exit 1
fi

# Display environment variables checklist
echo -e "\n${BLUE}📋 Environment Variables Checklist${NC}"
echo "Make sure you have these values ready:"
echo ""
echo "✓ Database (Neon):"
echo "  - DATABASE_URL"
echo ""
echo "✓ Redis (Upstash):"
echo "  - UPSTASH_REDIS_REST_URL"
echo "  - UPSTASH_REDIS_REST_TOKEN"
echo ""
echo "✓ Security:"
echo "  - SECRET_KEY (32 chars)"
echo "  - JWT_SECRET_KEY (32 chars)"
echo ""
echo "✓ AI Configuration:"
echo "  - OPENAI_API_KEY or ANTHROPIC_API_KEY"
echo ""

read -p "Press Enter to continue..."

# Create render.yaml if it doesn't exist
if [ ! -f "render.yaml" ]; then
    echo -e "\n${BLUE}Creating render.yaml...${NC}"
    cat > render.yaml << 'EOF'
services:
  - type: web
    name: prism-backend
    runtime: docker
    dockerfilePath: ./Dockerfile
    dockerContext: ./
    branch: main
    region: oregon
    plan: free
    
    healthCheckPath: /health
    
    envVars:
      - key: PORT
        value: 8000
      - key: ENVIRONMENT
        value: production
      - key: LOG_LEVEL
        value: INFO
      - key: BEHIND_PROXY
        value: true
      
      # Add other environment variables in Render dashboard
EOF
    echo -e "${GREEN}✓ render.yaml created${NC}"
fi

# Display deployment instructions
echo -e "\n${BLUE}📚 Deployment Instructions${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Go to https://dashboard.render.com"
echo ""
echo "2. Click 'New +' → 'Web Service'"
echo ""
echo "3. Connect your GitHub repository"
echo ""
echo "4. Configure:"
echo "   - Name: prism-backend"
echo "   - Region: Oregon (US West)"
echo "   - Branch: main"
echo "   - Runtime: Docker"
echo "   - Instance Type: Free"
echo ""
echo "5. Add ALL environment variables from RENDER_ENV_VARIABLES.md"
echo ""
echo "6. Click 'Create Web Service'"
echo ""

# Generate helper file
echo -e "\n${BLUE}📄 Generating environment template...${NC}"
cat > render-env-template.txt << 'EOF'
# Core Configuration
DATABASE_URL=
UPSTASH_REDIS_REST_URL=
UPSTASH_REDIS_REST_TOKEN=
SECRET_KEY=
JWT_SECRET_KEY=

# AI Configuration
DEFAULT_LLM_PROVIDER=openai
DEFAULT_LLM_MODEL=gpt-3.5-turbo
OPENAI_API_KEY=

# URLs (update after deployment)
BACKEND_URL=https://your-app.onrender.com
FRONTEND_URL=https://your-app.vercel.app
CORS_ALLOWED_ORIGINS=https://your-app.vercel.app,http://localhost:3000

# Cost Control
AI_CACHE_ENABLED=true
AI_CACHE_TTL=86400
AI_MONTHLY_BUDGET_USD=20
AI_USER_MONTHLY_LIMIT=50
RATE_LIMIT_AI_PER_MINUTE=5

# See RENDER_ENV_VARIABLES.md for complete list
EOF

echo -e "${GREEN}✓ Template created: render-env-template.txt${NC}"

# Cost warning
echo -e "\n${YELLOW}💰 Cost Protection Reminder${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Since this is an open source project, make sure:"
echo ""
echo "1. AI_CACHE_ENABLED=true (saves 80% costs)"
echo "2. AI_MONTHLY_BUDGET_USD=20 (hard limit)"
echo "3. RATE_LIMIT_AI_PER_MINUTE=5 (prevent abuse)"
echo "4. Set up OpenAI billing alerts"
echo ""

# Post-deployment steps
echo -e "${BLUE}📋 After Deployment${NC}"
echo "━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Get your Render URL:"
echo "   https://prism-backend.onrender.com"
echo ""
echo "2. Update these variables in Render:"
echo "   - BACKEND_URL=https://[your-url].onrender.com"
echo "   - CORS_ALLOWED_ORIGINS=https://[frontend].vercel.app"
echo ""
echo "3. Test your deployment:"
echo "   curl https://[your-url].onrender.com/health"
echo ""
echo "4. Monitor costs:"
echo "   - OpenAI: https://platform.openai.com/usage"
echo "   - Check daily for first week"
echo ""

# Security reminder
echo -e "${RED}🔐 Security Reminder${NC}"
echo "━━━━━━━━━━━━━━━━━━"
echo "1. Regenerate any exposed API keys"
echo "2. Never commit secrets to Git"
echo "3. Use Render's secret management"
echo "4. Enable 2FA on all accounts"
echo ""

echo -e "${GREEN}Ready to deploy! Follow the instructions above.${NC}"
echo -e "${BLUE}Full documentation: RENDER_ENV_VARIABLES.md${NC}"
echo ""

# Offer to open browser
if command -v open &> /dev/null; then
    echo "Open Render dashboard now? (y/n)"
    read -p "> " open_render
    if [[ $open_render =~ ^[Yy]$ ]]; then
        open "https://dashboard.render.com"
    fi
elif command -v xdg-open &> /dev/null; then
    echo "Open Render dashboard now? (y/n)"
    read -p "> " open_render
    if [[ $open_render =~ ^[Yy]$ ]]; then
        xdg-open "https://dashboard.render.com"
    fi
fi