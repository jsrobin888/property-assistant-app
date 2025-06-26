#!/bin/bash

# Quick start script for Property Management API
echo "🏠 Starting Property Management API..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create necessary directories
echo -e "${BLUE}Creating directories...${NC}"
echo ":: mkdir -p data logs"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from example...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}Please edit .env file with your configuration${NC}"
fi

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo -e "${YELLOW}Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Build and start the service
echo -e "${BLUE}Building and starting the API service...${NC}"
echo "::docker-compose up --build"

echo -e "${GREEN}API should be available at:${NC}"
echo "🌐 API Documentation: http://localhost:8000/docs"
echo "🌐 API Health Check: http://localhost:8000/health"
echo "🌐 Alternative Docs: http://localhost:8000/redoc"


#!/bin/bash
# Fast build and run commands for Property Management API

# Enable BuildKit for faster builds
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

echo "🚀 Building with optimizations..."

# Fast build options:

# 1. FASTEST: Development build (uses mounted volumes, no rebuild needed)
echo "Option 1: Development mode (fastest)"
echo "docker-compose up"

# 2. OPTIMIZED: Build with parallel processing and cache
echo "Option 2: Optimized build"
echo "docker-compose build --parallel --compress && docker-compose up"

# 3. CLEAN: Fresh build (if having issues)
echo "Option 3: Clean build"
echo "docker-compose build --no-cache --parallel && docker-compose up"

# 4. BACKGROUND: Run in background
echo "Option 4: Background mode"
echo "docker-compose up -d"

# Monitoring commands:
echo ""
echo "📊 Monitoring commands:"
echo "docker stats property-management-api  # Resource usage"
echo "docker logs -f property-management-api  # Live logs"
echo "docker-compose ps  # Service status"

# Quick aliases you can add to your shell profile:
echo ""
echo "💡 Add these aliases to ~/.bashrc or ~/.zshrc for faster commands:"
echo "alias dcup='docker-compose up'"
echo "alias dcbuild='DOCKER_BUILDKIT=1 docker-compose build --parallel'"
echo "alias dcfast='DOCKER_BUILDKIT=1 docker-compose up --build'"
echo "alias dclogs='docker logs -f property-management-api'"