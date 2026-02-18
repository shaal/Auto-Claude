"""Async subprocess manager for running builds and spec creation."""

import asyncio
import sys
import time
from pathlib import Path

from ..ws.event_bus import get_event_bus


class ProcessInfo:
    """Info about a running subprocess."""
    def __init__(self, spec_id: str, process: asyncio.subprocess.Process):
        self.spec_id = spec_id
        self.process = process
        self.logs: list[str] = []
        self.started_at = time.time()


class ProcessManager:
    """Manages async subprocesses for builds and spec creation."""

    def __init__(self):
        self._processes: dict[str, ProcessInfo] = {}
        self._backend_dir = Path(__file__).parent.parent.parent

    async def start_build(self, spec_folder: str, project_dir: Path, model: str = "opus") -> str:
        """Start a build subprocess for a spec."""
        python = sys.executable
        run_py = self._backend_dir / "run.py"

        cmd = [
            python, str(run_py),
            "--spec", spec_folder,
            "--model", model,
            "--auto-continue",
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(project_dir),
        )

        info = ProcessInfo(spec_folder, process)
        self._processes[spec_folder] = info

        # Stream output in background
        asyncio.create_task(self._stream_output(info))

        return spec_folder

    async def start_spec_creation(
        self, task_description: str, project_dir: Path, complexity: str = "standard"
    ) -> str:
        """Start a spec creation subprocess."""
        python = sys.executable
        spec_runner = self._backend_dir / "runners" / "spec_runner.py"

        cmd = [
            python, str(spec_runner),
            "--task", task_description,
            "--complexity", complexity,
            "--auto-approve",
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(project_dir),
        )

        process_id = f"spec-create-{int(time.time())}"
        info = ProcessInfo(process_id, process)
        self._processes[process_id] = info

        asyncio.create_task(self._stream_output(info))

        return process_id

    def stop_process(self, spec_folder: str) -> bool:
        """Kill a running process."""
        info = self._processes.get(spec_folder)
        if not info or info.process.returncode is not None:
            return False
        info.process.terminate()
        return True

    def get_status(self, spec_folder: str) -> str:
        """Get process status: running, stopped, or not_found."""
        info = self._processes.get(spec_folder)
        if not info:
            return "not_found"
        if info.process.returncode is None:
            return "running"
        return "stopped"

    def get_logs(self, spec_folder: str) -> list[str]:
        """Get captured log lines for a process."""
        info = self._processes.get(spec_folder)
        if not info:
            return []
        return info.logs

    async def _stream_output(self, info: ProcessInfo) -> None:
        """Read stdout/stderr and publish to event bus."""
        bus = get_event_bus()
        assert info.process.stdout is not None

        while True:
            line = await info.process.stdout.readline()
            if not line:
                break
            text = line.decode("utf-8", errors="replace").rstrip()
            info.logs.append(text)

            # Parse structured markers
            event_type = "log"
            event_data = text

            if "__EXEC_PHASE__" in text:
                event_type = "phase_update"
            elif "__TASK_LOG_STATUS__" in text:
                event_type = "status_change"

            bus.publish({
                "type": event_type,
                "taskId": info.spec_id,
                "data": event_data,
                "timestamp": time.time(),
            })

        # Process exited
        await info.process.wait()
        bus.publish({
            "type": "exit",
            "taskId": info.spec_id,
            "data": {"returncode": info.process.returncode},
            "timestamp": time.time(),
        })


# Singleton
_manager: ProcessManager | None = None


def get_process_manager() -> ProcessManager:
    global _manager
    if _manager is None:
        _manager = ProcessManager()
    return _manager
