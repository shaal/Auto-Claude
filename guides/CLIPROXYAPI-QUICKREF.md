# CLIProxyAPI Quick Reference

## Option A: With CLIProxyAPI

### 1. Configure `.env`
```bash
# apps/backend/.env
ANTHROPIC_BASE_URL=http://localhost:8317
ANTHROPIC_AUTH_TOKEN=cliproxyapi
NO_PROXY=127.0.0.1,localhost
DISABLE_TELEMETRY=true
DISABLE_COST_WARNINGS=true
API_TIMEOUT_MS=600000
GRAPHITI_ENABLED=false
```

### 2. Run
```bash
# Terminal 1: Start CLIProxyAPI FIRST
~/.local/bin/cliproxyapi --config ~/.cli-proxy-api/config.yaml

# Terminal 2: Run Auto-Claude
cd apps/backend
source .venv/bin/activate
python runners/spec_runner.py --interactive
```

---

## Option B: Without Proxy (Direct OAuth)

### 1. Configure `.env`
```bash
# apps/backend/.env
# NO ANTHROPIC_BASE_URL = uses default API
DISABLE_TELEMETRY=true
GRAPHITI_ENABLED=false
ENABLE_FANCY_UI=true
```

### 2. Run
```bash
cd apps/backend
source .venv/bin/activate
python runners/spec_runner.py --interactive
```

---

## Common Commands

```bash
# Create spec interactively
python runners/spec_runner.py --interactive

# Create from task
python runners/spec_runner.py --task "Add feature X"

# Run build
python run.py --spec 001

# Merge to project
python run.py --spec 001 --merge
```

---

## Verify Setup

```bash
cd apps/backend && source .venv/bin/activate

# Check auth (Option A)
python -c "from dotenv import load_dotenv; load_dotenv(); from core.auth import get_auth_token; print('OK' if get_auth_token() else 'MISSING')"

# Check auth (Option B)
python -c "from core.auth import get_auth_token; print('OK' if get_auth_token() else 'MISSING')"
```

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Hangs after Phase 2 | Proxy not running | Start CLIProxyAPI or use Option B |
| No OAuth token | Missing auth | Add `ANTHROPIC_AUTH_TOKEN` or run `claude login` |
| Connection refused | Proxy not running | `cliproxyapi --port 8317` |
| Timeout errors | Long request | Increase `API_TIMEOUT_MS` |

---

See [CLIPROXYAPI-SETUP.md](./CLIPROXYAPI-SETUP.md) for full documentation.
