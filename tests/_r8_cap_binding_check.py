"""
Round 8 Step 5 — SYMBOL_RISK_CAP binding verification (2026-04-20).

Confirms the new R8 caps (Gold 0.50%, DAX 0.25%, NDX 0.15%, GBPUSD 0.20%,
USDJPY 0.00%) bind correctly at engine level when the caller requests a
higher risk than the cap. Also verifies the ticker-map normaliser reaches
GC=F, ^IXIC, ^GDAXI, and the OANDA names (XAU_USD, NAS100_USD, DE30_EUR,
GBP_USD, USD_JPY).

Writes: logs/round8/cap_binding_check.log
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.risk_manager import risk_config_for_interval, SYMBOL_RISK_CAP, _normalize_symbol_for_cap

LOG = Path(__file__).resolve().parent.parent / "logs" / "round8" / "cap_binding_check.log"
LOG.parent.mkdir(parents=True, exist_ok=True)

# Caller requests 1.00% risk intentionally — every cap should bind below that.
CALLER_RISK = 0.01

# (symbol, asset_class, expected_cap_key, expected_effective_risk)
CASES = [
    # Gold
    ("GC=F",       "gold",    "GOLD",   0.0050),
    ("XAUUSD",     "gold",    "GOLD",   0.0050),
    ("XAU_USD",    "gold",    "GOLD",   0.0050),
    # DAX
    ("^GDAXI",     "indices", "DAX",    0.0025),
    ("DE30_EUR",   "indices", "DAX",    0.0025),
    # NDX
    ("^IXIC",      "indices", "NDX",    0.0015),
    ("NAS100_USD", "indices", "NDX",    0.0015),
    # GBPUSD
    ("GBPUSD=X",   "forex",   "GBPUSD", 0.0020),
    ("GBP_USD",    "forex",   "GBPUSD", 0.0020),
    ("GBPUSD",     "forex",   "GBPUSD", 0.0020),
    # USDJPY
    ("USDJPY=X",   "forex",   "USDJPY", 0.0000),
    ("USD_JPY",    "forex",   "USDJPY", 0.0000),
    # Uncapped (passthrough)
    ("EURUSD=X",   "forex",   None,     CALLER_RISK),
]

lines = []
p = lambda s: (lines.append(s), print(s))

p("=" * 72)
p("  R8 STEP 5 | SYMBOL_RISK_CAP binding verification | 2026-04-20")
p("=" * 72)
p(f"  caller_risk = {CALLER_RISK:.4f} (1.00%)")
p(f"  SYMBOL_RISK_CAP = {SYMBOL_RISK_CAP}")
p("-" * 72)
p(f"  {'symbol':<14} {'class':<8} {'expect_key':<8} {'expect_eff':>10} {'got_eff':>10} {'norm':<8} {'verdict':<6}")
p("-" * 72)

fails = 0
for symbol, ac, expect_key, expect_eff in CASES:
    norm = _normalize_symbol_for_cap(symbol)
    rc = risk_config_for_interval('1h', CALLER_RISK, ac, symbol=symbol)
    got = rc.risk_per_trade
    key_ok = (norm == expect_key) if expect_key else (norm not in SYMBOL_RISK_CAP)
    eff_ok = abs(got - expect_eff) < 1e-9
    ok = key_ok and eff_ok
    if not ok:
        fails += 1
    v = "PASS" if ok else "FAIL"
    p(f"  {symbol:<14} {ac:<8} {str(expect_key):<8} {expect_eff:>10.4f} {got:>10.4f} {str(norm):<8} {v:<6}")

p("-" * 72)
if fails == 0:
    p(f"  RESULT: all {len(CASES)} cases PASS — R8 caps bind correctly.")
else:
    p(f"  RESULT: {fails}/{len(CASES)} FAIL — investigate normaliser or cap dict.")

with open(LOG, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"Written to {LOG}")

sys.exit(0 if fails == 0 else 1)
