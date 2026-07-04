# Calibration Dataset — `calibration_trades.csv`

Consolidated dataset merging the user's real annotated trades with the labeled
TradingView review batches, for calibrating the ZTT screener / selection layer.

- **Build:** `venv\Scripts\python.exe analysis\calibration\build_calibration_dataset.py`
  (deterministic, no network, re-runnable — byte-identical output on re-run)
- **Tests:** `venv\Scripts\python.exe -m pytest tests\test_calibration_csv.py -v`
- **Rows:** 172 = 25 `real_trades` + 60 `tv_review_may_jun` + 87 `tv_review_jan_feb`

## Provenance

| source | file(s) | rows | labels |
|---|---|---|---|
| `real_trades` | `analysis/real_trades/trades.csv` (from `Zeros True Trade 5m - 15m.docx`) | 25 | all `decision=take` (the user actually took them; incl. 1 `miss` he planned but never entered) |
| `tv_review_may_jun` | `tv_review/ztt_review_2026-05-11_to_2026-06-09_base.csv` + `ztt_trades_..._base.csv` (joined on `n`) | 60 | 30 take / 30 skip, free-text reasons |
| `tv_review_jan_feb` | `tv_review/ztt_review_2026-01-01_to_2026-02-28_v2.csv` + `ztt_trades_..._v2.csv` (joined on `n`) | 87 | **unlabeled** (`decision` empty) — future-label reference set |

Join sanity is asserted in the build script: for every review row, the trades
companion row with the same `n` must match on `entry_time`, `direction`,
`entry_price`, and `entry_time` must equal the companion `entry_ms` epoch (UTC).

## Schema (33 columns)

| column | meaning | notes |
|---|---|---|
| `source` | `real_trades` \| `tv_review_may_jun` \| `tv_review_jan_feb` | |
| `source_row_id` | `id` (real trades) / `n` (tv batches) | unique within source |
| `entry_time_utc` | entry timestamp, UTC, `YYYY-MM-DD HH:MM:SS+00:00` | see Timezone below |
| `timeframe` | chart timeframe | real trades: as recorded (5m/10m/15m); tv batches: `10m` (generator config — `export_ztt_trades.py` runs on OANDA XAUUSD 10m data) |
| `direction` | long/short | |
| `mode` | continuation/range/reversal | tv batches only |
| `decision` | `take` / `skip` / empty (NaN) | real trades = `take`; Jan–Feb = empty |
| `entry_price`, `stop_loss`, `take_profit` | as recorded in the source (verbatim strings) | real trades: the user's own SL/TP; tv batches: the algo's SL/TP |
| `user_stop_loss`, `user_take_profit` | user-stated levels | real trades: mirror of `stop_loss`/`take_profit` (they ARE user choices); tv batches: ONLY the 4 hardcoded override rows (below), everything else empty |
| `sl_pct_entry`, `tp_pct_entry` | \|entry−SL\|/entry, \|TP−entry\|/entry, in % (4 dp) | computed from `stop_loss`/`take_profit` |
| `user_sl_pct_entry`, `user_tp_pct_entry` | same, from user levels | empty where user levels empty |
| `rr_algo` | algo target R:R (`rr_target`) | tv batches only |
| `rr_user` | \|TP−entry\|/\|entry−SL\| from **user** levels (2 dp) | real trades: all rows; tv: only #22 (1.77) and #58 (4.19) |
| `outcome` | verbatim source outcome (`win/loss/timeout/miss`) | |
| `outcome_class` | normalized: `win`, `loss`, `timeout`, `no_entry` (miss) | |
| `realized_r` | realized R multiple | tv: measured by the exporter; real trades: **estimated** (see below) |
| `realized_r_is_estimated` | `True`/`False`/empty | `True` for all real-trade win/loss rows, `False` for tv rows, empty for the `miss` row |
| `level_price`, `level_touches`, `session` | tv batches only | |
| `sig_momentum`, `sig_fvg`, `sig_sweep`, `htf_up`, `atr` | from the `ztt_trades_*` feature companions | tv batches only |
| `reason_text` | real trades: `note`; tv: `reason`, with `notes` appended as `" \|\| notes: <notes>"` when present | |
| `dedup_status` | `unique` / `dup_candidate` | every row has one |
| `is_duplicate_of` | `<source>:<source_row_id>`, `;`-joined if multiple | dup candidates only |

Fields a source doesn't have are left **empty** — nothing is fabricated.

## Normalization decisions

### 1. Timezone: real-trades `entry_local` = **UTC+1** (verified, not assumed)
Evidence: real trade **id=4** (`entry_local 2026-05-26 01:20:16`, SL 4564.518,
TP 4513.041) is the same trade the user cites verbatim in May–Jun review row
**#22**: *"this was actually a trade I entered and the stop loss was 4564.518
and the take profit was 4513.041"*. Review timestamps are UTC (proven per-row
in the build script by matching `entry_time` against the companion `entry_ms`
epoch-ms column). Review #23 sits at `2026-05-26 00:20 UTC`; `entry_local −
1h = 00:20:16 UTC` — a **16-second** gap (price 0.047% apart). Under a UTC+0
assumption the gap would be ~60 minutes. Conclusion: `entry_time_utc =
entry_local − 1 hour` for all 25 real trades. TV batch times are already UTC.

### 2. The 4 hardcoded user SL/TP overrides (May–Jun batch only)
Copied **verbatim** from `tv_review/ZTT_REVIEW_ANALYSIS.md` (the only rows
where the user states explicit prices). No regex-mining of free text.

| row | user_stop_loss | user_take_profit |
|---|---|---|
| #22 | `4564.518` | `4513.041` |
| #31 | `4448.000` | *(none stated)* |
| #36 | `4510.994` | *(none stated)* |
| #58 | `4286.754` | `4212.520` |

Note: `rr_user` is **recomputed** from these prices: #22 → 32.904/18.573 =
**1.77**, #58 → 59.940/14.294 = **4.19**. ZTT_REVIEW_ANALYSIS.md states 1.73
and 4.45 — its arithmetic is slightly off; this dataset keeps the computed
values (the raw prices, which byte-match the doc, are the ground truth).

### 3. Dedup rule (real trades × May–Jun batch, overlapping period)
Fuzzy match: **same direction AND entry price within 0.5% AND entry time
within 60 minutes**. Both rows of a pair get `dedup_status=dup_candidate` and
cross-referencing `is_duplicate_of`. Rows are **never dropped or merged**.

**3 candidate pairs found** (5 rows marked):

| pair | Δt | Δprice |
|---|---|---|
| `real_trades:4` ↔ `tv_review_may_jun:22` | 10.3 min | 0.124% |
| `real_trades:4` ↔ `tv_review_may_jun:23` | 0.3 min | 0.047% |
| `real_trades:7` ↔ `tv_review_may_jun:2` | 29.0 min | 0.426% |

Known near-miss (documented, NOT marked): `real_trades:1` (2026-06-04
03:40:11 UTC, long 4460.048) vs `tv_review_may_jun:43` (02:40:00 UTC, long
4470.445) — Δt = 60.2 min, just outside the 60-minute window. Also
`real_trades:4` ↔ `tv_review_may_jun:24` fails on Δt = 89.7 min despite the
user's reason text linking #24 to #22/#23. Widen the window deliberately if
you want these; the rule is applied strictly as registered.

### 4. `realized_r` estimation for real trades
`trades.csv` records only `outcome`, not realized R. Estimate: `win` → +`rr_user`
(assumes TP hit at the recorded TP), `loss` → −1.00 (assumes SL hit at the
recorded SL), `miss` → empty. All flagged `realized_r_is_estimated=True`.
TV rows carry the exporter-measured `realized_r` (`False`).

### 5. Other decisions
- `decision=take` for all 25 real trades (he took them), including id=14
  (`outcome=miss` / `outcome_class=no_entry`: planned but price never retested).
- Real-trade SL/TP are mirrored into `user_stop_loss/user_take_profit` because
  they are genuinely the user's own levels — this makes user-level exit
  geometry (`user_sl_pct_entry` etc.) comparable across sources.
- `timeframe=10m` for tv rows comes from the generator config (screener runs
  on OANDA XAUUSD 10m), not from the CSVs themselves.
- `session` etc. are NOT derived for real trades (would require re-running the
  algo's session classifier — left empty rather than approximated).
- Numeric derived fields: percentages 4 dp, R:R 2 dp. Source numerics are
  copied as verbatim strings to preserve byte fidelity.
