#!/bin/bash

# Quick start script for Bybit P2P Automation

echo "🤖 Bybit P2P Automation - Quick Start"
echo "======================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "✏️  Please edit .env file and add your credentials:"
    echo "   - BYBIT_API_KEY"
    echo "   - BYBIT_API_SECRET"
    echo "   - TELEGRAM_BOT_TOKEN"
    echo "   - OPENAI_API_KEY (for voice/image features)"
    echo ""
    echo "Get testnet keys from: https://testnet.bybit.com"
    echo ""
    read -p "Press Enter after you've configured .env file..."
fi

# Determine mode
MODE="${1:-server}"

case "$MODE" in
    server)
        echo "Starting FastAPI server..."
        ;;
    bot)
        echo "Starting Telegram bot..."
        ;;
    docker)
        echo "Starting with Docker Compose..."
        docker-compose up -d
        echo ""
        echo "✅ Services started!"
        echo "   App: http://127.0.0.1:8000"
        echo "   Logs: docker-compose logs -f"
        exit 0
        ;;
    *)
        echo "Usage: $0 {server|bot|docker}"
        echo ""
        echo "Commands:"
        echo "  server  - Start FastAPI web server (default)"
        echo "  bot     - Start Telegram bot only"
        echo "  docker  - Start all services with Docker Compose"
        exit 1
        ;;
esac

# Check if uv is installed
if command -v uv &> /dev/null; then
    echo "✓ uv found"
    echo ""
    
    if [ "$MODE" = "bot" ]; then
        echo "🚀 Starting Telegram bot with uv..."
        uv run python main_bot.py
    else
        echo "🚀 Starting server with uv..."
        uv run python main.py
    fi
else
    echo "⚠️  uv not found. Using standard Python..."
    echo ""
    
    if [ ! -d .venv ]; then
        echo "Creating virtual environment..."
        python3 -m venv .venv
    fi
    
    echo "Activating virtual environment..."
    source .venv/bin/activate
    
    echo "Installing dependencies..."
    pip install -e .
    
    echo ""
    if [ "$MODE" = "bot" ]; then
        echo "🚀 Starting Telegram bot..."
        python main_bot.py
    else
        echo "🚀 Starting server..."
        python main.py
    fi
fi
