"""Build the consolidated calibration dataset.

Merges three sources into analysis/calibration/calibration_trades.csv:

  1. analysis/real_trades/trades.csv                                (25 real trades)
  2. analysis/real_trades/tv_review/ztt_review_2026-05-11_to_2026-06-09_base.csv
     + ztt_trades companion (join on n)                             (60 labeled setups)
  3. analysis/real_trades/tv_review/ztt_review_2026-01-01_to_2026-02-28_v2.csv
     + ztt_trades companion (join on n)                             (87 unlabeled setups)

Deterministic, no network, re-runnable. See analysis/calibration/README.md for
every normalization decision.

TIMEZONE: real-trades `entry_local` is UTC+1 (verified: real trade id=4,
entry_local 2026-05-26 01:20:16, SL 4564.518 / TP 4513.041, is the SAME trade
the user cites verbatim in review row #22 ("the stop loss was 4564.518 and the
take profit was 4513.041"). Review row #23 entry_time = 2026-05-26 00:20 and
its entry_ms 1779754800000 confirms review times are UTC. entry_local minus 1h
= 00:20:16 UTC, 16 seconds from review #23. A UTC+0 assumption would leave a
60-minute gap. Hence entry_time_utc = entry_local - 1 hour.)

USER SL/TP OVERRIDES: exactly 4 rows of the May-Jun review batch carry
explicit user-stated SL/TP prices per ZTT_REVIEW_ANALYSIS.md (#22, #31, #36,
#58). They are hardcoded VERBATIM below -- no regex mining of free text.
"""
from __future__ import annotations

import csv
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REAL_TRADES = ROOT / "analysis/real_trades/trades.csv"
TV_DIR = ROOT / "analysis/real_trades/tv_review"
MJ_REVIEW = TV_DIR / "ztt_review_2026-05-11_to_2026-06-09_base.csv"
MJ_TRADES = TV_DIR / "ztt_trades_2026-05-11_to_2026-06-09_base.csv"
JF_REVIEW = TV_DIR / "ztt_review_2026-01-01_to_2026-02-28_v2.csv"
JF_TRADES = TV_DIR / "ztt_trades_2026-01-01_to_2026-02-28_v2.csv"
OUT_CSV = ROOT / "analysis/calibration/calibration_trades.csv"

REAL_TRADES_UTC_OFFSET_HOURS = 1  # entry_local = UTC+1 (see module docstring)

# Verbatim user-stated SL/TP from ZTT_REVIEW_ANALYSIS.md (sections 1 & 2).
# Keys are May-Jun review row numbers (column `n`). Values are strings so the
# CSV bytes match the document exactly (e.g. "4448.000", not "4448.0").
USER_OVERRIDES = {
    22: {"user_stop_loss": "4564.518", "user_take_profit": "4513.041"},
    31: {"user_stop_loss": "4448.000", "user_take_profit": ""},
    36: {"user_stop_loss": "4510.994", "user_take_profit": ""},
    58: {"user_stop_loss": "4286.754", "user_take_profit": ""},
}
USER_OVERRIDES[58]["user_take_profit"] = "4212.520"

# Dedup rule (real trades vs May-Jun review batch, which overlap in time):
# same direction AND entry price within 0.5% AND entry time within 60 minutes.
DEDUP_PRICE_TOL = 0.005
DEDUP_TIME_TOL_MIN = 60.0

COLUMNS = [
    "source", "source_row_id", "entry_time_utc", "timeframe", "direction",
    "mode", "decision", "entry_price", "stop_loss", "take_profit",
    "user_stop_loss", "user_take_profit", "sl_pct_entry", "tp_pct_entry",
    "user_sl_pct_entry", "user_tp_pct_entry", "rr_algo", "rr_user",
    "outcome", "outcome_class", "realized_r", "realized_r_is_estimated",
    "level_price", "level_touches", "session", "sig_momentum", "sig_fvg",
    "sig_sweep", "htf_up", "atr", "reason_text", "dedup_status",
    "is_duplicate_of",
]

OUTCOME_CLASS = {"win": "win", "loss": "loss", "timeout": "timeout",
                 "miss": "no_entry"}


def _pct(entry: float, level: float) -> str:
    return f"{abs(entry - level) / entry * 100.0:.4f}"


def _rr(entry: float, sl: float, tp: float) -> str:
    sl_dist = abs(entry - sl)
    if sl_dist == 0:
        return ""
    return f"{abs(tp - entry) / sl_dist:.2f}"


def _read_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def load_real_trades() -> list[dict]:
    rows = _read_csv(REAL_TRADES)
    assert len(rows) == 25, f"expected 25 real trades, got {len(rows)}"
    out = []
    for r in rows:
        entry_local = datetime.strptime(r["entry_local"], "%Y-%m-%d %H:%M:%S")
        entry_utc = entry_local - timedelta(hours=REAL_TRADES_UTC_OFFSET_HOURS)
        entry = float(r["entry_price"])
        sl = float(r["sl"])
        tp = float(r["tp"])
        rr_user = _rr(entry, sl, tp)
        outcome = r["outcome"].strip()
        # realized_r is NOT recorded in trades.csv -> estimate from outcome:
        # win => +rr_user, loss => -1.0, miss (never entered) => empty.
        if outcome == "win":
            realized_r, est = rr_user, "True"
        elif outcome == "loss":
            realized_r, est = "-1.00", "True"
        else:  # miss
            realized_r, est = "", ""
        row = {c: "" for c in COLUMNS}
        row.update({
            "source": "real_trades",
            "source_row_id": r["id"],
            "entry_time_utc": entry_utc.strftime("%Y-%m-%d %H:%M:%S") + "+00:00",
            "timeframe": r["timeframe"],
            "direction": r["direction"],
            "decision": "take",  # the user took these trades
            "entry_price": r["entry_price"],
            "stop_loss": r["sl"],
            "take_profit": r["tp"],
            # These trades ARE the user's own SL/TP choices -> mirror them.
            "user_stop_loss": r["sl"],
            "user_take_profit": r["tp"],
            "sl_pct_entry": _pct(entry, sl),
            "tp_pct_entry": _pct(entry, tp),
            "user_sl_pct_entry": _pct(entry, sl),
            "user_tp_pct_entry": _pct(entry, tp),
            "rr_user": rr_user,
            "outcome": outcome,
            "outcome_class": OUTCOME_CLASS[outcome],
            "realized_r": realized_r,
            "realized_r_is_estimated": est,
            "reason_text": r["note"],
        })
        row["_dt"] = entry_utc.replace(tzinfo=timezone.utc)
        out.append(row)
    return out


def load_tv_batch(review_path: Path, trades_path: Path, source: str,
                  expected: int) -> list[dict]:
    review = _read_csv(review_path)
    trades = {t["n"]: t for t in _read_csv(trades_path)}
    assert len(review) == expected, (
        f"{review_path.name}: expected {expected} rows, got {len(review)}")
    out = []
    for r in review:
        t = trades.get(r["n"])
        assert t is not None, f"{trades_path.name}: no companion row n={r['n']}"
        # Join sanity: the two files must describe the same setup.
        for key in ("entry_time", "direction", "entry_price"):
            assert r[key] == t[key], (
                f"join mismatch n={r['n']} field={key}: {r[key]!r} != {t[key]!r}")
        entry_dt = datetime.strptime(r["entry_time"], "%Y-%m-%d %H:%M")
        # Verify review timestamps are UTC via the companion epoch-ms column.
        ms_dt = datetime.fromtimestamp(int(t["entry_ms"]) / 1000.0,
                                       tz=timezone.utc).replace(tzinfo=None)
        assert ms_dt == entry_dt, (
            f"n={r['n']}: entry_time {entry_dt} != entry_ms {ms_dt} (UTC)")
        entry = float(r["entry_price"])
        sl = float(r["stop_loss"])
        tp = float(r["take_profit"])
        row = {c: "" for c in COLUMNS}
        row.update({
            "source": source,
            "source_row_id": r["n"],
            "entry_time_utc": entry_dt.strftime("%Y-%m-%d %H:%M:%S") + "+00:00",
            "timeframe": "10m",  # generator config: OANDA XAUUSD 10m (export_ztt_trades.py)
            "direction": r["direction"],
            "mode": r["mode"],
            "decision": r["decision"].strip(),
            "entry_price": r["entry_price"],
            "stop_loss": r["stop_loss"],
            "take_profit": r["take_profit"],
            "sl_pct_entry": _pct(entry, sl),
            "tp_pct_entry": _pct(entry, tp),
            "rr_algo": r["rr_target"],
            "outcome": r["outcome"],
            "outcome_class": OUTCOME_CLASS[r["outcome"]],
            "realized_r": r["realized_r"],
            "realized_r_is_estimated": "False",
            "level_price": r["level_price"],
            "level_touches": r["level_touches"],
            "session": r["session"],
            "sig_momentum": t["sig_momentum"],
            "sig_fvg": t["sig_fvg"],
            "sig_sweep": t["sig_sweep"],
            "htf_up": t["htf_up"],
            "atr": t["atr"],
        })
        reason = r.get("reason", "").strip()
        notes = r.get("notes", "").strip()
        row["reason_text"] = (f"{reason} || notes: {notes}" if notes else reason)
        if source == "tv_review_may_jun":
            ov = USER_OVERRIDES.get(int(r["n"]))
            if ov:
                row["user_stop_loss"] = ov["user_stop_loss"]
                row["user_take_profit"] = ov["user_take_profit"]
                usl = float(ov["user_stop_loss"])
                row["user_sl_pct_entry"] = _pct(entry, usl)
                if ov["user_take_profit"]:
                    utp = float(ov["user_take_profit"])
                    row["user_tp_pct_entry"] = _pct(entry, utp)
                    row["rr_user"] = _rr(entry, usl, utp)
        row["_dt"] = entry_dt.replace(tzinfo=timezone.utc)
        out.append(row)
    return out


def dedup_pass(real_rows: list[dict], mj_rows: list[dict]) -> int:
    """Fuzzy-match real trades vs May-Jun review rows. Marks BOTH rows of
    each candidate pair; never drops or merges. Returns pair count."""
    pairs = 0
    matches: dict[int, list[str]] = {}
    for rr in real_rows:
        for mj in mj_rows:
            if rr["direction"] != mj["direction"]:
                continue
            p_real = float(rr["entry_price"])
            p_mj = float(mj["entry_price"])
            if abs(p_real - p_mj) / p_real > DEDUP_PRICE_TOL:
                continue
            dt_min = abs((rr["_dt"] - mj["_dt"]).total_seconds()) / 60.0
            if dt_min > DEDUP_TIME_TOL_MIN:
                continue
            pairs += 1
            matches.setdefault(id(rr), []).append(
                f"{mj['source']}:{mj['source_row_id']}")
            matches.setdefault(id(mj), []).append(
                f"{rr['source']}:{rr['source_row_id']}")
            print(f"  dup_candidate: real_trades:{rr['source_row_id']} "
                  f"({rr['entry_time_utc']} {rr['direction']} @{p_real}) <-> "
                  f"tv_review_may_jun:{mj['source_row_id']} "
                  f"({mj['entry_time_utc']} {mj['direction']} @{p_mj}) "
                  f"[dt={dt_min:.1f}min, dp={abs(p_real - p_mj) / p_real * 100:.3f}%]")
    for row in real_rows + mj_rows:
        hits = matches.get(id(row))
        if hits:
            row["dedup_status"] = "dup_candidate"
            row["is_duplicate_of"] = ";".join(hits)
        else:
            row["dedup_status"] = "unique"
    return pairs


def main() -> int:
    real_rows = load_real_trades()
    mj_rows = load_tv_batch(MJ_REVIEW, MJ_TRADES, "tv_review_may_jun", 60)
    jf_rows = load_tv_batch(JF_REVIEW, JF_TRADES, "tv_review_jan_feb", 87)
    for row in jf_rows:  # Jan-Feb is unlabeled: future-label reference set
        row["decision"] = ""
        row["dedup_status"] = "unique"

    print("DEDUP pass (real_trades vs tv_review_may_jun):")
    n_pairs = dedup_pass(real_rows, mj_rows)
    print(f"DEDUP: {n_pairs} dup_candidate pairs found")

    all_rows = real_rows + mj_rows + jf_rows
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        w.writeheader()
        for row in all_rows:
            w.writerow(row)
    print(f"WROTE {OUT_CSV} ({len(all_rows)} rows: "
          f"{len(real_rows)} real_trades + {len(mj_rows)} tv_review_may_jun + "
          f"{len(jf_rows)} tv_review_jan_feb)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
