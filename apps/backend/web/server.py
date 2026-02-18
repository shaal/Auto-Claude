"""FastAPI web server for Auto Claude shared dashboard."""

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
