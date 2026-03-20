---
tags: [tool, skill, live-trading, SBRS]
aliases: [live-status, runner-status]
related: [[CLAUDE]], [[29-P5-P7-P8-OANDA-Portfolio]], [[16-Risk-Management-Elite-System]]
---

# /live-status — SBRS Live Runner Health Check

## What It Does

A custom Claude Code **skill** (slash command) that instantly checks the health of your live SBRS paper trading system. Instead of manually reading state files and logs, just type `/live-status` in any Claude Code session.

## How It Works

When you type `/live-status`, Claude will:

1. **Read `state/sbrs_state.json`** — extracts current capital, peak equity, drawdown, open trades, pending setups, and full trade history
2. **Read latest log file in `logs/`** — checks for errors, runner frequency, anomalies
3. **Analyse trade history** — calculates win rate, average P&L, exit reason breakdown
4. **Present a structured report** — formatted dashboard with alerts for any issues
5. **Flag problems** — especially `broker_closed` exits, runner gaps, capital discrepancies

## What It Monitors

| Check | What It Catches |
|-------|----------------|
| Capital vs Peak | Drawdown alerts (>5%, >10%, >15%) |
| Runner Last Run | Stale/dead runner detection |
| Exit Reasons | `broker_closed` bugs, premature BE stops |
| Error Count | OANDA data fetch failures |
| Runner Frequency | Over-firing (should be 1x/hour) |
| Pending Setup Age | Stale setups waiting too long for retest |

## Location

```
.claude/skills/live-status/SKILL.md
```

## Usage

```
/live-status
```

No arguments needed. It reads everything from the state and log files automatically.

## Why This Exists

Manual checking of `sbrs_state.json` and log files is tedious and error-prone. This skill standardises the health check so nothing gets missed — especially silent failures like the `broker_closed` pattern that cost ~$5,443 in the first month of live trading.

## Related

- [[CLAUDE]] — SBRS strategy specification
- [[29-P5-P7-P8-OANDA-Portfolio]] — Portfolio tiers and OANDA integration
- [[16-Risk-Management-Elite-System]] — Risk management rules the runner enforces
- [[32-Tool-Auto-Test-Hook]] — Auto-testing after code changes

---

*Installed: 2026-03-20*
