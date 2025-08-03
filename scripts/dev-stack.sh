#!/bin/bash

# Development Stack Script (Database only, local dev for API/Frontend)
# 開発スタックスクリプト（データベースのみ、API/フロントエンドはローカル開発）

set -e

echo "🛠️  Starting Development Stack..."
echo "================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your API keys before continuing."
fi

# Start only database and setup
echo "🗄️  Starting PostgreSQL database..."
docker-compose up -d postgres

# Wait for database
echo "⏳ Waiting for database to be ready..."
sleep 10

# Setup knowledge data
echo "📚 Setting up knowledge database..."
uv run python database/setup_knowledge.py

echo ""
echo "✅ Development database ready!"
echo "=============================="
echo "🗄️  Database: localhost:5432"
echo ""
echo "🚀 Next steps:"
echo "1. Start backend: python scripts/start_api.py"
echo "2. Start frontend: cd frontend && npm run dev"
echo ""
echo "📊 Frontend: http://localhost:5173"
echo "🔧 Backend: http://localhost:8000"
echo ""
echo "🛑 To stop database: docker-compose down"