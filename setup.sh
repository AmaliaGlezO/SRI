#!/bin/bash

set -e

echo "======================================"
echo "SRI Application - Docker Setup Script"
echo "======================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker Desktop."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Create required directories
echo "📁 Creating required directories..."
mkdir -p data logs models indexes coverage
echo "✅ Directories created"
echo ""

# Build images
echo "🏗️  Building Docker images..."
docker-compose build --no-cache
echo "✅ Images built successfully"
echo ""

# Start services
echo "🚀 Starting services..."
docker-compose up -d
echo "✅ Services started"
echo ""

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ API is ready"
        break
    fi
    attempt=$((attempt + 1))
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "⚠️  API took longer than expected to start"
fi

echo ""
echo "======================================"
echo "✅ Setup Complete!"
echo "======================================"
echo ""
echo "📍 Service URLs:"
echo "   API: http://localhost:8000"
echo "   Swagger Docs: http://localhost:8000/docs"
echo "   Chroma: http://localhost:8001"
echo ""
echo "📚 Useful commands:"
echo "   View logs:      make logs"
echo "   Run tests:      make test"
echo "   Stop services:  make down"
echo "   Help:           make help"
echo ""
echo "🎯 Next steps:"
echo "   1. Open http://localhost:8000/docs in your browser"
echo "   2. Try the /query endpoint"
echo "   3. Run tests with: make test"
echo ""
