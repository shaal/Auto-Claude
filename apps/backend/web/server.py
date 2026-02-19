"""FastAPI web server for Auto Claude shared dashboard."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .config import WebConfig
from .routers import projects, tasks, workspace
from .ws.events import router as ws_router


def create_app(config: WebConfig | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    if config is None:
        config = WebConfig()

    app = FastAPI(title="Auto Claude Web Dashboard", version="1.0.0")
    app.state.config = config

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routers
    app.include_router(projects.router, prefix="/api")
    app.include_router(tasks.router, prefix="/api")
    app.include_router(workspace.router, prefix="/api")

    # WebSocket
    app.include_router(ws_router, prefix="/ws")

    # Health check
    @app.get("/api/health")
    async def health():
        return {"status": "ok", "project_dir": str(config.project_dir)}

    # Settings endpoints (simple JSON file persistence)
    @app.get("/api/settings/tab-state")
    async def get_tab_state():
        import json
        settings_file = config.project_dir / ".auto-claude" / "web-settings.json"
        if settings_file.exists():
            return json.loads(settings_file.read_text())
        return {"openProjectIds": [], "activeProjectId": None, "tabOrder": []}

    @app.post("/api/settings/tab-state")
    async def save_tab_state(tab_state: dict):
        import json
        settings_dir = config.project_dir / ".auto-claude"
        settings_dir.mkdir(parents=True, exist_ok=True)
        settings_file = settings_dir / "web-settings.json"
        settings_file.write_text(json.dumps(tab_state, indent=2))
        return {"success": True}

    # App settings (skip onboarding wizard in web mode)
    _APP_SETTINGS_FILE = config.project_dir / ".auto-claude" / "web-app-settings.json"
    _BACKEND_DIR = str(Path(__file__).parent.parent.resolve())

    @app.get("/api/settings")
    async def get_settings():
        import json
        settings = {}
        if _APP_SETTINGS_FILE.exists():
            try:
                settings = json.loads(_APP_SETTINGS_FILE.read_text())
            except (json.JSONDecodeError, OSError):
                settings = {}
        # Always force onboarding completed — web mode has no wizard
        settings["onboardingCompleted"] = True
        # Provide autoBuildPath so project initialization works
        settings.setdefault("autoBuildPath", _BACKEND_DIR)
        return settings

    @app.post("/api/settings")
    async def save_settings(updates: dict):
        import json
        settings = {}
        if _APP_SETTINGS_FILE.exists():
            try:
                settings = json.loads(_APP_SETTINGS_FILE.read_text())
            except (json.JSONDecodeError, OSError):
                settings = {}
        settings.update(updates)
        # Always force onboarding completed
        settings["onboardingCompleted"] = True
        settings_dir = config.project_dir / ".auto-claude"
        settings_dir.mkdir(parents=True, exist_ok=True)
        _APP_SETTINGS_FILE.write_text(json.dumps(settings, indent=2))
        return settings

    # GitHub CLI status (check if gh is available on the server)
    @app.get("/api/github/cli-status")
    async def github_cli_status():
        import shutil
        import subprocess
        result = {"installed": False, "authenticated": False}
        gh_path = shutil.which("gh")
        if not gh_path:
            return result
        try:
            version_out = subprocess.run(
                [gh_path, "--version"], capture_output=True, text=True, timeout=5
            )
            if version_out.returncode == 0:
                # Extract version like "gh version 2.x.x ..."
                first_line = version_out.stdout.strip().split("\n")[0]
                result["installed"] = True
                result["version"] = first_line.split()[-1] if first_line else None
        except Exception:
            return result
        try:
            auth_out = subprocess.run(
                [gh_path, "auth", "status"], capture_output=True, text=True, timeout=5
            )
            result["authenticated"] = auth_out.returncode == 0
            if result["authenticated"]:
                # Try to get username
                user_out = subprocess.run(
                    [gh_path, "api", "user", "--jq", ".login"],
                    capture_output=True, text=True, timeout=5
                )
                if user_out.returncode == 0 and user_out.stdout.strip():
                    result["username"] = user_out.stdout.strip()
        except Exception:
            pass
        return result

    # Serve static files and SPA catch-all
    if config.static_dir and config.static_dir.exists():
        assets_dir = config.static_dir / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        # Detect the HTML entry point (build outputs index.web.html)
        index_html = config.static_dir / "index.web.html"
        if not index_html.exists():
            index_html = config.static_dir / "index.html"

        @app.get("/{path:path}")
        async def spa_catch_all(path: str):
            """Serve static files or fall back to index.html for SPA routing."""
            file_path = config.static_dir / path
            if file_path.exists() and file_path.is_file():
                return FileResponse(file_path)
            return FileResponse(index_html)

    return app
