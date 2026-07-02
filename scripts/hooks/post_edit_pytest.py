"""PostToolUse hook: run the quick-test suite after Edit/Write to src/**/*.py.

Reads the Claude Code hook payload from stdin, extracts tool_input.file_path,
runs pytest on the indicator + engine validation suites if the edited file is
under src/. Always exits 0 (informational — never blocks the tool result).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
VENV_PYTHON = PROJECT_ROOT / "venv" / "Scripts" / "python.exe"
QUICK_TESTS = [
    "tests/test_sbrs_indicators.py",
    "tests/test_engine_validation.py",
]
SRC_PY_PATTERN = re.compile(r"src[\\/].*\.py$")
TAIL_LINES = 25


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    file_path = (payload.get("tool_input") or {}).get("file_path", "") or ""
    if not SRC_PY_PATTERN.search(file_path.replace("\\", "/")):
        return 0

    python_exe = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
    proc = subprocess.run(
        [python_exe, "-m", "pytest", *QUICK_TESTS, "--tb=short", "-q"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    combined = (proc.stdout or "") + (proc.stderr or "")
    tail = "\n".join(combined.splitlines()[-TAIL_LINES:])
    print(f"[post-edit pytest] {file_path}")
    print(tail)
    return 0


if __name__ == "__main__":
    sys.exit(main())
