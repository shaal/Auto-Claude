"""Entry point for the Auto Claude web server.

Usage:
    python -m web.run_web --project-dir /path/to/repo
    python -m web.run_web --port 8080 --host 0.0.0.0
"""

import argparse
import sys
from pathlib import Path

# Ensure backend directory is on sys.path
_BACKEND_DIR = Path(__file__).parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))


def main():
    parser = argparse.ArgumentParser(description="Auto Claude Web Dashboard")
    parser.add_argument("--project-dir", type=str, default=None, help="Project directory to manage")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on")
    parser.add_argument("--static-dir", type=str, default=None, help="Path to built web frontend")
    args = parser.parse_args()

    # Load .env
    try:
        from dotenv import load_dotenv
        env_file = _BACKEND_DIR / ".env"
        if env_file.exists():
            load_dotenv(env_file)
    except ImportError:
        pass

    # Auto-detect static dir
    static_dir = args.static_dir
    if not static_dir:
        # Check for built frontend relative to project
        frontend_dist = _BACKEND_DIR.parent / "frontend" / "dist-web"
        if frontend_dist.exists():
            static_dir = str(frontend_dist)

    from web.config import WebConfig
    from web.server import create_app

    config = WebConfig(
        project_dir=Path(args.project_dir) if args.project_dir else Path.cwd(),
        host=args.host,
        port=args.port,
        static_dir=Path(static_dir) if static_dir else None,
    )

    app = create_app(config)

    import uvicorn
    print(f"\n  Auto Claude Web Dashboard")
    print(f"  Project: {config.project_dir}")
    print(f"  URL: http://{config.host}:{config.port}")
    if config.static_dir:
        print(f"  Static: {config.static_dir}")
    print()

    uvicorn.run(app, host=config.host, port=config.port)


if __name__ == "__main__":
    main()
