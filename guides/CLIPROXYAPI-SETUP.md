# CLIProxyAPI Setup Guide

This guide explains how to configure Auto-Claude to use CLIProxyAPI as your API proxy, eliminating the need for direct Anthropic API keys.

## Overview

CLIProxyAPI acts as a middleware between Auto-Claude and the Anthropic API. Your API credentials are stored in the proxy, and Auto-Claude simply forwards requests through it.

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Auto-Claude    │────▶│   CLIProxyAPI    │────▶│  Anthropic API  │
│ (Claude SDK)    │     │ localhost:8317   │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
     Uses:                    Handles:               Uses:
  ANTHROPIC_AUTH_TOKEN      Your own auth        Your proxy's keys
  ANTHROPIC_BASE_URL       (stored in proxy)
```

## Two Configuration Options

### Option A: Use CLIProxyAPI (Full proxy setup)
- Requires CLIProxyAPI running on port 8317
- All API keys managed by the proxy
- See [Configuration with CLIProxyAPI](#option-a-configuration-with-cliproxyapi) below

### Option B: Use Claude Code OAuth Token Directly (No proxy needed)
- Uses your existing Claude Code authentication
- No additional software required
- See [Configuration without Proxy](#option-b-configuration-without-proxy) below

## Prerequisites

- Python 3.12+ installed
- Auto-Claude dependencies installed (`npm run install:all` or `uv pip install -r requirements.txt`)
- **For Option A:** CLIProxyAPI installed and running
- **For Option B:** Claude Code CLI authenticated (`claude login` or token in keychain)

---

## Installing CLIProxyAPI

### macOS (Homebrew)
```bash
brew tap router-for-me/tap
brew install cliproxyapi
```

### Windows (winget)
```bash
winget install -e --id LuisPater.CLIProxyAPI
```

### Linux (Build from source)
```bash
# Requires Go 1.22+
git clone https://github.com/router-for-me/CLIProxyAPI.git /tmp/CLIProxyAPI
cd /tmp/CLIProxyAPI
go build -o cliproxyapi ./cmd/server

# Install to PATH
mkdir -p ~/.local/bin
cp cliproxyapi ~/.local/bin/
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```

### Initial Setup (Login)

After installing, authenticate with your Claude Code account:

```bash
cliproxyapi --claude-login
```

This opens a browser for OAuth login. Tokens are saved to `~/.cli-proxy-api/`.

### Create Config File

Create `~/.cli-proxy-api/config.yaml`:

```yaml
# CLIProxyAPI Configuration for Auto-Claude
host: "127.0.0.1"  # localhost only for security
port: 8317

# Authentication directory
auth-dir: "~/.cli-proxy-api"

# API keys for client authentication
api-keys:
  - "cliproxyapi"

# Settings
debug: false
request-retry: 3
```

---

## Option A: Configuration with CLIProxyAPI

### Step 1: Configure Environment Variables

Edit `apps/backend/.env` with the following settings:

```bash
# =============================================================================
# CUSTOM API ENDPOINT - Using CLIProxyAPI
# =============================================================================

# Point to your CLIProxyAPI instance
ANTHROPIC_BASE_URL=http://localhost:8317

# Bypass proxy for localhost connections
NO_PROXY=127.0.0.1,localhost

# Disable telemetry and cost warnings (proxy handles billing)
DISABLE_TELEMETRY=true
DISABLE_COST_WARNINGS=true

# Extended timeout for long-running requests (10 minutes)
API_TIMEOUT_MS=600000

# Authentication token for CLIProxyAPI
# Set this to your proxy's auth token, or use a placeholder if no auth required
ANTHROPIC_AUTH_TOKEN=cliproxyapi

# =============================================================================
# GRAPHITI MEMORY (Optional - disable if you don't have embedding API keys)
# =============================================================================
GRAPHITI_ENABLED=false
```

### Step 2: Start CLIProxyAPI

**CRITICAL: CLIProxyAPI must be running before you start Auto-Claude!**

In a separate terminal, start your CLIProxyAPI server:

```bash
# Start CLIProxyAPI (adjust based on your setup)
cliproxyapi --port 8317
```

Verify it's running:
```bash
curl http://localhost:8317/anthropic
# Should return a response (not "Connection refused")
```

### Step 3: Verify Configuration

```bash
cd apps/backend
source .venv/bin/activate

# Load .env and check authentication
python -c "
from dotenv import load_dotenv
load_dotenv()
from core.auth import get_auth_token, get_sdk_env_vars
print('Auth Token:', get_auth_token())
print('SDK Environment:', get_sdk_env_vars())
"
```

Expected output:
```
Auth Token: cliproxyapi
SDK Environment: {'ANTHROPIC_BASE_URL': 'http://localhost:8317/anthropic', 'ANTHROPIC_AUTH_TOKEN': 'cliproxyapi', 'NO_PROXY': '127.0.0.1,localhost', 'DISABLE_TELEMETRY': 'true', 'DISABLE_COST_WARNINGS': 'true', 'API_TIMEOUT_MS': '600000'}
```

---

## Option B: Configuration without Proxy

If you don't have CLIProxyAPI, you can use Claude Code's OAuth token directly.

### Step 1: Ensure Claude Code is Authenticated

```bash
# Check if you have a valid token
claude --version

# If not authenticated, run:
claude login
# or
claude setup-token
```

### Step 2: Configure Environment Variables

Edit `apps/backend/.env`:

```bash
# =============================================================================
# DIRECT AUTHENTICATION (No proxy)
# =============================================================================
# Leave ANTHROPIC_BASE_URL unset to use default Anthropic API
# The system will use your Claude Code OAuth token from system keychain

# Disable telemetry (optional)
DISABLE_TELEMETRY=true

# =============================================================================
# GRAPHITI MEMORY (Optional)
# =============================================================================
GRAPHITI_ENABLED=false

# =============================================================================
# UI SETTINGS
# =============================================================================
ENABLE_FANCY_UI=true
```

### Step 3: Verify Configuration

```bash
cd apps/backend
source .venv/bin/activate

python -c "
from core.auth import get_auth_token, get_auth_token_source
token = get_auth_token()
source = get_auth_token_source()
print(f'Token found: {\"Yes\" if token else \"No\"}')
print(f'Token source: {source}')
print(f'Token preview: {token[:20]}...' if token else 'No token')
"
```

Expected output (varies by OS):
```
Token found: Yes
Token source: macOS Keychain  # or Windows Credential Files, or CLAUDE_CODE_OAUTH_TOKEN
Token preview: sk-ant-oat01-...
```

---

## Running Auto-Claude

Once configured (either option), run Auto-Claude:

```bash
cd apps/backend
source .venv/bin/activate

# Create a new spec interactively
python runners/spec_runner.py --interactive

# Or create from a task description
python runners/spec_runner.py --task "Add user authentication"

# Run an existing spec
python run.py --spec 001

# List all specs
python run.py --list
```

### Review and Merge

```bash
# Review changes in isolated worktree
python run.py --spec 001 --review

# Merge completed build into project
python run.py --spec 001 --merge

# Or discard if not satisfied
python run.py --spec 001 --discard
```

---

## How It Works

### Authentication Flow

Auto-Claude uses a priority-based authentication system:

1. **`ANTHROPIC_AUTH_TOKEN`** - CCR/proxy token (used for CLIProxyAPI)
2. **`CLAUDE_CODE_OAUTH_TOKEN`** - OAuth token from environment variable
3. **System credential store** - macOS Keychain, Windows Credential Manager

For CLIProxyAPI setups (Option A), `ANTHROPIC_AUTH_TOKEN` is used.
For direct setups (Option B), the system keychain token is used.

### Environment Variables Passed to SDK

The following environment variables are automatically passed to the Claude Agent SDK subprocess:

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_BASE_URL` | Custom API endpoint (only for Option A) |
| `ANTHROPIC_AUTH_TOKEN` | Auth token for the proxy |
| `NO_PROXY` | Bypass proxy for localhost |
| `DISABLE_TELEMETRY` | Disable usage telemetry |
| `DISABLE_COST_WARNINGS` | Suppress cost warnings |
| `API_TIMEOUT_MS` | Request timeout in milliseconds |

### Security Note

Auto-Claude intentionally does **NOT** support `ANTHROPIC_API_KEY` directly. This is a security feature to prevent accidental billing to your API credits when OAuth is misconfigured.

---

## Troubleshooting

### Process hangs after "Requirements Gathering"

**Cause:** CLIProxyAPI is not running but `ANTHROPIC_BASE_URL` is set.

**Solution:** Either:
1. Start CLIProxyAPI: `cliproxyapi --port 8317`
2. Or switch to Option B by removing `ANTHROPIC_BASE_URL` from `.env`

### Error: "No OAuth token found"

**Cause:** No authentication token available.

**Solution:**
- For Option A: Add `ANTHROPIC_AUTH_TOKEN=cliproxyapi` to `.env`
- For Option B: Run `claude login` or `claude setup-token`

### Error: Connection refused to localhost:8317

**Cause:** CLIProxyAPI is not running.

**Solution:** Start CLIProxyAPI before running Auto-Claude:
```bash
# Check if the port is in use
lsof -i :8317 || netstat -tlnp | grep 8317

# Start your proxy
cliproxyapi --port 8317
```

### Error: API timeout

**Cause:** Request took longer than the configured timeout.

**Solution:** Increase `API_TIMEOUT_MS` in your `.env`:
```bash
API_TIMEOUT_MS=900000  # 15 minutes
```

### Graphiti Memory Errors

**Cause:** Graphiti is enabled but no embedding provider is configured.

**Solution:** Either disable Graphiti or configure an embedding provider:

```bash
# Option 1: Disable Graphiti
GRAPHITI_ENABLED=false

# Option 2: Use Ollama for fully local embeddings (no API keys needed)
GRAPHITI_ENABLED=true
GRAPHITI_LLM_PROVIDER=ollama
GRAPHITI_EMBEDDER_PROVIDER=ollama
OLLAMA_LLM_MODEL=deepseek-r1:7b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_EMBEDDING_DIM=768
```

---

## Complete .env Examples

### Example A: CLIProxyAPI Setup

```bash
# Auto Claude Environment Variables
# Configured to use CLIProxyAPI for Anthropic API access

# =============================================================================
# CUSTOM API ENDPOINT - Using CLIProxyAPI
# =============================================================================
ANTHROPIC_BASE_URL=http://localhost:8317
NO_PROXY=127.0.0.1,localhost
DISABLE_TELEMETRY=true
DISABLE_COST_WARNINGS=true
API_TIMEOUT_MS=600000

# CLIProxyAPI Authentication Token
ANTHROPIC_AUTH_TOKEN=cliproxyapi

# =============================================================================
# GRAPHITI MEMORY INTEGRATION
# =============================================================================
GRAPHITI_ENABLED=false

# =============================================================================
# UI SETTINGS
# =============================================================================
ENABLE_FANCY_UI=true
```

### Example B: Direct OAuth Setup (No Proxy)

```bash
# Auto Claude Environment Variables
# Uses Claude Code OAuth token directly (no proxy)

# =============================================================================
# AUTHENTICATION
# =============================================================================
# Token is automatically retrieved from system keychain
# (macOS Keychain, Windows Credential Manager)
# No ANTHROPIC_BASE_URL = uses default Anthropic API

DISABLE_TELEMETRY=true

# =============================================================================
# GRAPHITI MEMORY INTEGRATION
# =============================================================================
GRAPHITI_ENABLED=false

# =============================================================================
# UI SETTINGS
# =============================================================================
ENABLE_FANCY_UI=true
```

---

## Related Documentation

- [CLI Usage Guide](./CLI-USAGE.md) - Detailed CLI command reference
- [Quick Reference](./CLIPROXYAPI-QUICKREF.md) - Quick reference card
- [Main README](../README.md) - Project overview and setup
- [CLAUDE.md](../CLAUDE.md) - Development guidelines and architecture
