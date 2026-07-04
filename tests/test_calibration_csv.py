"""Tests for the consolidated calibration dataset.

Validates analysis/calibration/calibration_trades.csv built by
analysis/calibration/build_calibration_dataset.py.
"""
import csv
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "analysis/calibration/calibration_trades.csv"
BUILD_SCRIPT = ROOT / "analysis/calibration/build_calibration_dataset.py"

# Verified source row counts (counted from the actual files, not assumed):
#   analysis/real_trades/trades.csv                                -> 25
#   tv_review/ztt_review_2026-05-11_to_2026-06-09_base.csv         -> 60
#   tv_review/ztt_review_2026-01-01_to_2026-02-28_v2.csv           -> 87
EXPECTED_COUNTS = {"real_trades": 25, "tv_review_may_jun": 60,
                   "tv_review_jan_feb": 87}
EXPECTED_TOTAL = 172

MANDATORY_FIELDS = ["source", "source_row_id", "entry_time_utc", "direction",
                    "entry_price"]

# Verbatim user-stated SL/TP from ZTT_REVIEW_ANALYSIS.md (the ONLY 4 rows with
# explicit user prices). Byte-for-byte expected values.
EXPECTED_OVERRIDES = {
    "22": ("4564.518", "4513.041"),
    "31": ("4448.000", ""),
    "36": ("4510.994", ""),
    "58": ("4286.754", "4212.520"),
}


@pytest.fixture(scope="module")
def rows():
    assert CSV_PATH.exists(), f"missing {CSV_PATH} — run the build script"
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_file_exists_and_row_counts(rows):
    assert len(rows) == EXPECTED_TOTAL
    for source, expected in EXPECTED_COUNTS.items():
        got = sum(1 for r in rows if r["source"] == source)
        assert got == expected, f"{source}: expected {expected}, got {got}"


def test_no_nan_in_mandatory_fields(rows):
    for i, r in enumerate(rows):
        for field in MANDATORY_FIELDS:
            val = r[field]
            assert val is not None and val.strip() != "", (
                f"row {i} ({r.get('source')}:{r.get('source_row_id')}): "
                f"mandatory field '{field}' is empty")
            assert val.strip().lower() not in ("nan", "none", "null"), (
                f"row {i}: mandatory field '{field}' = {val!r}")


def test_user_override_rows_byte_match(rows):
    mj = {r["source_row_id"]: r for r in rows
          if r["source"] == "tv_review_may_jun"}
    for row_id, (exp_sl, exp_tp) in EXPECTED_OVERRIDES.items():
        r = mj[row_id]
        assert r["user_stop_loss"] == exp_sl, (
            f"row #{row_id}: user_stop_loss {r['user_stop_loss']!r} "
            f"!= {exp_sl!r}")
        assert r["user_take_profit"] == exp_tp, (
            f"row #{row_id}: user_take_profit {r['user_take_profit']!r} "
            f"!= {exp_tp!r}")
    # No other tv_review row may carry user SL/TP values.
    for row_id, r in mj.items():
        if row_id not in EXPECTED_OVERRIDES:
            assert r["user_stop_loss"] == "" and r["user_take_profit"] == "", (
                f"row #{row_id}: unexpected user override values")


def test_dedup_ran_and_script_logs_count(rows):
    # Column exists and every row has a status (never dropped/merged).
    assert "dedup_status" in rows[0]
    assert all(r["dedup_status"] in ("unique", "dup_candidate") for r in rows)
    # Candidates are marked on BOTH sides with cross-references.
    dups = [r for r in rows if r["dedup_status"] == "dup_candidate"]
    assert len(dups) > 0, "expected known real-trade/May-Jun overlaps"
    for r in dups:
        assert r["is_duplicate_of"].strip() != ""
    # The build script is deterministic and re-runnable: re-run and check that
    # it logs a dedup count (and rewrites identical output).
    before = CSV_PATH.read_bytes()
    proc = subprocess.run(
        [sys.executable, str(BUILD_SCRIPT)],
        capture_output=True, text=True, cwd=str(ROOT))
    assert proc.returncode == 0, proc.stderr
    assert "DEDUP:" in proc.stdout and "dup_candidate pairs found" in proc.stdout
    assert CSV_PATH.read_bytes() == before, "build script is not deterministic"


def test_entry_time_utc_parses_as_utc(rows):
    pd = pytest.importorskip("pandas")
    times = pd.to_datetime([r["entry_time_utc"] for r in rows], utc=True)
    assert not times.isna().any()
    assert str(times.tz) == "UTC"
    # Explicit UTC offset present on every timestamp string.
    assert all(r["entry_time_utc"].endswith("+00:00") for r in rows)
