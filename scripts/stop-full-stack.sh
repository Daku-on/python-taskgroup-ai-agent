#!/bin/bash

# Full Stack Stop Script
# 全スタック停止スクリプト

set -e

echo "🛑 Stopping AI Agent Full Stack..."
echo "=================================="

# Stop and remove containers
echo "🔄 Stopping services..."
docker-compose -f docker-compose.full.yml down

# Optional: Remove volumes (uncomment to reset data)
# echo "🗑️  Removing volumes..."
# docker-compose -f docker-compose.full.yml down -v

# Show status
echo ""
echo "✅ All services stopped!"
echo "========================"

# Clean up unused resources
read -p "🧹 Clean up unused Docker resources? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 Cleaning up..."
    docker system prune -f
    echo "✅ Cleanup completed!"
fi

echo ""
echo "💡 To start again: ./scripts/start-full-stack.sh"