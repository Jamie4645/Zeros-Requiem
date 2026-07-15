---
tags: [supervised, rebuild, real-trades, price-action, 5m-15m, active]
aliases: [Supervised Rebuild, Real Trade Analysis, 5m-15m Pivot, Current Phase]
related: [[86-SBRS-3.0-Spec-And-Build]], [[84-Realistic-Fill-No-Edge]], [[88-Audit-Harness-Index]], [[50-Smart-Money-Indicators]]
---

# 87 — Supervised Rebuild: Learning the Edge from Real Trades

> **➡️ CONTINUED in [[89-ZTT-Rebuild]]** — the user delivered 25 annotated real Gold trades; the supervised rebuild is now the **ZTT (Zero's True Trade)** clean-slate intraday-Gold strategy. 89 is the active hub.

**This is the active phase.** Mechanical codification topped out at PF 1.07
([[86-SBRS-3.0-Spec-And-Build]]) — not deployable. The conclusion: the user's edge
lives in real-time discretionary judgment (which levels are *truly* significant,
when price action is "clean", market context) that narrative rules don't reproduce.
The way to capture it is **supervised** — learn from the user's actual trades.

## Core idea
Take the user's real, annotated trades and compare, setup-by-setup, what the
algorithm does on the *same bars* versus what the user did. The **divergence on
real examples** reveals the missing judgment far better than rule-guessing.
The most valuable inputs are **losers and skips** — they define what the user's
judgment *rejects* that every mechanical version wrongly took.

## Timeframe pivot: 1H → 5m–15m
User now trades **5m–15m XAUUSD** (aligns with their 1%-trader goal). Implications:
- None of the 1H work transfers — this is a fresh regime.
- **Costs dominate** at 5m–15m: spread/slippage are a much bigger fraction of each
  move. The phantom-fill lesson is *amplified* — fills must be modelled ruthlessly.
- Data fetched per-trade-window (OANDA M5/M15) rather than the 1H canon set.

## Capability note (TradingView)
No direct TradingView connection is possible from the CLI environment (no API/MCP);
communication stays in-session. Workarounds: (1) chart screenshots — readable via
the image tool; (2) a Pine Script v5 strategy (offered, not yet built) for native
visual backtests.

## Intake format (locked with user)
Per trade, in a Word doc / folder `../analysis/real_trades/`:
- Clean chart screenshot showing price action + drawn levels (orange-circle marks).
- A typed header: `symbol, timeframe (5m/15m), direction, entry datetime (+UTC+1),
  entry/SL/TP`.
- Reasoning: which level, why significant, why TP/SL there, what made it "clean".
- Mix of winners + losers + **skips**.
Outcome (TP/SL) is reconstructed from OANDA data, not required from the user.
(The 4-trade example doc validated this format; only gap was per-trade typed
numbers + exact entry timestamp, since images are too low-res to read precisely.)

## Sample size to start
**~25 trades** (15 minimum), weighted toward variety and including losers/skips.
Rationale: hand-documented trades *teach the rules*; the 500+ statistical
validation comes from **backtesting the codified rules over years of data** — the
user does not hand-document hundreds.

## Workflow
1. User sends ~25 trades → per-trade algo-vs-user diff → identify recurring
   divergences.
2. Draft candidate rules → backtest at scale over full 5m/15m history.
3. Request a few *targeted* extra examples to settle edge cases.

## Status (2026-06)
Waiting on the user's real-trade documentation. Methodology reference:
`~/Downloads/Zeros_Trading_Methodology.docx` (17 discretionary trades) +
`~/OneDrive/Documents/Zeros True Trade 5m - 15m.docx` (live 5m–15m examples).
