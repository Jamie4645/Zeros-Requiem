"""
SBRS 1.1 — Original Parameters (LOCKED FOR LIVE TRADING)

DO NOT MODIFY THIS FILE.
This is the reference copy of all parameters used by the live paper trading bot.
If you change parameters in sbrs_gold.py for experiments, restore from here
before the next hourly run.

Locked: 2026-02-15
"""

# ── Core Parameters (DO NOT OPTIMIZE) ─────────────────────────
WMA_PERIOD = 9
SMMA_PERIOD = 7
SWING_LOOKBACK = 20       # bars to search for swings
SWING_WINDOW = 3          # bars on each side for swing confirmation
MIN_RR = 3.0              # minimum risk:reward ratio
RETEST_TOLERANCE_ATR = 0.5        # retest proximity for LONGS (ATR units)
RETEST_TOLERANCE_ATR_SHORT = 0.3  # tighter retest for SHORTS

# ── Tunable Parameters ────────────────────────────────────────
ATR_PERIOD = 14
MAX_RETEST_WAIT = 10      # max bars to wait for retest after break
SL_BUFFER_ATR = 0.3       # SL distance beyond retest extreme
BE_TRIGGER_R = 1.5        # move SL to breakeven at this R-multiple
BE_BUFFER_R = 0.1         # buffer above breakeven
MAX_HOLD_BARS = 40        # close trade after this many bars
MA_CROSS_LOOKBACK = 10    # bars to search for recent MA cross on 1H
TREND_CROSS_LOOKBACK = 5  # "recently crossed" on 4H (in 4H bars)
CHOP_ATR_THRESHOLD = 1.0  # range < this * ATR = choppy (skip)
CHOP_LOOKBACK = 10        # bars to measure chop

# ── Session Filter ────────────────────────────────────────────
SESSION_BLOCK_START_HOUR = 16    # GMT hour to stop new entries
SESSION_BLOCK_START_MINUTE = 30  # minute cutoff (16:30 GMT)
SESSION_BLOCK_END_HOUR = 24      # resume entries (next day Asia open)

# ── Forex-Specific Parameters ─────────────────────────────────
FOREX_RETEST_TOLERANCE_ATR = 0.3
FOREX_SESSION_START_HOUR = 7
FOREX_SESSION_END_HOUR = 16

# ── Indices-Specific Parameters ───────────────────────────────
INDICES_RETEST_TOLERANCE_ATR = 0.5
INDICES_OPEN_WINDOW_MINUTES = 90
INDICES_CLOSE_WINDOW_MINUTES = 60
INDICES_SESSIONS = {
    '^GSPC':  {'open_h': 13, 'open_m': 30, 'close_h': 20, 'close_m': 0},
    '^IXIC':  {'open_h': 13, 'open_m': 30, 'close_h': 20, 'close_m': 0},
    '^GDAXI': {'open_h': 7,  'open_m': 0,  'close_h': 15, 'close_m': 30},
}

# ── Engine Parameters (in src/core/engine.py) ─────────────────
SBRS_BE_TRIGGER_R = 1.5
SBRS_BE_BUFFER_R = 0.1
SBRS_MAX_HOLD_BARS = 40
SBRS_TRAILING_TRIGGER_R = 3.0

# ── Live Runner Parameters (in src/live/runner.py) ────────────
HISTORY_BARS = 300
RISK_PCT = 0.01  # 1% risk per trade
