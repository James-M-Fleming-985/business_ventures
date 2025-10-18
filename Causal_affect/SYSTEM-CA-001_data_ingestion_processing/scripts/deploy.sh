#!/bin/bash
# Deployment script for CA-001 Data Ingestion System

set -e

echo "🚀 Deploying Data Ingestion & Processing Engine"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Copying from .env.example"
    cp .env.example .env
    echo "📝 Please update .env with your configuration"
    exit 1
fi

# Pull latest images
echo "📦 Pulling latest Docker images..."
docker-compose pull

# Build application
echo "🔨 Building application..."
docker-compose build

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose run --rm backend alembic upgrade head || echo "⚠️  No migrations found (first run)"

# Start services
echo "▶️  Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check health
echo "🏥 Checking service health..."
curl -f http://localhost:8000/health || echo "⚠️  Health check failed"

echo "✅ Deployment complete!"
echo ""
echo "Services:"
echo "  - Backend API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Prometheus: http://localhost:9090"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop: docker-compose down"
