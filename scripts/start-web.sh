#!/usr/bin/env bash
#
# Auto Claude — Web Dashboard Launcher
#
# Starts all services in a tmux session with separate panes:
#   - CLIProxyAPI   (top-left)      :8317
#   - FastAPI       (top-right)     :8080
#   - Vite dev      (bottom)        :3000  (--dev mode only)
#
# Usage:
#   ./scripts/start-web.sh                          # production mode (serves built SPA)
#   ./scripts/start-web.sh --dev                    # dev mode (Vite hot-reload on :3000)
#   ./scripts/start-web.sh --project-dir /path/to/repo
#   ./scripts/start-web.sh --port 9000 --dev
#   ./scripts/start-web.sh --skip-proxy             # don't start CLIProxyAPI
#   ./scripts/start-web.sh --stop                   # stop all services
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/apps/backend"
FRONTEND_DIR="$ROOT_DIR/apps/frontend"
SESSION_NAME="auto-claude-web"

# Defaults
PROJECT_DIR=""
HOST="0.0.0.0"
PORT=8080
DEV_MODE=false
SKIP_PROXY=false
NO_BUILD=false

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

print_header() {
    echo ""
    echo -e "  ${BOLD}╔══════════════════════════════════════════╗${NC}"
    echo -e "  ${BOLD}║   Auto Claude — Web Dashboard            ║${NC}"
    echo -e "  ${BOLD}╚══════════════════════════════════════════╝${NC}"
    echo ""
}

print_ok()   { echo -e "  ${GREEN}[OK]${NC} $1"; }
print_wait() { echo -e "  ${YELLOW}[..]${NC} $1"; }
print_err()  { echo -e "  ${RED}[!!]${NC} $1"; }
print_skip() { echo -e "  ${CYAN}[--]${NC} $1"; }

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --project-dir)  PROJECT_DIR="$2"; shift 2 ;;
        --host)         HOST="$2"; shift 2 ;;
        --port)         PORT="$2"; shift 2 ;;
        --dev)          DEV_MODE=true; shift ;;
        --skip-proxy)   SKIP_PROXY=true; shift ;;
        --no-build)     NO_BUILD=true; shift ;;
        --stop)
            if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
                tmux kill-session -t "$SESSION_NAME"
                echo "Stopped $SESSION_NAME"
            else
                echo "No running session found"
            fi
            exit 0
            ;;
        -h|--help)
            echo "Auto Claude — Web Dashboard"
            echo ""
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --dev               Dev mode: Vite hot-reload on :3000 + API on :$PORT"
            echo "  --project-dir DIR   Project directory to manage (default: current dir)"
            echo "  --host HOST         Host to bind to (default: 0.0.0.0)"
            echo "  --port PORT         FastAPI port (default: 8080)"
            echo "  --skip-proxy        Don't start CLIProxyAPI"
            echo "  --no-build          Skip frontend build"
            echo "  --stop              Stop all running services"
            echo "  -h, --help          Show this help"
            echo ""
            echo "Modes:"
            echo "  Production:  Serves built SPA from FastAPI on :$PORT"
            echo "  Dev (--dev): Vite on :3000 (hot-reload) proxying to FastAPI on :$PORT"
            echo ""
            echo "Tmux controls:"
            echo "  Ctrl+B then D       Detach (services keep running)"
            echo "  tmux attach -t $SESSION_NAME   Re-attach"
            echo "  $0 --stop           Stop all services"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"; exit 1
            ;;
    esac
done

# Use current directory if no project dir specified
if [ -z "$PROJECT_DIR" ]; then
    PROJECT_DIR="$(pwd)"
fi
PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd)"

# Check tmux
if ! command -v tmux &>/dev/null; then
    echo "Error: tmux is required. Install with: sudo apt install tmux"
    exit 1
fi

# Kill existing session if any
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    print_wait "Stopping existing session..."
    tmux kill-session -t "$SESSION_NAME"
    sleep 1
fi

print_header
echo -e "  ${BOLD}Project:${NC}  $PROJECT_DIR"
if [ "$DEV_MODE" = true ]; then
    echo -e "  ${BOLD}Mode:${NC}     Development (Vite :3000 → FastAPI :$PORT)"
else
    echo -e "  ${BOLD}Mode:${NC}     Production (FastAPI :$PORT serves SPA)"
fi
echo ""

# ── Find Python ──────────────────────────────────────────────
if [ -f "$BACKEND_DIR/.venv/bin/python" ]; then
    PYTHON="$BACKEND_DIR/.venv/bin/python"
elif command -v python3 &>/dev/null; then
    PYTHON="python3"
else
    print_err "Python not found. Install Python 3.12+ or run: cd apps/backend && uv venv && uv pip install -r requirements.txt"
    exit 1
fi
print_ok "Python: $PYTHON"

# ── Check/install FastAPI ────────────────────────────────────
if ! "$PYTHON" -c "import fastapi" 2>/dev/null; then
    print_wait "Installing FastAPI..."
    "$PYTHON" -m pip install fastapi "uvicorn[standard]" -q
    print_ok "FastAPI installed"
else
    print_ok "FastAPI available"
fi

# ── Build frontend if needed (production mode) ──────────────
DIST_WEB="$FRONTEND_DIR/dist-web"
if [ "$DEV_MODE" = false ] && [ "$NO_BUILD" = false ]; then
    if [ ! -d "$DIST_WEB" ]; then
        print_wait "Building web frontend (first time)..."
        (cd "$FRONTEND_DIR" && npm run build:web) 2>&1 | tail -3
        print_ok "Frontend built"
    else
        print_ok "Frontend build exists"
    fi
fi

# ── Check CLIProxyAPI ────────────────────────────────────────
PROXY_RUNNING=false
if [ "$SKIP_PROXY" = false ]; then
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8317/v1/models 2>/dev/null | grep -q "200"; then
        print_ok "CLIProxyAPI already running on :8317"
        PROXY_RUNNING=true
    elif command -v cliproxyapi &>/dev/null; then
        print_wait "Will start CLIProxyAPI in tmux"
    else
        print_skip "CLIProxyAPI not installed (agents will need direct API keys)"
    fi
else
    print_skip "CLIProxyAPI skipped (--skip-proxy)"
fi

# ── Build tmux session ───────────────────────────────────────
echo ""
print_wait "Starting tmux session: ${BOLD}$SESSION_NAME${NC}"

# Create session with first pane (CLIProxyAPI or placeholder)
if [ "$SKIP_PROXY" = false ] && [ "$PROXY_RUNNING" = false ] && command -v cliproxyapi &>/dev/null; then
    PROXY_CMD="echo '── CLIProxyAPI (:8317) ──' && cliproxyapi --config ~/.cli-proxy-api/config.yaml 2>&1 || echo 'CLIProxyAPI exited'"
else
    PROXY_CMD="echo '── CLIProxyAPI ──' && echo 'Already running or skipped' && echo '' && echo 'Press Ctrl+C then type a command, or Ctrl+B D to detach' && cat"
fi

tmux new-session -d -s "$SESSION_NAME" -x 200 -y 50 "$PROXY_CMD"

# Split right: FastAPI backend
STATIC_ARG=""
if [ "$DEV_MODE" = false ] && [ -d "$DIST_WEB" ]; then
    STATIC_ARG="--static-dir $DIST_WEB"
fi

FASTAPI_CMD="echo '── FastAPI Backend (:$PORT) ──' && cd $BACKEND_DIR && $PYTHON -m web.run_web --project-dir '$PROJECT_DIR' --host $HOST --port $PORT $STATIC_ARG 2>&1 || echo 'FastAPI exited'"
tmux split-window -h -t "$SESSION_NAME" "$FASTAPI_CMD"

# Split bottom: Vite dev server (dev mode) or status panel (production)
if [ "$DEV_MODE" = true ]; then
    VITE_CMD="echo '── Vite Dev Server (:3000) ──' && cd $FRONTEND_DIR && npx vite --config vite.web.config.ts --host 0.0.0.0 2>&1 || echo 'Vite exited'"
    tmux split-window -v -t "$SESSION_NAME" "$VITE_CMD"
else
    STATUS_CMD="echo '── Auto Claude Web Dashboard ──' && echo '' && sleep 3 && echo 'Dashboard URL: http://$HOST:$PORT' && echo '' && echo 'Endpoints:' && echo '  API:       http://localhost:$PORT/api/health' && echo '  Specs:     http://localhost:$PORT/api/specs' && echo '  WebSocket: ws://localhost:$PORT/ws/events' && echo '' && echo 'Controls:' && echo '  Ctrl+B D     Detach (services keep running)' && echo '  Ctrl+B [     Scroll mode (q to exit)' && echo '  $0 --stop    Stop all' && echo '' && echo 'Waiting for services...' && sleep 2 && curl -s http://localhost:$PORT/api/health && echo '' && echo '' && echo 'Ready!' && cat"
    tmux split-window -v -t "$SESSION_NAME" "$STATUS_CMD"
fi

# Set pane titles and layout
tmux select-layout -t "$SESSION_NAME" main-horizontal

# Select the status/vite pane
tmux select-pane -t "$SESSION_NAME:0.2"

echo ""
print_ok "All services launching in tmux"
echo ""
if [ "$DEV_MODE" = true ]; then
    echo -e "  ${BOLD}Open:${NC}  ${CYAN}http://localhost:3000${NC}  (Vite dev, hot-reload)"
    echo -e "  ${BOLD}API:${NC}   http://localhost:$PORT/api/health"
else
    echo -e "  ${BOLD}Open:${NC}  ${CYAN}http://$HOST:$PORT${NC}"
fi
echo ""
echo -e "  ${BOLD}Tmux:${NC}  Ctrl+B D to detach  |  tmux attach -t $SESSION_NAME"
echo -e "  ${BOLD}Stop:${NC}  $0 --stop"
echo ""

# Attach to session
exec tmux attach -t "$SESSION_NAME"
