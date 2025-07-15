# 🚀 PRISM Deployment - Current Setup Guide

Based on your Neon and Upstash configuration, here's your specific deployment guide.

## 📋 Current Configuration

### Neon PostgreSQL Setup (From Screenshot)
- **Project Name**: `prism-db`
- **PostgreSQL Version**: 17
- **Region**: AWS US East 1 (N. Virginia)
- **Free Plan**: 0.5 GB storage, 24/7 database at 0.25 CU

### Upstash Redis Setup (From Screenshot)
- **Database Name**: `prism-cache`
- **Type**: Redis (Low-latency)
- **Commands**: 0 (just created)

## 🔧 Step 1: Complete Neon Setup

After clicking "Create project" in Neon:

1. **Copy your connection string** from the dashboard:
   ```
   postgresql://neondb_owner:XXXXXX@ep-XXXXX.us-east-1.aws.neon.tech/neondb?sslmode=require
   ```

2. **Create PRISM database schema**:
   
   Go to the Neon SQL Editor and run:
   ```sql
   -- Create required extensions
   CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
   
   -- Create enum types
   CREATE TYPE user_status AS ENUM ('active', 'inactive', 'pending');
   CREATE TYPE user_role AS ENUM ('admin', 'member', 'viewer');
   
   -- Users table
   CREATE TABLE users (
       id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
       email VARCHAR(255) UNIQUE NOT NULL,
       username VARCHAR(100) UNIQUE NOT NULL,
       password_hash VARCHAR(255) NOT NULL,
       full_name VARCHAR(255),
       status user_status DEFAULT 'pending',
       email_verified BOOLEAN DEFAULT FALSE,
       is_active BOOLEAN DEFAULT TRUE,
       is_superuser BOOLEAN DEFAULT FALSE,
       created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
       updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
   );
   
   -- Organizations table
   CREATE TABLE organizations (
       id SERIAL PRIMARY KEY,
       name VARCHAR(255) NOT NULL,
       slug VARCHAR(100) UNIQUE NOT NULL,
       owner_id UUID REFERENCES users(id),
       settings JSONB DEFAULT '{}',
       created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
       updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
   );
   
   -- Organization members
   CREATE TABLE organization_members (
       id SERIAL PRIMARY KEY,
       user_id UUID REFERENCES users(id) ON DELETE CASCADE,
       organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
       role VARCHAR(50) NOT NULL DEFAULT 'member',
       joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
       UNIQUE(user_id, organization_id)
   );
   
   -- Projects table
   CREATE TABLE projects (
       id SERIAL PRIMARY KEY,
       organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
       name VARCHAR(255) NOT NULL,
       key VARCHAR(20) NOT NULL,
       description TEXT,
       status VARCHAR(50) DEFAULT 'planning',
       owner_id UUID REFERENCES users(id),
       start_date DATE,
       end_date DATE,
       created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
       updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
       UNIQUE(organization_id, key)
   );
   
   -- Documents table
   CREATE TABLE documents (
       id SERIAL PRIMARY KEY,
       project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
       title VARCHAR(255) NOT NULL,
       slug VARCHAR(255) NOT NULL,
       content TEXT,
       document_type VARCHAR(50) NOT NULL,
       status VARCHAR(50) DEFAULT 'draft',
       creator_id UUID REFERENCES users(id),
       metadata JSONB DEFAULT '{}',
       created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
       updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
       published_at TIMESTAMP WITH TIME ZONE,
       UNIQUE(project_id, slug)
   );
   
   -- Create indexes
   CREATE INDEX idx_users_email ON users(email);
   CREATE INDEX idx_organizations_slug ON organizations(slug);
   CREATE INDEX idx_projects_organization_id ON projects(organization_id);
   CREATE INDEX idx_documents_project_id ON documents(project_id);
   ```

## 🔧 Step 2: Complete Upstash Setup

After creating your Redis database:

1. **Get your credentials** from Upstash dashboard:
   - **REST URL**: `https://XXXXX.upstash.io`
   - **REST Token**: `AXXXXXXX...`
   
2. **Test the connection**:
   ```bash
   curl -X POST https://YOUR-INSTANCE.upstash.io \
     -H "Authorization: Bearer YOUR-REST-TOKEN" \
     -d '["PING"]'
   
   # Should return: {"result":"PONG"}
   ```

## 🔧 Step 3: Update Environment Configuration

Update your `.env.production` file with actual values:

```bash
# ===== DATABASE (Neon PostgreSQL) =====
DATABASE_URL=postgresql://neondb_owner:YOUR-PASSWORD@ep-YOUR-ENDPOINT.us-east-1.aws.neon.tech/neondb?sslmode=require

# ===== REDIS (Upstash) =====
UPSTASH_REDIS_REST_URL=https://YOUR-INSTANCE.upstash.io
UPSTASH_REDIS_REST_TOKEN=YOUR-REST-TOKEN

# ===== SECURITY (Keep these as generated) =====
SECRET_KEY=0a6c2e3f6cf70fa1f3e442932af087bb8c437a498ad9f7c9145321ad98ef2c74
JWT_SECRET_KEY=5617ccf9d5fb1a5f15ccf1ff76a1909f91266fdfea5176fa574dc662c9ee164b

# ===== ENVIRONMENT =====
ENVIRONMENT=production
BACKEND_URL=https://prism-backend.onrender.com     # Update after deployment
FRONTEND_URL=https://prism-app.vercel.app          # Update after deployment

# ===== AI CONFIGURATION =====
DEFAULT_LLM_PROVIDER=mock
DEFAULT_LLM_MODEL=mock-model
```

## 🚀 Step 4: Deploy to Render

1. **Push to GitHub** (if not already done):
   ```bash
   git add .
   git commit -m "Configure Neon and Upstash for deployment"
   git push origin main
   ```

2. **Create Render Web Service**:
   - Go to [render.com](https://render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure:
     ```
     Name: prism-backend
     Region: Oregon (US West) or Ohio (US East)
     Branch: main
     Root Directory: (leave empty)
     Runtime: Docker
     ```

3. **Add Environment Variables** in Render:
   Copy each line from your `.env.production`:
   ```
   DATABASE_URL=postgresql://...
   UPSTASH_REDIS_REST_URL=https://...
   UPSTASH_REDIS_REST_TOKEN=...
   SECRET_KEY=...
   JWT_SECRET_KEY=...
   ENVIRONMENT=production
   DEFAULT_LLM_PROVIDER=mock
   PORT=8000
   ```

4. **Deploy** and wait for the build to complete

## 🚀 Step 5: Deploy Frontend to Vercel

1. **Update `frontend/.env.production`**:
   ```bash
   NEXT_PUBLIC_API_URL=https://prism-backend.onrender.com
   NEXT_PUBLIC_APP_URL=https://prism-app.vercel.app
   NEXTAUTH_URL=https://prism-app.vercel.app
   NEXTAUTH_SECRET=51d40a411f7a7a9024eac82a75cb0087b1a34077efdb98ead80314485ee757d7
   ```

2. **Deploy to Vercel**:
   - Go to [vercel.com](https://vercel.com)
   - Import your repository
   - Set root directory to `frontend`
   - Add environment variables
   - Deploy

## 🔧 Step 6: Initialize Database

Once backend is deployed, initialize the database:

1. **Option A: Using Render Shell**:
   ```bash
   cd backend
   python -m alembic upgrade head
   ```

2. **Option B: Using initialization script**:
   Create a temporary script and run it:
   ```python
   # init_db.py
   import os
   import psycopg2
   from psycopg2.extras import RealDictCursor
   
   # Use your Neon connection string
   DATABASE_URL = "postgresql://..."
   
   conn = psycopg2.connect(DATABASE_URL)
   cur = conn.cursor()
   
   # Create default organization
   cur.execute("""
       INSERT INTO organizations (name, slug, settings)
       VALUES ('Default Organization', 'default-org', '{}')
       ON CONFLICT (slug) DO NOTHING
       RETURNING id
   """)
   org_id = cur.fetchone()[0]
   
   # Create admin user
   # Password hash for 'Admin123!@#'
   password_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiLXCJLPWoeC"
   
   cur.execute("""
       INSERT INTO users (email, username, password_hash, full_name, status, email_verified, is_active, is_superuser)
       VALUES ('admin@example.com', 'admin', %s, 'Admin User', 'active', TRUE, TRUE, TRUE)
       ON CONFLICT (email) DO NOTHING
       RETURNING id
   """, (password_hash,))
   user_id = cur.fetchone()[0]
   
   # Link user to organization
   cur.execute("""
       INSERT INTO organization_members (user_id, organization_id, role)
       VALUES (%s, %s, 'admin')
       ON CONFLICT DO NOTHING
   """, (user_id, org_id))
   
   conn.commit()
   print("✅ Database initialized successfully!")
   ```

## ✅ Step 7: Verify Deployment

1. **Check Backend Health**:
   ```bash
   curl https://prism-backend.onrender.com/health
   ```

2. **Check API Documentation**:
   - Visit: https://prism-backend.onrender.com/docs

3. **Test Login**:
   - Go to your frontend URL
   - Login with: `admin@example.com` / `Admin123!@#`

## 📊 Monitoring Your Free Tier Usage

### Neon Dashboard
- Monitor at: https://console.neon.tech
- Check: Storage usage (0.5 GB limit)
- Check: Compute usage

### Upstash Dashboard  
- Monitor at: https://console.upstash.com
- Check: Daily commands (10k limit)
- Check: Data size

### Render Dashboard
- Monitor at: https://dashboard.render.com
- Check: Service health
- Check: Deploy status

## 🚨 Important Notes

1. **Cold Starts**: Render free tier sleeps after 15 minutes. First request will take 30-60 seconds.

2. **Database Connections**: Neon autosuspends after 5 minutes of inactivity. Use connection pooling.

3. **Redis Limits**: Upstash free tier allows 10,000 commands per day. Monitor usage.

4. **Bandwidth**: Vercel provides 100GB/month on free tier.

## 🆘 Troubleshooting

If you encounter issues:

1. **Check Render logs** for backend errors
2. **Verify environment variables** are set correctly
3. **Test database connection** using psql
4. **Ensure CORS** is configured for your frontend URL

Need help? Check the [troubleshooting guide](./docs/DEPLOYMENT_TROUBLESHOOTING.md) or open an issue!

---

Your deployment is now ready! The combination of Neon (US-East-1) and Upstash provides excellent performance for a free tier setup. 🚀