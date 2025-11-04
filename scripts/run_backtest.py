#!/usr/bin/env python3
"""Helper to run the backtest script using local Python or a venv."""

import sys
import subprocess
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    # Prefer venv if present
    venv_python = repo_root / ".venv" / "Scripts" / "python.exe"
    py = venv_python if venv_python.exists() else sys.executable
    script = repo_root / "src" / "backtest.py"
    args = [str(py), str(script)] + sys.argv[1:]
    try:
        return subprocess.call(args)
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())

