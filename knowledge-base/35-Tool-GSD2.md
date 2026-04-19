--
tags: [tooling, automation]
aliases: [GSD, GSD-2, get-shit-done]
related: [[CLAUDE]], [[32-Tool-Auto-Test-Hook]], [[31-Tool-Backtest]]
---

# GSD-2 — Get Shit Done

## What It Does

GSD-2 is a **meta-prompting and spec-driven development system** for Claude Code. It solves the biggest problem with AI-assisted coding on complex projects: **context rot** — the quality degradation that happens as conversations get long and Claude loses track of the big picture.

GSD structures all work into a hierarchy:
- **Milestone** — a shippable version (4-10 slices)
- **Slice** — one demoable vertical capability (1-7 tasks)
- **Task** — one context-window-sized unit of work

Each task runs in a fresh context window, so Claude never loses track.

## Key Commands

| Command          | What It Does                   | When to Use                                |
| ---------------- | ------------------------------ | ------------------------------------------ |
| `/gsd`           | Step-by-step execution         | Default — review each step                 |
| `/gsd auto`      | Fully autonomous mode          | Grinding through known-good work           |
| `/gsd next`      | Advance one step               | After reviewing a completed step           |
| `/gsd quick`     | Execute without planning       | Small, obvious tasks                       |
| `/gsd stop`      | Halt autonomous mode           | When something looks wrong                 |
| `/gsd discuss`   | Architecture conversation      | Safe during auto — won't pollute execution |
| `/gsd status`    | Progress dashboard             | Check where you are                        |
| `/gsd steer`     | Modify plans mid-execution     | When backtest results change priorities    |
| `/gsd doctor`    | Health check with auto-fixes   | When things feel broken                    |
| `/gsd forensics` | Investigate auto-mode failures | Post-mortem on failed runs                 |
| `/gsd logs`      | Activity and metrics           | Review token usage and progress            |

## How It Fits Zeros Requiem

### Example: "Fix the broker_closed bug"
Without GSD:
- Start investigating → context fills up → lose track of hypotheses → suggest wrong fix → waste tokens

With GSD:
```
Milestone: Fix SBRS Live Execution
├── Slice 1: Diagnose broker_closed exits
│   ├── Task 1: Read oanda_executor.py order placement logic
│   ├── Task 2: Trace SL/TP values from state.json trades
│   └── Task 3: Compare intended vs actual OANDA orders
├── Slice 2: Implement fix
│   ├── Task 1: Fix SL placement logic
│   └── Task 2: Add order confirmation logging
└── Slice 3: Validate
    ├── Task 1: Run backtest with fix
    └── Task 2: Paper trade 24h and verify
```

Each task gets a fresh context with only what it needs.

### Example: "Add S&P 500 to SBRS"
```
Milestone: SBRS Index Extension
├── Slice 1: Research data availability (IBKR/OANDA)
├── Slice 2: Implement SPY regime in sbrs_indices.py
├── Slice 3: Walk-forward validate (5Y+, 8 windows)
└── Slice 4: Monte Carlo + portfolio integration
```

## Configuration

### Installation
```bash
npm install -g gsd-pi@latest
```

### Project Preferences
Located in `.gsd/preferences.md`:
- Verification command: `python -m pytest tests/quick_test.py`
- Protected files list (mirrors [[33-Tool-Protected-Files-Hook]])
- Commit style: `[SBRS]`, `[SCAF]`, `[engine]` prefixes
- Model preferences per phase

## Key Features for Trading Projects

| Feature | Why It Matters |
|---------|---------------|
| **Fresh context per task** | No context rot during long debugging sessions |
| **Verification after execution** | Auto-runs tests (like [[32-Tool-Auto-Test-Hook]]) |
| **Cost tracking** | See exactly how many tokens each investigation costs |
| **Branch-per-slice** | Git isolation — experiments don't pollute main |
| **Crash recovery** | Picks up where it left off if session dies |
| **Dashboard** | `Ctrl+Alt+G` for real-time progress |

## When to Use GSD vs Regular Claude Code

| Situation | Use |
|-----------|-----|
| Quick question about code | Regular Claude Code |
| Single file edit | Regular Claude Code |
| `/live-status` or `/backtest` | Regular Claude Code |
| Multi-file investigation | **GSD** |
| New feature spanning 3+ files | **GSD** |
| Walk-forward analysis + interpretation | **GSD** |
| Bug requiring root cause analysis | **GSD** |

## Related

- [[CLAUDE]] — Strategy spec and development rules GSD enforces
- [[32-Tool-Auto-Test-Hook]] — Auto-testing (GSD also verifies)
- [[33-Tool-Protected-Files-Hook]] — File protection (GSD respects via preferences)
- [[34-Tool-Sequential-Thinking-MCP]] — Deep reasoning (complementary to GSD's structure)
- [[31-Tool-Backtest]] — Backtest reporting (can be used within GSD tasks)

---

*Installed: 2026-03-20*
