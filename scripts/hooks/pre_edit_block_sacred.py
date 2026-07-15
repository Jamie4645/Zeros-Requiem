"""PreToolUse hook: block Edit/Write to sacred CLAUDE.md-protected files.

Reads the Claude Code hook payload from stdin and exits with code 2 if the
target file matches a protected path. Exit code 2 instructs Claude Code to
block the tool call and surface the stderr message back to the assistant.
"""
from __future__ import annotations

import json
import re
import sys

# 2026-06-09 — risk_manager.py UNLOCKED for the ZTT (Zero's True Trade) rebuild
# per explicit user directive ("take the lock on any file I've locked"). The
# legacy SBRS params file stays guarded (it belongs to the now-VOID strategy).
# New ZTT sacred params (defined in Phase 2, src/regimes/ztt.py) will be added
# to this pattern once frozen.
PROTECTED = re.compile(r"(sbrs_original_parameters\.py)$")
MESSAGE = (
    "BLOCKED: {path} is a CLAUDE.md-protected sacred file. "
    "Ask the user for explicit approval before editing."
)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    file_path = (payload.get("tool_input") or {}).get("file_path", "") or ""
    if PROTECTED.search(file_path.replace("\\", "/")):
        print(MESSAGE.format(path=file_path), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
