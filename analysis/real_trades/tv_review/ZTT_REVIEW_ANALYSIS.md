# ZTT Trader Review Analysis — 60 Trades (2026-05-11 to 2026-06-09)

## OVERVIEW
- **Takes:** 30
- **Skips:** 30
- **Data structure:** CSV with entry_price, stop_loss, take_profit, decision, reason, notes

---

## 1. EXPLICIT STOP-LOSS PRICES STATED BY TRADER

The trader explicitly stated his preferred SL prices in **only 4 out of 60 trades**:

### Trade #22 (SHORT, TAKEN)
- Trader SL: **4564.518**
- Algo SL: 4582.091
- Entry: 4545.945
- SL Distance: 18.573 abs | **0.409% of entry**
- Quote: *"Entry was great as you waited for price to break a support level then came back to retest that level and as soon as it came back you entered which I really respect HOWEVER again your stop and take profits are too high and too low and this was actually a trade I entered and the stop loss was 4564.518 and the take profit was 4513.041 which is ideal"*

### Trade #31 (LONG, TAKEN)
- Trader SL: **4448.000**
- Algo SL: 4413.353
- Entry: 4468.000
- SL Distance: 20.000 abs | **0.448% of entry**
- Quote: *"good trades but what is killing us the the expected % in price so in this scenario I would have placed my stop loss below the newly respected support level so my stop loss would be 4448 and take profit would be 3x that"*

### Trade #36 (SHORT, TAKEN)
- Trader SL: **4510.994**
- Algo SL: 4527.597
- Entry: 4494.235
- SL Distance: 16.759 abs | **0.373% of entry**
- Quote: *"not a bad trade but the wide stop loss and take profit keeps allowing us to lose money on these trades so like I said before in a scenario like this where price has broke a respected support line and come back to retest it turning it into a resistance we can place stop loss there OR we place it on the most recent high low that was formed which would have put our stop loss at 4510.994"*

### Trade #58 (SHORT, TAKEN)
- Trader SL: **4286.754**
- Algo SL: 4369.445
- Entry: 4272.460
- SL Distance: 14.294 abs | **0.335% of entry**
- Quote: *"very good entry so price break the 4280.375 level which was the actually previous lower low level then came back to retest which makes that price a good resistant level to respect however the stop loss and take profit are too big in expectations as since we are now respecting a resistant level the short position I would have entered would have been stop loss placed at 4286.754"*

**KEY PATTERN:** All 4 explicit SL statements are **TIGHTER** than algo's SL (by 14–18 points). He places stops **closer to entry** to "respect significant levels" (previous high/low, level touches, resistance turned support).

---

## 2. EXPLICIT TAKE-PROFIT PRICES STATED BY TRADER

The trader explicitly stated his preferred TP prices in **only 2 out of 60 trades**:

### Trade #22 (SHORT, TAKEN)
- Trader TP: **4513.041**
- Algo TP: 4437.507
- Entry: 4545.945
- TP Distance: 32.904 abs | **0.724% of entry**
- **Implied R:R** (vs his SL 4564.518): (4545.945 − 4513.041) / (4564.518 − 4545.945) = **1.73** (NOT 3.0)
- Quote: *"the stop loss was 4564.518 and the take profit was 4513.041 which is ideal as I've said before the range does not need to be so wide"*

### Trade #58 (SHORT, TAKEN)
- Trader TP: **4212.520**
- Algo TP: 3981.506
- Entry: 4272.460
- TP Distance: 59.940 abs | **1.403% of entry**
- **Implied R:R** (vs his SL 4286.754): (4272.460 − 4212.520) / (4286.754 − 4272.460) = **4.45** (tight SL inflates ratio)
- Quote: *"the short position I would have entered would have been stop loss placed at 4286.754 and take profit placed at 4212.520"*

**KEY PATTERN:** Both explicit TPs are **SMALLER** in absolute move than algo's TP, resulting in more "realistic" % moves (0.7%–1.4% vs algo's typical 2%–7%). His own discretionary trades accept **R:R as low as 1.73**, well below the algo's 3.0 target.

---

## 3. R:R ACCEPTABILITY — EXPLICIT STATEMENTS

### Empirical Fact
- **All 30 taken trades** use R:R = 3.0 (the algo's target)
- **NO trades with R:R ≤ 1.0** were taken
- **HOWEVER:** The trader **repeatedly criticizes** the R:R as too high despite taking the trades

### Quoted Thresholds on % Movement

**Trade #1 (SKIP):**
> "1% price profit which is realistic as generally speaking when entering trades you should not be especially price to move more than 2% up and 2% down per trade"

**→ TARGET:** ~1% per trade is "realistic", max 2% in either direction

**Trade #20 (SKIP):**
> "we should try to keep it below 2% [for take profit]"

**→ MAX TP:** 2% price movement

**Trade #22 (TAKE):**
> "a price movement of -1.04% which is the kind of trade I would make"

**→ ACCEPTS:** 1.04% TP move as ideal

**Trade #2 (TAKE):**
> "the take profit is too far up as that would be a 2.25% growth in price which is quite the movement"

**→ BORDERLINE:** Accepts 2.25% but comments it's "quite the movement"

### Rejected % Movements
- **3.0%:** "2.4% is very optimistic"
- **4.0%:** "4% price increase which I would not try"
- **4.27%:** "extreme bullish movement"
- **5.0%:** "toooo wideeee!!! thats nearly 5% growth in price which I do not see"
- **7.0%:** "we will not be making profits with such unrealistic movement in price which here is -7%"

### Consensus
He targets **1–2% per trade** in low timeframe (10m/15m). Algo's 3.0 R:R often maps to 2.5–7% total TP moves on this timeframe, which he considers unrealistic for actual execution.

---

## 4. DOES HE SAY THE ALGO MISSED GOOD TRADES OR IS TOO RESTRICTIVE?

**SHORT ANSWER:** No. He never says the algo is too restrictive.

Instead, he says:
1. The algo is **MAKING PREDICTIONS** (entering before break/retest confirms)
2. The algo's SL/TP ranges are **UNREALISTICALLY WIDE**
3. The algo should be **MORE selective** on "significant" levels

### Positive Comments on Skipped Trades (where algo was too loose):

**Trade #8 (SKIP):**
> "same as the trade before price is not really moving and its not showing momentum but I can respect the fact that you entered when price broke the previous lower high so I can see as to why the algo made this trade"

**→** Algo's logic was sensible, but price lacked momentum

**Trade #27 (SKIP):**
> "there is no edge here price has not broken any respected level nor has it retested any respected or significant level but it is in a downtrend so I can respect looking for short positions"

**→** Accepts the SHORT bias but requires a break/retest first

**Trade #34 (SKIP, FALSE BREAKOUT):**
> "again you are making a prediction that price will break the resistant level and come back down to rest and another thing I need to make clear WE DO NOT TRADE FALSE BREAKOUTS they are misleading so ignore then"

**→** Clear rule violation

### Overall Assessment
The trader is **selective but not rejecting** the algo as broken. He wants:
- Tighter entry rules (mandatory break+retest, no prediction)
- Narrower SL/TP ranges (1–2% instead of 2–7%)

---

## 5. SKIP REASONS — CATEGORIZED (30 SKIPS)

### Primary Reason Categories

#### 1. R:R TOO WIDE / % MOVEMENT UNREALISTIC (11 trades)
- **Trades:** #3, 11, 12, 13, 20, 27, 28, 52, 53, 54, 55
- **Pattern:** Algo's TP implies >2% price movement, trader considers unrealistic
- **Quote (Trade #3):** *"your stop loss and take profit are too wide! 4.27% growth in price is extreme bullish movement which we have no signs of happening"*
- **Quote (Trade #20):** *"we should try to keep it below 2%"*

#### 2. CONSOLIDATION / NO MOMENTUM / CHOPPY (6 trades)
- **Trades:** #7, 8, 16, 17, 25, 26
- **Pattern:** Price is range-bound, no directional momentum
- **Quote (Trade #7):** *"price is not really moving there is no momentum its just stuck together and looking for a breakout and retest in such conditions is pointless"*
- **Quote (Trade #16):** *"price is basically in a range of consolidation and not exactly respecting any level currently so until we see that price is starting to respect some levels its not great to trade this period"*

#### 3. NO BREAK/RETEST (7 trades)
- **Trades:** #5, 9, 13, 37, 38, 39, 40
- **Pattern:** Algo enters expecting a break and retest, but price hasn't yet broken
- **Quote (Trade #5):** *"unless price breaks that and retest I dont see a trade"*
- **Quote (Trade #37):** *"this trade was entered at a level that was touched and did not break so unless price breaks the price that was touched on 1st June at 00:50 am then we would not be entering this trade"*

#### 4. NO RESPECTED LEVEL / NO EDGE (5 trades)
- **Trades:** #18, 19, 27, 29, 30
- **Pattern:** Price not respecting any level, no clear structure to trade
- **Quote (Trade #18):** *"price is not respecting any level currently and on top of that there realistically is no real edge here"*
- **Quote (Trade #29):** *"there is no edge here no significant level or respected support or resistance and no retest either so I would not enter this trade"*

#### 5. PREDICTION / PREMATURE ENTRY (4 trades)
- **Trades:** #4, 20, 21, 34
- **Pattern:** Trader criticizes algo for predicting price will break/retest before it happens
- **Quote (Trade #4):** *"you're trade for price to break a resistance level as normally I would wait for price to break that resistance level before we enter"*
- **Quote (Trade #20):** *"we do not predict price to break a strong resistance what we do is allow for the break to happen then wait for price to come back"*

#### 6. FALSE BREAKOUT / LONG WICKS (1 trade)
- **Trade:** #34
- **Quote:** *"WE DO NOT TRADE FALSE BREAKOUTS they are misleading so ignore then"*

#### 7. OTHER (5 trades)
- **Trades:** #1, 6, 15, 56, 57
- **Reasons:** Too late (already in similar trade), need stronger confirmation
- **Quote (Trade #15):** *"too late for a long trade as that would have happened inbetween trade #14 and '15"*
- **Quote (Trade #56):** *"for a trade like this I would want price to break a more significant lower high for extra confirmation"*

### Distribution Summary
| Category | Count | % |
|----------|-------|-----|
| R:R Too Wide / % Unrealistic | 11 | 37% |
| Consolidation / No Momentum | 6 | 20% |
| No Break/Retest | 7 | 23% |
| No Respected Level / No Edge | 5 | 17% |
| Prediction / Premature Entry | 4 | 13% |
| FALSE BREAKOUT | 1 | 3% |
| Other | 5 | 17% |

**KEY INSIGHT:** The trader's **most common skip reason** (37%) is that algo's % movements are **UNREALISTIC**. Second is consolidation/chop (20%). Together they account for **57% of all skips**.

---

## SYNTHESIS: EXIT RULES & SELECTIVITY

### Explicit Exit SL Rules (inferred from comments)
1. Place SL at or just below a "significant level" (previous high/low, level touched 2+ times)
2. Allow "room to move" — avoid placing SL on the exact level itself
3. **SL distance typical: 0.3–0.45% of entry price**
4. Never place SL on a "short-term" level — wait for 3+ touches or structural breaks
5. Use "most recent high/low" or "respected support/resistance" as anchor, not just ATR buffer

### Explicit Exit TP Rules (inferred from comments)
1. **Target 1–2% price movement per trade** as "realistic"
2. **Max 2% for most scenarios** on 10m/15m timeframe
3. Accept wider % only if trade has an obvious structural target (e.g., previous day high/low)
4. Use "high/low of day/week" as TP reference, not just R:R multiplier
5. Accept **R:R as low as 1.7–2.0** if entry is pristine (break + clean retest)

### Selectivity Assessment
- **NOT too restrictive:** Takes 50% of algo signals (30/60)
- **VERY particular on entry quality:** Skips if:
  - Price hasn't actually broken a level yet (prediction)
  - Price is choppy/consolidating without momentum
  - TP would require >2% unrealistic movement
  - No "significant" level to reference (2+ touches, high/low of day/week)
- **Accepts false positives over false negatives:** Will take trades with imperfect momentum if the entry structure (break+retest) is pristine

### Final Verdict
The trader is **NOT filtering out too many trades**. He's filtering out **UNREALISTIC trades** (2–7% TP moves on 10m timeframe). He views the algo as **too AGGRESSIVE on SL/TP width**, not too strict on entry count.

---

## SUMMARY TABLE: Explicit SL/TP Statements

| Trade | Decision | SL (trader) | SL (algo) | SL % entry | TP (trader) | TP (algo) | TP % entry | Implied R:R | Key Issue |
|-------|----------|-------------|-----------|-----------|-------------|-----------|-----------|-----------|-----------|
| #22 | TAKE | 4564.518 | 4582.091 | 0.409% | 4513.041 | 4437.507 | 0.724% | **1.73** | "ideal" ratio (much tighter than algo's 3.0) |
| #31 | TAKE | 4448.000 | 4413.353 | 0.448% | — | 4631.942 | — | — | "killing us the expected %"; wants tighter TP |
| #36 | TAKE | 4510.994 | 4527.597 | 0.373% | — | 4394.148 | — | — | "keeps allowing us to lose money" on wide ranges |
| #58 | TAKE | 4286.754 | 4369.445 | 0.335% | 4212.520 | 3981.506 | 1.403% | **4.45** | "too big in expectations"; prefers tight SL |

---

## Evidence Files
- Source CSV: `analysis/real_trades/tv_review/ztt_review_2026-05-11_to_2026-06-09_base.csv`
- This analysis: `analysis/real_trades/tv_review/ZTT_REVIEW_ANALYSIS.md`
