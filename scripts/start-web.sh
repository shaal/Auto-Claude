#!/usr/bin/env bash
#
# Start Auto Claude Web Dashboard
#
# Usage:
#   ./scripts/start-web.sh --project-dir /path/to/repo
#   ./scripts/start-web.sh --port 8080
#   ./scripts/start-web.sh  # uses current directory as project
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/apps/backend"
FRONTEND_DIR="$ROOT_DIR/apps/frontend"

# Defaults
PROJECT_DIR=""
HOST="0.0.0.0"
PORT=8080
BUILD_FRONTEND=true
SKIP_PROXY=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --project-dir)
            PROJECT_DIR="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --no-build)
            BUILD_FRONTEND=false
            shift
            ;;
        --skip-proxy)
            SKIP_PROXY=true
            shift
            ;;
        -h|--help)
            echo "Auto Claude Web Dashboard"
            echo ""
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --project-dir DIR   Project directory to manage (default: current dir)"
            echo "  --host HOST         Host to bind to (default: 0.0.0.0)"
            echo "  --port PORT         Port to listen on (default: 8080)"
            echo "  --no-build          Skip frontend build (use existing dist-web/)"
            echo "  --skip-proxy        Don't start CLIProxyAPI"
            echo "  -h, --help          Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Use current directory if no project dir specified
if [ -z "$PROJECT_DIR" ]; then
    PROJECT_DIR="$(pwd)"
fi

echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║   Auto Claude — Web Dashboard        ║"
echo "  ╚══════════════════════════════════════╝"
echo ""
echo "  Project: $PROJECT_DIR"
echo "  URL:     http://$HOST:$PORT"
echo ""

# Step 1: Check for CLIProxyAPI
if [ "$SKIP_PROXY" = false ]; then
    if command -v cliproxyapi &>/dev/null; then
        if curl -s http://localhost:8317/health &>/dev/null; then
            echo "  [OK] CLIProxyAPI already running on :8317"
        else
            echo "  [..] Starting CLIProxyAPI..."
            cliproxyapi &
            PROXY_PID=$!
            sleep 2
            if curl -s http://localhost:8317/health &>/dev/null; then
                echo "  [OK] CLIProxyAPI started (PID: $PROXY_PID)"
            else
                echo "  [!!] CLIProxyAPI failed to start (continuing without it)"
            fi
        fi
    else
        echo "  [--] CLIProxyAPI not found (skipping — agents will use direct API)"
    fi
fi

# Step 2: Build web frontend if needed
DIST_WEB="$FRONTEND_DIR/dist-web"
if [ "$BUILD_FRONTEND" = true ] && [ ! -d "$DIST_WEB" ]; then
    echo "  [..] Building web frontend..."
    cd "$FRONTEND_DIR"
    npm run build:web
    echo "  [OK] Frontend built at $DIST_WEB"
elif [ -d "$DIST_WEB" ]; then
    echo "  [OK] Using existing frontend build at $DIST_WEB"
else
    echo "  [--] No frontend build found (API-only mode)"
fi

# Step 3: Find Python
if [ -f "$BACKEND_DIR/.venv/bin/python" ]; then
    PYTHON="$BACKEND_DIR/.venv/bin/python"
elif command -v python3 &>/dev/null; then
    PYTHON="python3"
elif command -v python &>/dev/null; then
    PYTHON="python"
else
    echo "  [!!] Python not found. Please install Python 3.12+"
    exit 1
fi

echo "  [OK] Using Python: $PYTHON"
echo ""

# Step 4: Start FastAPI
cd "$BACKEND_DIR"
exec "$PYTHON" -m web.run_web \
    --project-dir "$PROJECT_DIR" \
    --host "$HOST" \
    --port "$PORT" \
    --static-dir "$DIST_WEB"
