#!/bin/bash

# PRISM Free Tier Setup Script
# This script helps you set up PRISM on free tier services

set -e

echo "🚀 PRISM Free Tier Setup"
echo "========================"
echo ""

# Check if required tools are installed
check_requirements() {
    echo "📋 Checking requirements..."
    
    if ! command -v git &> /dev/null; then
        echo "❌ Git is not installed. Please install Git first."
        exit 1
    fi
    
    if ! command -v node &> /dev/null; then
        echo "❌ Node.js is not installed. Please install Node.js 18+ first."
        exit 1
    fi
    
    if ! command -v npm &> /dev/null; then
        echo "❌ npm is not installed. Please install npm first."
        exit 1
    fi
    
    echo "✅ All requirements met!"
    echo ""
}

# Create environment files
create_env_files() {
    echo "📝 Creating environment files..."
    
    # Backend .env
    cat > .env.production <<EOF
# Database (Neon PostgreSQL)
DATABASE_URL=postgresql://username:password@host/neondb?sslmode=require

# Redis (Upstash)
UPSTASH_REDIS_REST_URL=https://your-instance.upstash.io
UPSTASH_REDIS_REST_TOKEN=your-token

# Security
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)

# Environment
ENVIRONMENT=production
BACKEND_URL=https://prism-backend.onrender.com
FRONTEND_URL=https://prism-app.vercel.app

# AI Provider (using mock for free tier)
DEFAULT_LLM_PROVIDER=mock

# CORS
CORS_ALLOWED_ORIGINS=https://prism-app.vercel.app,http://localhost:3000
EOF

    # Frontend .env
    cat > frontend/.env.production <<EOF
NEXT_PUBLIC_API_URL=https://prism-backend.onrender.com
NEXT_PUBLIC_APP_URL=https://prism-app.vercel.app
NEXTAUTH_URL=https://prism-app.vercel.app
NEXTAUTH_SECRET=$(openssl rand -hex 32)
EOF

    echo "✅ Environment files created!"
    echo ""
}

# Setup instructions
show_setup_instructions() {
    echo "📚 Setup Instructions"
    echo "===================="
    echo ""
    echo "1️⃣  Database Setup (Neon)"
    echo "   • Go to https://neon.tech"
    echo "   • Sign up with GitHub (no credit card)"
    echo "   • Create a new project"
    echo "   • Copy the connection string"
    echo "   • Update DATABASE_URL in .env.production"
    echo ""
    echo "2️⃣  Redis Setup (Upstash)"
    echo "   • Go to https://upstash.com"
    echo "   • Sign up with GitHub (no credit card)"
    echo "   • Create a Redis database"
    echo "   • Copy REST URL and token"
    echo "   • Update UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN"
    echo ""
    echo "3️⃣  Backend Deployment (Render)"
    echo "   • Go to https://render.com"
    echo "   • Sign up with GitHub"
    echo "   • Click 'New +' → 'Web Service'"
    echo "   • Connect your GitHub repo"
    echo "   • Use the render.yaml file"
    echo "   • Copy environment variables from .env.production"
    echo ""
    echo "4️⃣  Frontend Deployment (Vercel)"
    echo "   • Go to https://vercel.com"
    echo "   • Sign up with GitHub"
    echo "   • Import your repository"
    echo "   • Set root directory to 'frontend'"
    echo "   • Copy environment variables from frontend/.env.production"
    echo ""
    echo "5️⃣  GitHub Actions Setup"
    echo "   • Get Render API key from dashboard"
    echo "   • Get Vercel token: vercel login && vercel tokens create"
    echo "   • Add secrets to GitHub repository:"
    echo "     - RENDER_API_KEY"
    echo "     - RENDER_SERVICE_ID"
    echo "     - VERCEL_TOKEN"
    echo "     - VERCEL_ORG_ID"
    echo "     - VERCEL_PROJECT_ID"
    echo ""
}

# Database initialization script
create_db_init_script() {
    echo "🗄️  Creating database initialization script..."
    
    cat > scripts/init-free-tier-db.sql <<EOF
-- Initialize PRISM database for free tier

-- Create default organization
INSERT INTO organizations (name, slug, settings, created_at, updated_at)
VALUES (
    'Default Organization',
    'default-org',
    '{"tier": "free", "features": ["basic"]}',
    NOW(),
    NOW()
) ON CONFLICT (slug) DO NOTHING;

-- Create admin user (update email and password hash as needed)
INSERT INTO users (id, email, username, password_hash, full_name, status, email_verified, created_at, updated_at)
VALUES (
    gen_random_uuid(),
    'admin@example.com',
    'admin',
    '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiLXCJLPWoeC', -- Password: Admin123!@#
    'Admin User',
    'active',
    true,
    NOW(),
    NOW()
) ON CONFLICT (email) DO NOTHING;

-- Link admin to organization
INSERT INTO organization_members (user_id, organization_id, role, joined_at)
SELECT u.id, o.id, 'admin', NOW()
FROM users u, organizations o
WHERE u.email = 'admin@example.com' AND o.slug = 'default-org'
ON CONFLICT DO NOTHING;

-- Create sample project
INSERT INTO projects (organization_id, name, key, description, status, owner_id, created_at, updated_at)
SELECT o.id, 'Sample Project', 'SAMP', 'A sample project to get started', 'active', u.id, NOW(), NOW()
FROM organizations o, users u
WHERE o.slug = 'default-org' AND u.email = 'admin@example.com'
ON CONFLICT DO NOTHING;
EOF

    echo "✅ Database init script created!"
    echo ""
}

# Create deployment checklist
create_checklist() {
    echo "📋 Creating deployment checklist..."
    
    cat > DEPLOYMENT_CHECKLIST.md <<EOF
# PRISM Free Tier Deployment Checklist

## Pre-Deployment
- [ ] Fork/clone repository
- [ ] Run setup-free-tier.sh script
- [ ] Create accounts on all platforms

## Database Setup (Neon)
- [ ] Create Neon account
- [ ] Create new project
- [ ] Copy connection string
- [ ] Update .env.production
- [ ] Run database migrations

## Redis Setup (Upstash)
- [ ] Create Upstash account
- [ ] Create Redis database
- [ ] Copy REST URL and token
- [ ] Update .env.production

## Backend Deployment (Render)
- [ ] Create Render account
- [ ] Create new Web Service
- [ ] Connect GitHub repository
- [ ] Configure environment variables
- [ ] Deploy and verify

## Frontend Deployment (Vercel)
- [ ] Create Vercel account
- [ ] Import repository
- [ ] Configure build settings
- [ ] Set environment variables
- [ ] Deploy and verify

## Post-Deployment
- [ ] Test authentication flow
- [ ] Create first project
- [ ] Generate sample PRD
- [ ] Set up monitoring
- [ ] Configure custom domain (optional)

## Monitoring Setup
- [ ] UptimeRobot account
- [ ] Configure health checks
- [ ] Set up alerts

## Documentation
- [ ] Update README with URLs
- [ ] Document any custom configurations
- [ ] Share with team
EOF

    echo "✅ Deployment checklist created!"
    echo ""
}

# Main execution
main() {
    check_requirements
    create_env_files
    create_db_init_script
    create_checklist
    
    echo "🎉 Setup Complete!"
    echo "=================="
    echo ""
    echo "Next steps:"
    echo "1. Review .env.production and frontend/.env.production"
    echo "2. Follow the setup instructions above"
    echo "3. Use DEPLOYMENT_CHECKLIST.md to track progress"
    echo ""
    echo "Files created:"
    echo "• .env.production"
    echo "• frontend/.env.production"
    echo "• scripts/init-free-tier-db.sql"
    echo "• DEPLOYMENT_CHECKLIST.md"
    echo ""
    echo "Happy deploying! 🚀"
}

# Run main function
main