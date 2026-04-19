"""
Round 5 Y2 — IBKR cache silent-staleness guard.

Pre-fix: `_load_cache` returned ANY valid CSV without checking its age.
The outer `fetch_ibkr` call had a 7-day check but the primitive itself did not,
so any future call site that bypassed that wrapper could silently ship stale
bars into backtests/live. Council mandated a guard inside `_load_cache` itself.

Strategy: write through a tmpdir, `os.utime` the file to a stale mtime,
then verify `_load_cache` returns None (forcing refetch).
"""
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest

from src.data import ibkr_fetcher


@pytest.fixture
def cached_file(tmp_path, monkeypatch):
    monkeypatch.setattr(ibkr_fetcher, "CACHE_DIR", tmp_path)
    # Mirror the module's file naming convention
    idx = pd.date_range("2024-01-01", periods=200, freq="h", tz="UTC")
    df = pd.DataFrame({
        "Open": 1.0, "High": 1.1, "Low": 0.9, "Close": 1.05, "Volume": 100
    }, index=idx)
    path = tmp_path / "TESTSYM_1h.csv"
    df.to_csv(path)
    return path


def test_fresh_cache_returns_df(cached_file):
    """A file written seconds ago must be returned."""
    loaded = ibkr_fetcher._load_cache("TESTSYM", "1h")
    assert loaded is not None
    assert len(loaded) == 200


def test_stale_cache_returns_none(cached_file):
    """File mtime aged past the 7-day guard must return None."""
    stale_time = (datetime.now() - timedelta(days=10)).timestamp()
    os.utime(cached_file, (stale_time, stale_time))

    loaded = ibkr_fetcher._load_cache("TESTSYM", "1h")
    assert loaded is None, (
        "Round 5 Y2: _load_cache must refuse caches older than 7 days to prevent "
        "silently feeding month-old bars into backtests/live."
    )


def test_boundary_6_days_still_fresh(cached_file):
    """6-day-old cache is inside the 7-day window."""
    t = (datetime.now() - timedelta(days=6)).timestamp()
    os.utime(cached_file, (t, t))
    assert ibkr_fetcher._load_cache("TESTSYM", "1h") is not None


def test_boundary_8_days_stale(cached_file):
    """8-day-old cache is past the window."""
    t = (datetime.now() - timedelta(days=8)).timestamp()
    os.utime(cached_file, (t, t))
    assert ibkr_fetcher._load_cache("TESTSYM", "1h") is None
