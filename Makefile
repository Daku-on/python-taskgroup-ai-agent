# AI Agent System Makefile
# 簡単な起動・停止コマンド

.PHONY: help install dev full stop clean

# Default target
help:
	@echo "🤖 AI Agent System Commands"
	@echo "============================="
	@echo "📦 install     - Install all dependencies"
	@echo "🛠️  dev         - Start development environment (database only)"
	@echo "🚀 full        - Start full stack with Docker"
	@echo "🛑 stop        - Stop all services"
	@echo "🧹 clean       - Clean up Docker resources"
	@echo ""
	@echo "📊 URLs:"
	@echo "  Frontend: http://localhost:3000 (full) / http://localhost:5173 (dev)"
	@echo "  Backend:  http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"

# Install dependencies
install:
	@echo "📦 Installing dependencies..."
	@echo "Backend (Python):"
	uv sync
	@echo "Frontend (Node.js):"
	cd frontend && npm install
	@echo "✅ Dependencies installed!"

# Development environment (database + manual start)
dev:
	@echo "🛠️  Starting development environment..."
	./scripts/dev-stack.sh

# Full stack with Docker
full:
	@echo "🚀 Starting full stack..."
	./scripts/start-full-stack.sh

# Stop all services
stop:
	@echo "🛑 Stopping services..."
	./scripts/stop-full-stack.sh

# Clean up Docker resources
clean:
	@echo "🧹 Cleaning up..."
	docker system prune -f
	docker volume prune -f

# Backend only (for development)
backend:
	@echo "🔧 Starting backend API server..."
	uv run python scripts/start_api.py

# Frontend only (for development)
frontend:
	@echo "📊 Starting frontend development server..."
	cd frontend && npm run dev

# Database setup
db-setup:
	@echo "📚 Setting up knowledge database..."
	uv run python database/setup_knowledge.py

# Run tests
test:
	@echo "🧪 Running tests..."
	uv run pytest tests/ -v

# Code quality checks
lint:
	@echo "🔍 Running code quality checks..."
	uv run ruff check .
	uv run mypy src/

# Format code
format:
	@echo "✨ Formatting code..."
	uv run ruff format .

# Build frontend for production
build:
	@echo "🏗️  Building frontend for production..."
	cd frontend && npm run build