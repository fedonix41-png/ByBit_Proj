#!/bin/bash

set -e

echo "🚀 P2P Automation Setup"
echo "======================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your API keys before continuing"
    exit 1
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker found"

# Create directories
echo "📁 Creating directories..."
mkdir -p data/photos data/checkpoints logs

# Start services
echo "🐳 Starting Docker containers..."
docker-compose up -d postgres

echo "⏳ Waiting for PostgreSQL..."
sleep 5

# Run migrations
echo "🔄 Running database migrations..."
docker-compose run --rm app alembic upgrade head

# Start all services
echo "🚀 Starting all services..."
docker-compose up -d

echo ""
echo "✅ Setup complete!"
echo ""
echo "Services:"
echo "  - Web UI: http://localhost:8000"
echo "  - PostgreSQL: localhost:5432"
echo "  - Telegram Bot: running"
echo ""
echo "Commands:"
echo "  - View logs: docker-compose logs -f"
echo "  - Stop: docker-compose down"
echo "  - Restart: docker-compose restart"
echo ""
