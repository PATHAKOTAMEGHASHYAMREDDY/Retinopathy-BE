#!/bin/bash

# Docker Build and Run Script for Retinopathy Backend
# Usage: ./docker-build.sh [dev|prod] [build|run|stop|logs]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT=${1:-dev}
ACTION=${2:-build}
IMAGE_NAME="retinopathy-backend"
CONTAINER_NAME="retinopathy-api"

# Print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
check_env_file() {
    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating from template..."
        cat > .env << EOF
MONGODB_URI=mongodb://localhost:27017/retinopathy
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
FLASK_ENV=${ENVIRONMENT}
EOF
        print_warning "Please edit .env file with your actual values"
    fi
}

# Build Docker image
build_image() {
    print_status "Building Docker image for ${ENVIRONMENT} environment..."
    
    if [ "$ENVIRONMENT" = "prod" ]; then
        docker build -f Dockerfile.prod -t ${IMAGE_NAME}:${ENVIRONMENT} .
    else
        docker build -t ${IMAGE_NAME}:${ENVIRONMENT} .
    fi
    
    print_success "Docker image built successfully: ${IMAGE_NAME}:${ENVIRONMENT}"
}

# Run Docker container
run_container() {
    print_status "Running Docker container for ${ENVIRONMENT} environment..."
    
    # Stop existing container if running
    if docker ps -q -f name=${CONTAINER_NAME}-${ENVIRONMENT} | grep -q .; then
        print_warning "Stopping existing container..."
        docker stop ${CONTAINER_NAME}-${ENVIRONMENT}
        docker rm ${CONTAINER_NAME}-${ENVIRONMENT}
    fi
    
    # Run new container
    if [ "$ENVIRONMENT" = "prod" ]; then
        docker run -d \
            --name ${CONTAINER_NAME}-${ENVIRONMENT} \
            -p 5000:5000 \
            --env-file .env \
            --restart unless-stopped \
            ${IMAGE_NAME}:${ENVIRONMENT}
    else
        docker run -d \
            --name ${CONTAINER_NAME}-${ENVIRONMENT} \
            -p 5000:5000 \
            -v $(pwd):/app \
            --env-file .env \
            ${IMAGE_NAME}:${ENVIRONMENT}
    fi
    
    print_success "Container started: ${CONTAINER_NAME}-${ENVIRONMENT}"
    print_status "API available at: http://localhost:5000"
}

# Stop Docker container
stop_container() {
    print_status "Stopping Docker container..."
    
    if docker ps -q -f name=${CONTAINER_NAME}-${ENVIRONMENT} | grep -q .; then
        docker stop ${CONTAINER_NAME}-${ENVIRONMENT}
        docker rm ${CONTAINER_NAME}-${ENVIRONMENT}
        print_success "Container stopped and removed"
    else
        print_warning "No running container found"
    fi
}

# Show container logs
show_logs() {
    print_status "Showing logs for ${CONTAINER_NAME}-${ENVIRONMENT}..."
    
    if docker ps -q -f name=${CONTAINER_NAME}-${ENVIRONMENT} | grep -q .; then
        docker logs -f ${CONTAINER_NAME}-${ENVIRONMENT}
    else
        print_error "Container not running"
        exit 1
    fi
}

# Main script logic
main() {
    print_status "Retinopathy Backend Docker Script"
    print_status "Environment: ${ENVIRONMENT}"
    print_status "Action: ${ACTION}"
    
    check_env_file
    
    case $ACTION in
        build)
            build_image
            ;;
        run)
            build_image
            run_container
            ;;
        stop)
            stop_container
            ;;
        logs)
            show_logs
            ;;
        restart)
            stop_container
            build_image
            run_container
            ;;
        *)
            print_error "Unknown action: $ACTION"
            echo "Usage: $0 [dev|prod] [build|run|stop|logs|restart]"
            exit 1
            ;;
    esac
}

# Run main function
main