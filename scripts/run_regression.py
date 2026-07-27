from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PROJECTS = (
    ("java-mock-service", REPO_ROOT / "projects" / "java-mock-service"),
    ("ai-service", REPO_ROOT / "projects" / "ai-service"),
)


def main() -> int:
    for project_name, project_dir in PROJECTS:
        if not project_dir.exists():
            print(f"[regression] missing project directory: {project_dir}", flush=True)
            return 1

        commands = (
            ("sync dependencies", ["uv", "sync", "--frozen"]),
            (
                "compile python files",
                [
                    "uv",
                    "run",
                    "python",
                    "-m",
                    "compileall",
                    "-q",
                    "-x",
                    ".venv|__pycache__",
                    ".",
                ],
            ),
            ("run pytest", ["uv", "run", "pytest"]),
        )
        for label, command in commands:
            exit_code = run_command(project_name, label, command, project_dir)
            if exit_code != 0:
                return exit_code
    print("[regression] all checks passed", flush=True)
    return 0


def run_command(
    project_name: str,
    label: str,
    command: list[str],
    cwd: Path,
) -> int:
    print(f"[regression] {project_name}: {label}", flush=True)
    try:
        completed = subprocess.run(command, cwd=cwd, check=False)
    except FileNotFoundError:
        print(
            "[regression] uv was not found. Install uv before running regression.",
            flush=True,
        )
        return 127
    if completed.returncode != 0:
        print(
            f"[regression] {project_name}: {label} failed with "
            f"exit code {completed.returncode}",
            flush=True,
        )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
