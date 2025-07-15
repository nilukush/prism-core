# Deployment Guide

This guide covers deploying PRISM to production environments.

## Prerequisites

- Docker and Docker Compose
- Domain name with DNS configured
- SSL certificate (or use Let's Encrypt)
- Cloud provider account (AWS, GCP, Azure, or VPS)

## Production Checklist

### 1. Security Configuration

#### Environment Variables
```bash
# Generate secure keys
openssl rand -hex 32  # For SECRET_KEY
openssl rand -hex 32  # For JWT_SECRET_KEY

# Update .env.production
cp .env.example .env.production
# Edit all values, especially:
# - SECRET_KEY
# - DATABASE_URL
# - REDIS_PASSWORD
# - API keys
```

#### Database Security
```sql
-- Create production database and user
CREATE USER prism_prod WITH ENCRYPTED PASSWORD 'strong-password';
CREATE DATABASE prism_production OWNER prism_prod;
GRANT ALL PRIVILEGES ON DATABASE prism_production TO prism_prod;
```

### 2. Docker Production Setup

#### Build Production Images
```bash
# Backend
docker build -t prism-backend:latest -f Dockerfile --target production .

# Frontend
docker build -t prism-frontend:latest -f frontend/Dockerfile --target production frontend/
```

#### docker-compose.production.yml
```yaml
version: '3.8'

services:
  backend:
    image: prism-backend:latest
    restart: always
    environment:
      - ENVIRONMENT=production
    env_file:
      - .env.production
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    image: prism-frontend:latest
    restart: always
    environment:
      - NODE_ENV=production
    env_file:
      - .env.production

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - backend
      - frontend
```

### 3. Nginx Configuration

Create `nginx.conf`:
```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:3000;
    }

    server {
        listen 80;
        server_name your-domain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # Backend API
        location /api {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # WebSocket support
        location /ws {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }
}
```

### 4. Database Backup

Set up automated backups:
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
DB_NAME="prism_production"

# Create backup
docker exec postgres pg_dump -U prism_prod $DB_NAME | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete
```

Add to crontab:
```bash
0 2 * * * /path/to/backup.sh
```

### 5. Monitoring Setup

#### Health Checks
- Backend: `https://your-domain.com/api/v1/health`
- Frontend: `https://your-domain.com/`

#### Logging
```bash
# View logs
docker compose -f docker-compose.production.yml logs -f

# Export logs
docker compose -f docker-compose.production.yml logs > prism_logs_$(date +%Y%m%d).txt
```

### 6. Deployment Steps

```bash
# 1. Clone repository
git clone https://github.com/nilukush/prism-core.git
cd prism-core

# 2. Set up environment
cp .env.example .env.production
# Edit .env.production with production values

# 3. Build images
docker compose -f docker-compose.yml -f docker-compose.production.yml build

# 4. Run migrations
docker compose -f docker-compose.yml -f docker-compose.production.yml run --rm backend alembic upgrade head

# 5. Start services
docker compose -f docker-compose.yml -f docker-compose.production.yml up -d

# 6. Check status
docker compose -f docker-compose.yml -f docker-compose.production.yml ps
```

## Cloud Provider Guides

### AWS Deployment

#### Using ECS (Elastic Container Service)
1. Push images to ECR
2. Create ECS task definitions
3. Set up ALB (Application Load Balancer)
4. Configure RDS for PostgreSQL
5. Use ElastiCache for Redis

#### Using EC2
1. Launch EC2 instance (t3.large minimum)
2. Install Docker and Docker Compose
3. Follow standard deployment steps
4. Set up security groups

### Google Cloud Platform

#### Using Cloud Run
1. Push images to Container Registry
2. Deploy to Cloud Run
3. Use Cloud SQL for PostgreSQL
4. Use Memorystore for Redis

### Azure

#### Using Container Instances
1. Push images to Container Registry
2. Create Container Instance groups
3. Use Azure Database for PostgreSQL
4. Use Azure Cache for Redis

### DigitalOcean

#### Using App Platform
1. Connect GitHub repository
2. Configure build settings
3. Set environment variables
4. Deploy with one click

## Kubernetes Deployment

See the `/k8s` directory for Kubernetes manifests:

```bash
# Apply base configuration
kubectl apply -k k8s/base/

# Apply production overlay
kubectl apply -k k8s/overlays/prod/
```

## SSL/TLS Configuration

### Let's Encrypt (Recommended)
```bash
# Install certbot
apt-get install certbot

# Generate certificate
certbot certonly --standalone -d your-domain.com

# Auto-renewal
echo "0 0 * * * root certbot renew --quiet" >> /etc/crontab
```

### Commercial SSL
1. Purchase SSL certificate
2. Place files in `./ssl/` directory
3. Update nginx.conf paths

## Performance Optimization

### 1. Enable Caching
```python
# In .env.production
CACHE_TTL_DEFAULT=3600
CACHE_TTL_DOCUMENTS=7200
```

### 2. CDN Setup
- Static assets: CloudFlare, AWS CloudFront
- API caching: Varnish, Redis

### 3. Database Optimization
```sql
-- Add missing indexes
CREATE INDEX CONCURRENTLY idx_documents_search 
ON documents USING gin(to_tsvector('english', title || ' ' || content));

-- Vacuum regularly
VACUUM ANALYZE;
```

## Scaling

### Horizontal Scaling
```yaml
# docker-compose.production.yml
backend:
  deploy:
    replicas: 3
```

### Load Balancing
- Use Nginx upstream with multiple backend instances
- Configure session affinity if needed

## Troubleshooting

### Common Issues

1. **502 Bad Gateway**
   - Check if backend is running
   - Verify nginx upstream configuration

2. **Database Connection Errors**
   - Check DATABASE_URL
   - Verify PostgreSQL is accessible

3. **Redis Connection Errors**
   - Check REDIS_URL and password
   - Ensure Redis is running

### Debug Mode
```bash
# Enable debug logging
ENVIRONMENT=production DEBUG=true docker compose up
```

## Security Hardening

1. **Firewall Rules**
   - Only expose ports 80 and 443
   - Restrict SSH access

2. **Regular Updates**
   ```bash
   docker compose pull
   docker compose up -d
   ```

3. **Security Headers**
   - Already configured in backend
   - Additional headers in nginx.conf

4. **Rate Limiting**
   - Enabled by default
   - Adjust limits in .env.production

## Maintenance

### Regular Tasks
- Weekly backups verification
- Monthly security updates
- Quarterly performance review

### Update Procedure
```bash
# 1. Backup database
./backup.sh

# 2. Pull latest changes
git pull origin main

# 3. Rebuild and deploy
docker compose -f docker-compose.yml -f docker-compose.production.yml up -d --build

# 4. Run migrations
docker compose exec backend alembic upgrade head
```

## Support

For deployment support:
- [GitHub Issues](https://github.com/nilukush/prism-core/issues)
- [Deployment Discussions](https://github.com/nilukush/prism-core/discussions/categories/deployment)