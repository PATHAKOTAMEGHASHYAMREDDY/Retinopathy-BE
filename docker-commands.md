# Docker Commands for Retinopathy Backend

## 🐳 Basic Docker Commands

### Build Docker Image
```bash
# Development build
docker build -t retinopathy-backend:dev .

# Production build
docker build -f Dockerfile.prod -t retinopathy-backend:prod .

# Build with specific tag
docker build -t retinopathy-backend:v1.0.0 .
```

### Run Docker Container
```bash
# Development run (with volume mounting for live reload)
docker run -d \
  --name retinopathy-api \
  -p 5000:5000 \
  -v $(pwd):/app \
  -e MONGODB_URI="your_mongodb_uri" \
  -e JWT_SECRET_KEY="your_jwt_secret" \
  retinopathy-backend:dev

# Production run
docker run -d \
  --name retinopathy-api-prod \
  -p 5000:5000 \
  -e MONGODB_URI="your_mongodb_uri" \
  -e JWT_SECRET_KEY="your_jwt_secret" \
  retinopathy-backend:prod

# Run with environment file
docker run -d \
  --name retinopathy-api \
  -p 5000:5000 \
  --env-file .env \
  retinopathy-backend:dev
```

## 🚀 Docker Compose Commands

### Development Environment
```bash
# Start all services
docker-compose up

# Start in detached mode
docker-compose up -d

# Build and start
docker-compose up --build

# Start specific service
docker-compose up retinopathy-backend

# View logs
docker-compose logs -f retinopathy-backend

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Production Environment
```bash
# Start production services
docker-compose -f docker-compose.prod.yml up -d

# Build and start production
docker-compose -f docker-compose.prod.yml up --build -d

# View production logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop production services
docker-compose -f docker-compose.prod.yml down
```

## 🔧 Container Management

### Container Operations
```bash
# List running containers
docker ps

# List all containers
docker ps -a

# Stop container
docker stop retinopathy-api

# Start container
docker start retinopathy-api

# Restart container
docker restart retinopathy-api

# Remove container
docker rm retinopathy-api

# Execute command in running container
docker exec -it retinopathy-api bash

# View container logs
docker logs -f retinopathy-api
```

### Image Management
```bash
# List images
docker images

# Remove image
docker rmi retinopathy-backend:dev

# Remove unused images
docker image prune

# Remove all unused images
docker image prune -a
```

## 🧹 Cleanup Commands

### Clean Up Everything
```bash
# Remove stopped containers
docker container prune

# Remove unused networks
docker network prune

# Remove unused volumes
docker volume prune

# Remove everything unused
docker system prune

# Remove everything including unused images
docker system prune -a
```

## 📊 Monitoring Commands

### Container Stats
```bash
# View resource usage
docker stats

# View specific container stats
docker stats retinopathy-api

# Container information
docker inspect retinopathy-api

# Container processes
docker top retinopathy-api
```

## 🔍 Debugging Commands

### Debug Container Issues
```bash
# Check container health
docker inspect --format='{{.State.Health.Status}}' retinopathy-api

# View container filesystem changes
docker diff retinopathy-api

# Export container as tar
docker export retinopathy-api > retinopathy-backup.tar

# Copy files from container
docker cp retinopathy-api:/app/logs ./logs

# Copy files to container
docker cp ./config.py retinopathy-api:/app/
```

## 🌐 Network Commands

### Docker Network Management
```bash
# List networks
docker network ls

# Create network
docker network create retinopathy-network

# Connect container to network
docker network connect retinopathy-network retinopathy-api

# Inspect network
docker network inspect retinopathy-network
```

## 💾 Volume Commands

### Docker Volume Management
```bash
# List volumes
docker volume ls

# Create volume
docker volume create retinopathy-data

# Inspect volume
docker volume inspect retinopathy-data

# Remove volume
docker volume rm retinopathy-data
```

## 🚀 Quick Start Commands

### Development Setup
```bash
# Clone and setup
git clone <your-repo>
cd backend

# Create environment file
cp .env.example .env
# Edit .env with your values

# Build and run with Docker Compose
docker-compose up --build -d

# View logs
docker-compose logs -f

# Access API at http://localhost:5000
```

### Production Deployment
```bash
# Build production image
docker build -f Dockerfile.prod -t retinopathy-backend:prod .

# Run production container
docker run -d \
  --name retinopathy-api-prod \
  -p 5000:5000 \
  --env-file .env.production \
  --restart unless-stopped \
  retinopathy-backend:prod

# Or use docker-compose for production
docker-compose -f docker-compose.prod.yml up -d
```

## 🔐 Security Best Practices

### Secure Container Run
```bash
# Run with limited resources and non-root user
docker run -d \
  --name retinopathy-api \
  -p 5000:5000 \
  --memory="1g" \
  --cpus="0.5" \
  --read-only \
  --tmpfs /tmp \
  --user 1000:1000 \
  --env-file .env \
  retinopathy-backend:prod
```

## 📝 Environment Variables

### Required Environment Variables
```bash
# Create .env file with these variables:
MONGODB_URI=mongodb://localhost:27017/retinopathy
JWT_SECRET_KEY=your-super-secret-jwt-key
FLASK_ENV=development  # or production
```

## 🏥 Health Checks

### Check Application Health
```bash
# Check if API is responding
curl http://localhost:5000/

# Check container health status
docker inspect --format='{{.State.Health.Status}}' retinopathy-api

# Manual health check
docker exec retinopathy-api curl -f http://localhost:5000/ || echo "Health check failed"
```