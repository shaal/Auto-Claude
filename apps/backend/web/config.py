"""Web server configuration."""

from dataclasses import dataclass, field
from pathlib import Path
import os


@dataclass
class WebConfig:
    """Configuration for the web server."""
    project_dir: Path = field(default_factory=lambda: Path(os.environ.get("AUTO_CLAUDE_PROJECT_DIR", str(Path.cwd()))))
    host: str = field(default_factory=lambda: os.environ.get("AUTO_CLAUDE_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.environ.get("AUTO_CLAUDE_PORT", "8080")))
    cors_origins: list[str] = field(default_factory=lambda: ["*"])
    static_dir: Path | None = None

    def __post_init__(self):
        self.project_dir = Path(self.project_dir).resolve()
        if self.static_dir:
            self.static_dir = Path(self.static_dir).resolve()
