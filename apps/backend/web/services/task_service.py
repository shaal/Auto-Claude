"""Task service - wraps CLI functions for web use."""

import json
from pathlib import Path


def get_specs(project_dir: Path) -> list[dict]:
    """Get all specs, with Path objects converted to strings."""
    import sys
    backend_dir = Path(__file__).parent.parent.parent
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    from cli.spec_commands import list_specs
    specs = list_specs(project_dir)
    # Convert Path objects to strings for JSON serialization
    for spec in specs:
        spec["path"] = str(spec["path"])
    return specs


def get_spec_detail(spec_dir: Path) -> dict:
    """Read spec.md and implementation_plan.json for a spec."""
    result = {"folder": spec_dir.name}

    spec_md = spec_dir / "spec.md"
    if spec_md.exists():
        result["spec"] = spec_md.read_text(encoding="utf-8")

    plan_file = spec_dir / "implementation_plan.json"
    if plan_file.exists():
        try:
            result["plan"] = json.loads(plan_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            result["plan"] = None

    qa_report = spec_dir / "qa_report.md"
    if qa_report.exists():
        result["qaReport"] = qa_report.read_text(encoding="utf-8")

    return result


def find_spec_dir(project_dir: Path, spec_folder: str) -> Path | None:
    """Find a spec directory by folder name or number."""
    specs_dir = project_dir / ".auto-claude" / "specs"
    if not specs_dir.exists():
        return None

    # Direct match
    direct = specs_dir / spec_folder
    if direct.exists():
        return direct

    # Match by number prefix
    for d in specs_dir.iterdir():
        if d.is_dir() and d.name.startswith(spec_folder):
            return d

    return None
