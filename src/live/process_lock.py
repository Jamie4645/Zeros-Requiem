"""
Single-instance lock for live execution (runner + engine_live).

Prevents two processes from writing state / placing duplicate orders.
Uses a byte-range lock on state/.sbrs_live_execution.lock (Windows + POSIX).
"""

from __future__ import annotations

import atexit
import os
import sys
from pathlib import Path

LOCK_PATH = Path(__file__).resolve().parent.parent.parent / 'state' / '.sbrs_live_execution.lock'

_lock_fp = None


def acquire_live_lock() -> None:
    """Exit with code 2 if another live process holds the lock."""
    global _lock_fp
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        fp = open(LOCK_PATH, 'a+', encoding='utf-8')
    except OSError as e:
        print(f"Cannot open lock file {LOCK_PATH}: {e}", file=sys.stderr)
        sys.exit(1)
    try:
        if sys.platform == 'win32':
            import msvcrt
            # msvcrt.locking locks bytes at the CURRENT file position. The file
            # is opened 'a+' (position = EOF), so without this seek two processes
            # lock disjoint bytes and BOTH acquire the "single-instance" lock
            # (duplicate live orders). Lock byte 0 unconditionally.
            fp.seek(0)
            msvcrt.locking(fp.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(fp.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print(
            'Another SBRS live process (runner or engine_live) is already running. Exiting.',
            file=sys.stderr,
        )
        try:
            fp.close()
        except OSError:
            pass
        sys.exit(2)
    fp.seek(0)
    fp.truncate()
    fp.write(str(os.getpid()))
    fp.flush()
    _lock_fp = fp
    atexit.register(_release_live_lock)


def _release_live_lock() -> None:
    global _lock_fp
    fp = _lock_fp
    if fp is None:
        return
    try:
        if sys.platform == 'win32':
            import msvcrt
            try:
                fp.seek(0)
                msvcrt.locking(fp.fileno(), msvcrt.LK_UNLCK, 1)
            except OSError:
                pass
        else:
            import fcntl
            try:
                fcntl.flock(fp.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass
    finally:
        try:
            fp.close()
        except OSError:
            pass
        _lock_fp = None
        try:
            LOCK_PATH.unlink(missing_ok=True)
        except OSError:
            pass
