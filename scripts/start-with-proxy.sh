#!/bin/bash

###############################################################################
# Auto Claude - Start with CLIProxyAPI
###############################################################################
#
# Starts CLIProxyAPI in the background, waits for it to be ready,
# then launches Auto-Claude. Cleans up the proxy on exit.
#
# Usage:
#   ./scripts/start-with-proxy.sh                    # interactive spec creation
#   ./scripts/start-with-proxy.sh --spec 001         # run existing spec
#   ./scripts/start-with-proxy.sh --task "Add X"     # create spec from task
#
# Any arguments are passed directly to the spec_runner or run.py.
#
###############################################################################

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_DIR/apps/backend"
VENV_PYTHON="$BACKEND_DIR/.venv/bin/python"
CLIPROXYAPI="${CLIPROXYAPI_BIN:-$HOME/.local/bin/cliproxyapi}"
PROXY_CONFIG="${CLIPROXYAPI_CONFIG:-$HOME/.cli-proxy-api/config.yaml}"
PROXY_PORT=8317
PROXY_PID=""

# --- Cleanup on exit ---
cleanup() {
    if [ -n "$PROXY_PID" ] && kill -0 "$PROXY_PID" 2>/dev/null; then
        echo ""
        echo -e "${YELLOW}Stopping CLIProxyAPI (PID $PROXY_PID)...${NC}"
        kill "$PROXY_PID" 2>/dev/null || true
        wait "$PROXY_PID" 2>/dev/null || true
        echo -e "${GREEN}CLIProxyAPI stopped.${NC}"
    fi
}
trap cleanup EXIT INT TERM

# --- Preflight checks ---
echo -e "${BLUE}Auto Claude — Start with CLIProxyAPI${NC}"
echo ""

# Check cliproxyapi binary
if [ ! -x "$CLIPROXYAPI" ]; then
    echo -e "${RED}ERROR: cliproxyapi not found at $CLIPROXYAPI${NC}"
    echo "Install it or set CLIPROXYAPI_BIN to the correct path."
    exit 1
fi

# Check config
if [ ! -f "$PROXY_CONFIG" ]; then
    echo -e "${RED}ERROR: Config not found at $PROXY_CONFIG${NC}"
    echo "Create it or set CLIPROXYAPI_CONFIG to the correct path."
    exit 1
fi

# Check venv
if [ ! -x "$VENV_PYTHON" ]; then
    echo -e "${RED}ERROR: Python venv not found at $VENV_PYTHON${NC}"
    echo "Run: python3 -m venv $BACKEND_DIR/.venv && $BACKEND_DIR/.venv/bin/pip install -r $BACKEND_DIR/requirements.txt"
    exit 1
fi

# Check .env
if [ ! -f "$BACKEND_DIR/.env" ]; then
    echo -e "${RED}ERROR: $BACKEND_DIR/.env not found${NC}"
    echo "See guides/CLIPROXYAPI-SETUP.md for configuration."
    exit 1
fi

# --- Check if proxy is already running ---
if curl -s -o /dev/null -w "" http://localhost:$PROXY_PORT/ 2>/dev/null; then
    echo -e "${GREEN}CLIProxyAPI already running on port $PROXY_PORT.${NC}"
else
    # Start CLIProxyAPI
    echo -e "${YELLOW}Starting CLIProxyAPI on port $PROXY_PORT...${NC}"
    "$CLIPROXYAPI" --config "$PROXY_CONFIG" &
    PROXY_PID=$!

    # Wait for proxy to be ready (up to 10 seconds)
    for i in $(seq 1 20); do
        if curl -s -o /dev/null -w "" http://localhost:$PROXY_PORT/ 2>/dev/null; then
            echo -e "${GREEN}CLIProxyAPI ready. (PID $PROXY_PID)${NC}"
            break
        fi
        if ! kill -0 "$PROXY_PID" 2>/dev/null; then
            echo -e "${RED}ERROR: CLIProxyAPI exited unexpectedly.${NC}"
            exit 1
        fi
        sleep 0.5
    done

    # Final check
    if ! curl -s -o /dev/null -w "" http://localhost:$PROXY_PORT/ 2>/dev/null; then
        echo -e "${RED}ERROR: CLIProxyAPI did not start within 10 seconds.${NC}"
        exit 1
    fi
fi

echo ""

# --- Determine which command to run ---
if [ $# -eq 0 ]; then
    # No args — interactive spec creation
    echo -e "${BLUE}Launching interactive spec creation...${NC}"
    echo ""
    "$VENV_PYTHON" "$BACKEND_DIR/runners/spec_runner.py" --interactive
elif [[ "$1" == "--spec" ]]; then
    # Run existing spec
    echo -e "${BLUE}Running spec...${NC}"
    echo ""
    "$VENV_PYTHON" "$BACKEND_DIR/run.py" "$@"
else
    # Pass everything to spec_runner (--task, --complexity, etc.)
    echo -e "${BLUE}Launching spec runner...${NC}"
    echo ""
    "$VENV_PYTHON" "$BACKEND_DIR/runners/spec_runner.py" "$@"
fi
