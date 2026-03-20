"""
SBRS 1.0 — Indicator Unit Tests
Tests WMA, SMMA, and swing detection logic.
Run: py -m tests.test_sbrs_indicators
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from src.indicators.technical import (
    wma, smma,
    detect_swing_high, detect_swing_low,
    get_recent_swing_high, get_recent_swing_low
)

passed = 0
failed = 0

def check(name, condition, detail=""):
    global passed, failed
    if condition:
        print(f"  PASS: {name}")
        passed += 1
    else:
        print(f"  FAIL: {name} — {detail}")
        failed += 1


print("=" * 60)
print("  SBRS 1.0 — Indicator Unit Tests")
print("=" * 60)

# ============================================
# Test 1: WMA calculation
# ============================================
print("\n--- WMA Tests ---")

prices = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0])
w = wma(prices, period=3)

# WMA(3) at index 2: (10*1 + 11*2 + 12*3) / 6 = 68/6 = 11.333
check("WMA seed value", abs(w.iloc[2] - 11.333) < 0.01,
      f"Expected 11.333, got {w.iloc[2]:.3f}")

# WMA(3) at index 3: (11*1 + 12*2 + 13*3) / 6 = 74/6 = 12.333
check("WMA rolling value", abs(w.iloc[3] - 12.333) < 0.01,
      f"Expected 12.333, got {w.iloc[3]:.3f}")

# First two values should be NaN
check("WMA NaN padding", np.isnan(w.iloc[0]) and np.isnan(w.iloc[1]),
      "First period-1 values should be NaN")

# WMA(9) — default period
w9 = wma(prices, period=9)
# Only last value should be non-NaN (9 values, period=9)
check("WMA(9) first valid at index 8", not np.isnan(w9.iloc[8]),
      f"Value at idx 8: {w9.iloc[8]}")
check("WMA(9) NaN at index 7", np.isnan(w9.iloc[7]),
      f"Value at idx 7: {w9.iloc[7]}")

# ============================================
# Test 2: SMMA calculation
# ============================================
print("\n--- SMMA Tests ---")

prices2 = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0])
s = smma(prices2, period=3)

# SMMA(3) at index 2: SMA(1,2,3) = 2.0
check("SMMA seed = SMA", abs(s.iloc[2] - 2.0) < 0.001,
      f"Expected 2.000, got {s.iloc[2]:.3f}")

# SMMA at index 3: (2.0 * 2 + 4.0) / 3 = 8/3 = 2.667
check("SMMA recursive step 1", abs(s.iloc[3] - 2.6667) < 0.01,
      f"Expected 2.667, got {s.iloc[3]:.3f}")

# SMMA at index 4: (2.667 * 2 + 5.0) / 3 = 10.333/3 = 3.444
expected_4 = (2.6667 * 2 + 5.0) / 3
check("SMMA recursive step 2", abs(s.iloc[4] - expected_4) < 0.01,
      f"Expected {expected_4:.3f}, got {s.iloc[4]:.3f}")

# NaN padding
check("SMMA NaN at index 0", np.isnan(s.iloc[0]),
      f"Value at idx 0: {s.iloc[0]}")
check("SMMA NaN at index 1", np.isnan(s.iloc[1]),
      f"Value at idx 1: {s.iloc[1]}")

# SMMA is smoother than SMA — verify it's always between extremes
check("SMMA values reasonable", all(1.0 <= s.iloc[i] <= 7.0 for i in range(2, 7)),
      "SMMA should stay within data range")

# ============================================
# Test 3: Swing High Detection
# ============================================
print("\n--- Swing High Tests ---")

# Clear swing high at index 5: peak of 110
# Left 3: [103, 104, ...] < 110 ✓
# Right 3: [104, 103, 102] < 110 ✓
highs = pd.Series([100, 101, 102, 103, 104, 110, 104, 103, 102, 101, 100])
sh = detect_swing_high(highs, left=3, right=3)

check("Swing high at index 5", sh.iloc[5] == True,
      f"Got {sh.iloc[5]}")
check("Only 1 swing high total", sh.sum() == 1,
      f"Expected 1, got {sh.sum()}")

# Equal highs should NOT form a swing (strictly less than required)
highs_eq = pd.Series([100, 101, 102, 103, 103, 103, 102, 101, 100, 98, 97])
sh_eq = detect_swing_high(highs_eq, left=3, right=3)
check("Equal highs = no swing", sh_eq.sum() == 0,
      f"Expected 0, got {sh_eq.sum()}")

# Multiple swing highs
highs_multi = pd.Series([90, 91, 92, 93, 100, 93, 92, 91, 92, 93, 105, 93, 92, 91, 90])
sh_multi = detect_swing_high(highs_multi, left=3, right=3)
check("Two swing highs detected", sh_multi.sum() == 2,
      f"Expected 2, got {sh_multi.sum()}")
check("First swing at index 4", sh_multi.iloc[4] == True,
      f"Got {sh_multi.iloc[4]}")
check("Second swing at index 10", sh_multi.iloc[10] == True,
      f"Got {sh_multi.iloc[10]}")

# ============================================
# Test 4: Swing Low Detection
# ============================================
print("\n--- Swing Low Tests ---")

# Clear swing low at index 5: trough of 90
lows = pd.Series([100, 99, 98, 97, 96, 90, 96, 97, 98, 99, 100])
sl = detect_swing_low(lows, left=3, right=3)

check("Swing low at index 5", sl.iloc[5] == True,
      f"Got {sl.iloc[5]}")
check("Only 1 swing low total", sl.sum() == 1,
      f"Expected 1, got {sl.sum()}")

# Equal lows should NOT form a swing
lows_eq = pd.Series([100, 99, 98, 97, 97, 97, 98, 99, 100, 101, 102])
sl_eq = detect_swing_low(lows_eq, left=3, right=3)
check("Equal lows = no swing", sl_eq.sum() == 0,
      f"Expected 0, got {sl_eq.sum()}")

# ============================================
# Test 5: get_recent_swing_high with 3-bar lag
# ============================================
print("\n--- get_recent_swing_high Tests ---")

# Swing at index 5. Needs 3 right bars to confirm.
# At bar 8 (search_end = 8-3=5): swing at 5 IS detectable
result = get_recent_swing_high(highs, sh, current_idx=8, lookback=20)
check("Found at bar 8", result == (5, 110.0),
      f"Expected (5, 110.0), got {result}")

# At bar 7 (search_end = 7-3=4): swing at 5 is NOT yet detectable
result2 = get_recent_swing_high(highs, sh, current_idx=7, lookback=20)
check("Not found at bar 7 (3-bar lag)", result2 is None,
      f"Expected None, got {result2}")

# Lookback too short
result3 = get_recent_swing_high(highs, sh, current_idx=10, lookback=2)
check("Not found with short lookback", result3 is None,
      f"Expected None (lookback=2), got {result3}")

# ============================================
# Test 6: get_recent_swing_low with 3-bar lag
# ============================================
print("\n--- get_recent_swing_low Tests ---")

result4 = get_recent_swing_low(lows, sl, current_idx=8, lookback=20)
check("Found at bar 8", result4 == (5, 90.0),
      f"Expected (5, 90.0), got {result4}")

result5 = get_recent_swing_low(lows, sl, current_idx=7, lookback=20)
check("Not found at bar 7 (3-bar lag)", result5 is None,
      f"Expected None, got {result5}")

# ============================================
# Test 7: WMA vs SMMA cross detection logic (manual)
# ============================================
print("\n--- WMA/SMMA Cross Logic Test ---")

# Create data where WMA(3) crosses above SMMA(3)
# Rising prices should cause WMA to lead (react faster)
rising = pd.Series([10, 10, 10, 10, 10, 10, 12, 14, 16, 18, 20])
w_cross = wma(rising, period=3)
s_cross = smma(rising, period=3)

# WMA should react faster to the rise and eventually cross above SMMA
# (or already be above since WMA weights recent more heavily)
cross_found = False
for i in range(3, len(rising)):
    if not np.isnan(w_cross.iloc[i]) and not np.isnan(s_cross.iloc[i]):
        if not np.isnan(w_cross.iloc[i-1]) and not np.isnan(s_cross.iloc[i-1]):
            if w_cross.iloc[i] > s_cross.iloc[i] and w_cross.iloc[i-1] <= s_cross.iloc[i-1]:
                cross_found = True
                print(f"  Cross detected at bar {i}: WMA={w_cross.iloc[i]:.2f} > SMMA={s_cross.iloc[i]:.2f}")
                break

check("WMA crosses above SMMA on rising data", cross_found,
      "WMA should cross above SMMA when prices start rising")

# ============================================
# SUMMARY
# ============================================
print(f"\n{'=' * 60}")
print(f"  RESULTS: {passed} passed, {failed} failed")
print(f"{'=' * 60}")

if failed > 0:
    sys.exit(1)
else:
    print("  ALL TESTS PASSED")
