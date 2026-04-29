#!/bin/bash

# Server management script

PID_FILE="server.pid"
LOG_FILE="server.log"

case "$1" in
    start)
        if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            echo "❌ Server is already running (PID: $(cat $PID_FILE))"
            exit 1
        fi
        
        echo "🚀 Starting Bybit P2P Automation Server..."
        nohup uv run python main.py > "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        sleep 3
        
        if kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            echo "✅ Server started successfully!"
            echo "   PID: $(cat $PID_FILE)"
            echo "   URL: http://127.0.0.1:8000"
            echo "   Log: tail -f $LOG_FILE"
        else
            echo "❌ Failed to start server. Check $LOG_FILE"
            rm -f "$PID_FILE"
            exit 1
        fi
        ;;
        
    stop)
        if [ ! -f "$PID_FILE" ]; then
            echo "❌ Server is not running (no PID file)"
            exit 1
        fi
        
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "🛑 Stopping server (PID: $PID)..."
            kill "$PID"
            sleep 2
            
            if kill -0 "$PID" 2>/dev/null; then
                echo "⚠️  Force killing..."
                kill -9 "$PID"
            fi
            
            rm -f "$PID_FILE"
            echo "✅ Server stopped"
        else
            echo "❌ Server is not running (stale PID file)"
            rm -f "$PID_FILE"
        fi
        ;;
        
    restart)
        bash "$0" stop
        sleep 2
        bash "$0" start
        ;;
        
    status)
        if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            echo "✅ Server is running"
            echo "   PID: $(cat $PID_FILE)"
            echo "   URL: http://127.0.0.1:8000"
            echo ""
            echo "Recent logs:"
            tail -5 "$LOG_FILE"
        else
            echo "❌ Server is not running"
            [ -f "$PID_FILE" ] && rm -f "$PID_FILE"
        fi
        ;;
        
    logs)
        if [ ! -f "$LOG_FILE" ]; then
            echo "❌ No log file found"
            exit 1
        fi
        tail -f "$LOG_FILE"
        ;;
        
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the server"
        echo "  stop    - Stop the server"
        echo "  restart - Restart the server"
        echo "  status  - Check server status"
        echo "  logs    - Follow server logs"
        exit 1
        ;;
esac
