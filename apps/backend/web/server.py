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

    # Serve static files and SPA catch-all
    if config.static_dir and config.static_dir.exists():
        app.mount("/assets", StaticFiles(directory=config.static_dir / "assets"), name="assets")

        @app.get("/{path:path}")
        async def spa_catch_all(path: str):
            """Serve index.html for all non-API routes (SPA routing)."""
            file_path = config.static_dir / path
            if file_path.exists() and file_path.is_file():
                return FileResponse(file_path)
            return FileResponse(config.static_dir / "index.html")

    return app
