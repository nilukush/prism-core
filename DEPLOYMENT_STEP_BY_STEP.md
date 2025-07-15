# 🚀 PRISM Free Tier Deployment - Step by Step Guide

This guide walks you through deploying PRISM on free tier services with **zero cost**.

## 📋 Prerequisites

- GitHub account
- Basic command line knowledge
- 30-45 minutes of time

## 🎯 Services We'll Use (All Free)

1. **Neon** - PostgreSQL Database (3GB free)
2. **Upstash** - Redis Cache (10k commands/day free)
3. **Render** - Backend Hosting (750 hours/month free)
4. **Vercel** - Frontend Hosting (unlimited free)

## 📖 Step-by-Step Instructions

### Step 1: Fork and Clone Repository

```bash
# Fork the repository on GitHub first
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/prism-core.git
cd prism-core
```

### Step 2: Create Neon Database (5 minutes)

1. **Go to [neon.tech](https://neon.tech)**
2. **Click "Sign Up"** - Use GitHub OAuth (no credit card)
3. **Create a new project:**
   - Project name: `prism-db`
   - Database name: `prism`
   - Region: Choose closest to you (e.g., US East)
4. **Copy the connection string** - It looks like:
   ```
   postgresql://username:password@ep-cool-darkness-123456.us-east-2.aws.neon.tech/prism?sslmode=require
   ```
5. **Save this for later!**

### Step 3: Create Upstash Redis (5 minutes)

1. **Go to [upstash.com](https://upstash.com)**
2. **Click "Sign Up"** - Use GitHub OAuth (no credit card)
3. **Click "Create Database"**
   - Name: `prism-cache`
   - Type: Regional
   - Region: Same as your database
   - Enable TLS: Yes
4. **Copy these values:**
   - REST URL: `https://us1-xxxxx.upstash.io`
   - REST Token: `AX3sACQgN2M0YjA...`
5. **Save these for later!**

### Step 4: Prepare Environment Files

Create `.env.production` in the root directory:

```bash
# Database (from Neon)
DATABASE_URL=postgresql://username:password@ep-cool-darkness-123456.us-east-2.aws.neon.tech/prism?sslmode=require

# Redis (from Upstash)
UPSTASH_REDIS_REST_URL=https://us1-xxxxx.upstash.io
UPSTASH_REDIS_REST_TOKEN=AX3sACQgN2M0YjA...

# Security (generate these)
SECRET_KEY=your-secret-key-here-32-chars-long!!
JWT_SECRET_KEY=your-jwt-secret-32-chars-long!!!

# Environment
ENVIRONMENT=production
BACKEND_URL=https://prism-backend.onrender.com  # Update after deployment
FRONTEND_URL=https://prism-app.vercel.app       # Update after deployment

# AI Provider
DEFAULT_LLM_PROVIDER=mock

# CORS
CORS_ALLOWED_ORIGINS=https://prism-app.vercel.app,http://localhost:3000
```

To generate secure keys:
```bash
# On Mac/Linux
openssl rand -hex 32
openssl rand -hex 32

# Or use Python
python -c "import secrets; print(secrets.token_hex(32))"
python -c "import secrets; print(secrets.token_hex(32))"
```

### Step 5: Deploy Backend to Render (10 minutes)

1. **Go to [render.com](https://render.com)**
2. **Sign up with GitHub** (no credit card)
3. **Click "New +" → "Web Service"**
4. **Connect your GitHub account and repository**
5. **Configure the service:**
   
   **Basic Settings:**
   - Name: `prism-backend` (or your choice)
   - Region: Oregon, USA (or closest to you)
   - Branch: `main`
   - Root Directory: `./` (leave empty)
   - Runtime: Docker
   
   **Build Settings:**
   - Build Command: Leave empty (uses Dockerfile)
   - Start Command: Leave empty (uses Dockerfile)

6. **Click "Advanced" and add environment variables:**
   
   Copy each line from your `.env.production`:
   - `DATABASE_URL` = (your Neon connection string)
   - `UPSTASH_REDIS_REST_URL` = (your Upstash URL)
   - `UPSTASH_REDIS_REST_TOKEN` = (your Upstash token)
   - `SECRET_KEY` = (your generated secret)
   - `JWT_SECRET_KEY` = (your generated JWT secret)
   - `ENVIRONMENT` = production
   - `DEFAULT_LLM_PROVIDER` = mock
   - `PORT` = 8000

7. **Click "Create Web Service"**
8. **Wait for deployment** (5-10 minutes first time)
9. **Copy your Render URL**: `https://prism-backend.onrender.com`

### Step 6: Initialize Database

Once backend is deployed:

1. **Go to Render dashboard**
2. **Click on your service → "Shell" tab**
3. **Run these commands:**

```bash
# Run database migrations
cd backend
python -m alembic upgrade head

# Create default admin user
python -c "
from src.database import get_db, engine
from src.models.user import User
from src.models.organization import Organization, OrganizationMember
from src.core.security import hash_password
from sqlalchemy.orm import Session
import uuid

# Create session
db = Session(engine)

# Create organization
org = Organization(
    name='Default Organization',
    slug='default-org',
    settings={}
)
db.add(org)
db.commit()

# Create admin user
user = User(
    id=str(uuid.uuid4()),
    email='admin@example.com',
    username='admin',
    password_hash=hash_password('Admin123!@#'),
    full_name='Admin User',
    is_active=True,
    is_superuser=True,
    email_verified=True
)
db.add(user)
db.commit()

# Link to organization
member = OrganizationMember(
    user_id=user.id,
    organization_id=org.id,
    role='admin'
)
db.add(member)
db.commit()

print('✅ Database initialized!')
"
```

### Step 7: Deploy Frontend to Vercel (10 minutes)

1. **Create `frontend/.env.production`:**

```bash
NEXT_PUBLIC_API_URL=https://prism-backend.onrender.com  # Your Render URL
NEXT_PUBLIC_APP_URL=https://prism-app.vercel.app       # Will update after deploy
NEXTAUTH_URL=https://prism-app.vercel.app              # Will update after deploy
NEXTAUTH_SECRET=your-nextauth-secret-32-chars!!!        # Generate new secret
```

2. **Go to [vercel.com](https://vercel.com)**
3. **Sign up with GitHub** (no credit card)
4. **Click "Add New..." → "Project"**
5. **Import your GitHub repository**
6. **Configure the project:**
   
   **Framework Preset:** Next.js (auto-detected)
   **Root Directory:** `frontend` ⚠️ IMPORTANT
   **Build Settings:**
   - Build Command: `npm run build`
   - Output Directory: `.next`
   - Install Command: `npm install`

7. **Add Environment Variables** (click "Environment Variables"):
   - `NEXT_PUBLIC_API_URL` = https://prism-backend.onrender.com
   - `NEXT_PUBLIC_APP_URL` = https://prism-app.vercel.app
   - `NEXTAUTH_URL` = https://prism-app.vercel.app
   - `NEXTAUTH_SECRET` = (generate a new 32-char secret)

8. **Click "Deploy"**
9. **Wait for build** (3-5 minutes)
10. **Copy your Vercel URL**: `https://prism-xxxx.vercel.app`

### Step 8: Update Backend CORS

1. **Go back to Render dashboard**
2. **Update environment variable:**
   - `CORS_ALLOWED_ORIGINS` = https://prism-xxxx.vercel.app,http://localhost:3000
   - `FRONTEND_URL` = https://prism-xxxx.vercel.app
3. **Click "Save Changes"** - This triggers redeploy

### Step 9: Test Your Deployment

1. **Visit your frontend URL**: https://prism-xxxx.vercel.app
2. **Login with default credentials:**
   - Email: `admin@example.com`
   - Password: `Admin123!@#`
3. **Create a test project**
4. **Generate a test PRD**

## 🎉 Congratulations!

You now have PRISM running in production for **$0/month**!

## 📊 Monitor Your Usage

### Check Free Tier Limits

**Neon Dashboard:**
- Storage used (3GB limit)
- Compute hours

**Upstash Dashboard:**
- Daily commands (10k limit)
- Storage used

**Render Dashboard:**
- Service hours (750/month)
- Deploy count

**Vercel Dashboard:**
- Bandwidth (100GB/month)
- Function invocations

## 🚨 Important Notes

### Cold Starts
- Render free tier sleeps after 15 minutes of inactivity
- First request after sleep takes 30-60 seconds
- Solution: Use a service like UptimeRobot to ping every 14 minutes

### Database Backups
Neon free tier includes 7-day history. For longer retention:
```bash
# Manual backup (run monthly)
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

### Upgrade Path
When you need to upgrade:
1. **First**: Database (when approaching 3GB)
2. **Second**: Backend hosting (for no sleep)
3. **Third**: Redis (for more commands)
4. **Last**: Frontend (rarely needed)

## 🆘 Troubleshooting

### "Application Error" on Render
1. Check Render logs: Dashboard → Logs
2. Verify all environment variables are set
3. Check database connection string

### "500 Error" on Frontend
1. Check browser console for errors
2. Verify API URL is correct
3. Check CORS settings on backend

### Database Connection Failed
1. Check connection string format
2. Ensure SSL mode is `require`
3. Check if database is active in Neon dashboard

### Login Not Working
1. Verify database was initialized
2. Check JWT_SECRET matches on backend
3. Clear browser cookies and try again

## 📚 Next Steps

1. **Set up monitoring**: [UptimeRobot](https://uptimerobot.com) (free)
2. **Configure backups**: See backup script in `/scripts`
3. **Customize settings**: Update organization name and branding
4. **Add team members**: Invite collaborators
5. **Start building**: Create projects and generate PRDs!

## 🤝 Need Help?

- GitHub Issues: [Report problems](https://github.com/nilukush/prism-core/issues)
- Discussions: [Ask questions](https://github.com/nilukush/prism-core/discussions)
- Documentation: [Read the docs](./docs)

---

**Remember**: This setup is perfect for MVPs and proof-of-concepts. As you grow, the upgrade path is smooth and incremental!