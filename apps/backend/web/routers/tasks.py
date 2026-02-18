"""Task/spec endpoints."""

import json
from pathlib import Path
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from ..services.task_service import get_specs, get_spec_detail, find_spec_dir
from ..services.process_manager import get_process_manager

router = APIRouter(tags=["tasks"])


class CreateSpecRequest(BaseModel):
    title: str
    description: str = ""
    complexity: str = "standard"


class StartBuildRequest(BaseModel):
    model: str = "opus"
    skip_qa: bool = False


@router.get("/specs")
async def list_specs(request: Request):
    """List all specs in the project."""
    config = request.app.state.config
    return get_specs(config.project_dir)


@router.get("/specs/{spec_folder}")
async def get_spec(request: Request, spec_folder: str):
    """Get detail for a single spec."""
    config = request.app.state.config
    spec_dir = find_spec_dir(config.project_dir, spec_folder)
    if not spec_dir:
        raise HTTPException(status_code=404, detail=f"Spec '{spec_folder}' not found")
    return get_spec_detail(spec_dir)


@router.post("/specs")
async def create_spec(request: Request, body: CreateSpecRequest):
    """Create a new spec by spawning spec_runner.py."""
    config = request.app.state.config
    pm = get_process_manager()
    process_id = await pm.start_spec_creation(
        task_description=body.title + (f"\n\n{body.description}" if body.description else ""),
        project_dir=config.project_dir,
        complexity=body.complexity,
    )
    return {"success": True, "process_id": process_id}


@router.post("/specs/{spec_folder}/start")
async def start_build(request: Request, spec_folder: str, body: StartBuildRequest | None = None):
    """Start a build for a spec."""
    config = request.app.state.config
    spec_dir = find_spec_dir(config.project_dir, spec_folder)
    if not spec_dir:
        raise HTTPException(status_code=404, detail=f"Spec '{spec_folder}' not found")

    pm = get_process_manager()
    if pm.get_status(spec_folder) == "running":
        raise HTTPException(status_code=409, detail="Build already running")

    model = body.model if body else "opus"
    await pm.start_build(
        spec_folder=spec_folder,
        project_dir=config.project_dir,
        model=model,
    )
    return {"success": True, "status": "started"}


@router.post("/specs/{spec_folder}/stop")
async def stop_build(spec_folder: str):
    """Stop a running build."""
    pm = get_process_manager()
    stopped = pm.stop_process(spec_folder)
    if not stopped:
        raise HTTPException(status_code=404, detail="No running process for this spec")
    return {"success": True, "status": "stopped"}


@router.get("/specs/{spec_folder}/logs")
async def get_logs(spec_folder: str):
    """Get captured logs for a spec build."""
    pm = get_process_manager()
    return {"logs": pm.get_logs(spec_folder)}
