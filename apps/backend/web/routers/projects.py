"""Project endpoints."""

from fastapi import APIRouter, Request

router = APIRouter(tags=["projects"])


@router.get("/projects")
async def get_projects(request: Request):
    """Get the current project info."""
    config = request.app.state.config
    project_dir = config.project_dir
    return [{
        "id": str(project_dir),
        "name": project_dir.name,
        "path": str(project_dir),
        "autoBuildPath": str(project_dir / ".auto-claude"),
        "settings": {},
        "createdAt": None,
        "updatedAt": None,
    }]


@router.post("/projects")
async def add_project(body: dict):
    """In web mode, project is set server-side. This is a no-op."""
    return {
        "id": body.get("path", ""),
        "name": body.get("path", "").split("/")[-1] if body.get("path") else "",
        "path": body.get("path", ""),
    }
