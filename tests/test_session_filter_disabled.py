"""
Round 5 A1 — Gold session-filter sentinel.

Belt-and-braces for the runtime flag `GOLD_SESSION_FILTER_ENABLED=False`:
the hour constant must also be 99 so the ablation harness (and any future
accidental re-enable) cannot reintroduce the 16:30-23:59 block.

See knowledge-base/67-Round-5-Post-Council-Validation.md and the council
remediation plan (R1 in round5-remediation).
"""
import pandas as pd
import pytest

from src.regimes import sbrs_v2


def test_session_block_start_hour_is_sentinel():
    assert sbrs_v2.SESSION_BLOCK_START_HOUR == 99, (
        "Round 5 council memo: SESSION_BLOCK_START_HOUR must be the 99 sentinel "
        "so `is_session_blocked` never returns True for any hour on a Gold timestamp."
    )


@pytest.mark.parametrize("hour", list(range(24)))
def test_is_session_blocked_false_for_every_hour(hour):
    ts = pd.Timestamp(f"2026-04-18 {hour:02d}:30:00", tz="UTC")
    assert sbrs_v2.is_session_blocked(ts) is False, (
        f"is_session_blocked returned True for hour={hour}; the Gold session "
        f"filter is supposed to be fully disabled post-Round-5."
    )


def test_gold_session_filter_enabled_flag_is_false():
    """Runtime flag must also remain off — defense in depth."""
    assert sbrs_v2.GOLD_SESSION_FILTER_ENABLED is False
