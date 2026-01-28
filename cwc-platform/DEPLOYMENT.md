# CWC Platform - Deployment Guide

This guide covers deploying the CWC Platform using Docker.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- Domain name with SSL certificate (for production)

## Quick Start (Development)

```bash
# Clone the repository
git clone <repository-url>
cd cwc-platform

# Create environment file from template
cp backend/.env.example .env

# Edit .env with your configuration
# At minimum, set:
# - SECRET_KEY (generate with: openssl rand -hex 32)
# - POSTGRES_PASSWORD (strong password for production)

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

The application will be available at:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8001
- **API Docs:** http://localhost:8001/docs

## Production Deployment

### 1. Environment Configuration

Create a production `.env` file with secure values:

```bash
# Generate a secure secret key
openssl rand -hex 32

# Create .env
cp backend/.env.example .env
```

Required production settings:

```env
# Database - use strong password
POSTGRES_USER=cwc_user
POSTGRES_PASSWORD=<strong-random-password>
POSTGRES_DB=cwc_platform

# Security - generated secret key
SECRET_KEY=<generated-secret-key>

# URLs - your domain
FRONTEND_URL=https://app.yourdomain.com
NEXT_PUBLIC_API_URL=https://api.yourdomain.com

# Email
SENDGRID_API_KEY=<your-sendgrid-api-key>
SENDGRID_FROM_EMAIL=noreply@yourdomain.com

# Payments
STRIPE_SECRET_KEY=<your-stripe-secret-key>
STRIPE_WEBHOOK_SECRET=<your-stripe-webhook-secret>

# OAuth
GOOGLE_CLIENT_ID=<your-google-client-id>
GOOGLE_CLIENT_SECRET=<your-google-client-secret>
NEXT_PUBLIC_GOOGLE_CLIENT_ID=<your-google-client-id>

# AI Features
ANTHROPIC_API_KEY=<your-anthropic-api-key>

# Zoom
ZOOM_CLIENT_ID=<your-zoom-client-id>
ZOOM_CLIENT_SECRET=<your-zoom-client-secret>
ZOOM_REDIRECT_URI=https://api.yourdomain.com/api/integrations/zoom/callback
```

### 2. Build and Deploy

```bash
# Build images
docker-compose build

# Start in detached mode
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head
```

### 3. Reverse Proxy (Nginx/Traefik)

For production, use a reverse proxy for SSL termination. Example Nginx configuration:

```nginx
# API server
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Frontend server
server {
    listen 443 ssl http2;
    server_name app.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Docker Commands Reference

```bash
# Build specific service
docker-compose build backend
docker-compose build frontend

# Restart a service
docker-compose restart backend

# View logs for a service
docker-compose logs -f backend

# Execute command in container
docker-compose exec backend bash
docker-compose exec db psql -U postgres -d cwc_platform

# Remove containers and volumes (CAUTION: deletes database)
docker-compose down -v
```

## Database Management

### Backup

```bash
# Create backup
docker-compose exec db pg_dump -U postgres cwc_platform > backup_$(date +%Y%m%d).sql

# Or using docker directly
docker exec cwc-db pg_dump -U postgres cwc_platform > backup.sql
```

### Restore

```bash
# Restore from backup
cat backup.sql | docker-compose exec -T db psql -U postgres cwc_platform
```

### Migrations

```bash
# Run pending migrations
docker-compose exec backend alembic upgrade head

# Check migration status
docker-compose exec backend alembic current

# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "description"
```

## Scaling

The services can be scaled using Docker Compose:

```bash
# Scale backend (if using load balancer)
docker-compose up -d --scale backend=3
```

Note: When scaling the backend, you'll need a load balancer (like nginx or traefik) to distribute requests.

## Health Checks

The docker-compose.yml includes health checks:

- **Database:** Uses `pg_isready` to verify PostgreSQL is accepting connections
- **Backend:** Waits for database to be healthy before starting

Check service health:

```bash
docker-compose ps
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs backend

# Check if ports are in use
lsof -i :3000
lsof -i :8001
```

### Database connection issues

```bash
# Test database connectivity
docker-compose exec db psql -U postgres -c "SELECT 1"

# Check if database exists
docker-compose exec db psql -U postgres -l
```

### Build failures

```bash
# Clean build cache
docker-compose build --no-cache

# Remove all containers and rebuild
docker-compose down
docker system prune -f
docker-compose up -d --build
```

## Cloud Deployment Options

### Railway

1. Create a new project
2. Add PostgreSQL database
3. Connect GitHub repository
4. Set environment variables
5. Deploy

### DigitalOcean App Platform

1. Create new app from GitHub
2. Configure backend and frontend as separate services
3. Add managed PostgreSQL database
4. Set environment variables
5. Deploy

### AWS (ECS/Fargate)

1. Push images to ECR
2. Create ECS cluster
3. Set up task definitions for each service
4. Create RDS PostgreSQL instance
5. Configure ALB for load balancing
6. Deploy services

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `SECRET_KEY` | Yes | JWT signing key |
| `FRONTEND_URL` | Yes | Frontend URL for CORS and emails |
| `SENDGRID_API_KEY` | No | SendGrid API key for emails |
| `STRIPE_SECRET_KEY` | No | Stripe secret key for payments |
| `STRIPE_WEBHOOK_SECRET` | No | Stripe webhook verification |
| `GOOGLE_CLIENT_ID` | No | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | No | Google OAuth client secret |
| `ANTHROPIC_API_KEY` | No | Claude API key for AI features |
| `ZOOM_CLIENT_ID` | No | Zoom app client ID |
| `ZOOM_CLIENT_SECRET` | No | Zoom app client secret |
| `ZOOM_REDIRECT_URI` | No | Zoom OAuth callback URL |
