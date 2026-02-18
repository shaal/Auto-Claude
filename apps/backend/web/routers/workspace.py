"""Workspace endpoints (merge, discard, diff)."""

import subprocess
from pathlib import Path
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from ..services.task_service import find_spec_dir

router = APIRouter(tags=["workspace"])


class MergeRequest(BaseModel):
    noCommit: bool = False


@router.get("/workspace/{spec_folder}/diff")
async def get_diff(request: Request, spec_folder: str):
    """Get diff for a spec's worktree."""
    config = request.app.state.config
    worktree_path = config.project_dir / ".worktrees" / spec_folder

    if not worktree_path.exists():
        raise HTTPException(status_code=404, detail="No worktree found for this spec")

    try:
        result = subprocess.run(
            ["git", "diff", "--stat", "HEAD"],
            cwd=worktree_path,
            capture_output=True,
            text=True,
            timeout=30,
        )
        diff_stat = result.stdout if result.returncode == 0 else ""

        result = subprocess.run(
            ["git", "diff", "HEAD"],
            cwd=worktree_path,
            capture_output=True,
            text=True,
            timeout=30,
        )
        diff_full = result.stdout if result.returncode == 0 else ""

        return {
            "stat": diff_stat,
            "diff": diff_full,
            "worktreePath": str(worktree_path),
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Diff operation timed out")


@router.post("/workspace/{spec_folder}/merge")
async def merge_worktree(request: Request, spec_folder: str, body: MergeRequest | None = None):
    """Merge a spec's worktree back to main."""
    import sys
    config = request.app.state.config
    backend_dir = Path(__file__).parent.parent.parent
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    try:
        from cli.workspace_commands import handle_merge_command
        no_commit = body.noCommit if body else False
        success = handle_merge_command(config.project_dir, spec_folder, no_commit=no_commit)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workspace/{spec_folder}/discard")
async def discard_worktree(request: Request, spec_folder: str):
    """Discard a spec's worktree."""
    import sys
    config = request.app.state.config
    backend_dir = Path(__file__).parent.parent.parent
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    try:
        from cli.workspace_commands import handle_discard_command
        handle_discard_command(config.project_dir, spec_folder)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspace/{spec_folder}/merge-preview")
async def merge_preview(request: Request, spec_folder: str):
    """Preview merge conflicts without actually merging."""
    import sys
    config = request.app.state.config
    backend_dir = Path(__file__).parent.parent.parent
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    try:
        from cli.workspace_commands import handle_merge_preview_command
        result = handle_merge_preview_command(config.project_dir, spec_folder)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
