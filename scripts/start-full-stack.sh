#!/bin/bash

# Full Stack Startup Script
# 全スタック起動スクリプト

set -e

echo "🚀 Starting AI Agent Full Stack..."
echo "=================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your API keys before continuing."
    echo "    Required: OPENAI_API_KEY"
    read -p "Press Enter to continue after editing .env..."
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Build and start services
echo "🔨 Building and starting services..."
docker-compose -f docker-compose.full.yml down --remove-orphans
docker-compose -f docker-compose.full.yml build --no-cache
docker-compose -f docker-compose.full.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to start..."
echo "   - Database: postgres:5432"
echo "   - Backend API: http://localhost:8000"
echo "   - Frontend: http://localhost:3000"

# Wait for backend health check
echo "🔍 Checking backend health..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is healthy!"
        break
    fi
    
    if [ $attempt -eq $max_attempts ]; then
        echo "❌ Backend failed to start after $max_attempts attempts"
        echo "📋 Checking logs..."
        docker-compose -f docker-compose.full.yml logs backend
        exit 1
    fi
    
    echo "   Attempt $attempt/$max_attempts - waiting..."
    sleep 5
    ((attempt++))
done

# Setup database with knowledge data
echo "📚 Setting up knowledge database..."
docker-compose -f docker-compose.full.yml run --rm db-setup

# Show service status
echo ""
echo "🎉 All services are running!"
echo "=============================="
echo "📊 Frontend Dashboard: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo "🗄️  Database: localhost:5432"
echo ""
echo "🔍 Service Status:"
docker-compose -f docker-compose.full.yml ps

echo ""
echo "📋 Quick Commands:"
echo "  - View logs: docker-compose -f docker-compose.full.yml logs"
echo "  - Stop all: docker-compose -f docker-compose.full.yml down"
echo "  - Restart: docker-compose -f docker-compose.full.yml restart"
echo ""
echo "🎯 Ready to use! Open http://localhost:3000 in your browser"