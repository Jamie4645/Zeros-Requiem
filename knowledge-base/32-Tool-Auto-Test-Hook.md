--
tags: [tooling, automation]
aliases: [auto-test, post-tool-hook]
related: [[CLAUDE]], [[31-Tool-Backtest]], [[33-Tool-Protected-Files-Hook]]
---

# Auto-Test Hook — PostToolUse

## What It Does

A Claude Code **hook** that automatically runs `tests/quick_test.py` every time Claude edits or creates a Python file inside `src/`. No more forgetting to test — it's enforced at the infrastructure level.

## How It Works

```
Claude edits src/regimes/sbrs_gold.py
    ↓
PostToolUse hook fires (matcher: Edit|Write)
    ↓
Hook checks: is the file in src/ and a .py file?
    ↓
YES → runs: python -m pytest tests/quick_test.py --tb=short -q
    ↓
Results shown to Claude (and user) automatically
    ↓
If tests FAIL → Claude sees the failure and can fix immediately
```

## Why It Matters

From [[CLAUDE|the strategy spec]]:
> *"Test with `py -m tests.quick_test` after every change"*

This rule was previously **advisory** — Claude was told to test but could forget. Now it's **deterministic**. The hook runs every single time, no exceptions.

For a trading system, untested code changes are dangerous. A single bug in entry logic or stop-loss placement can silently drain capital (see: the `broker_closed` pattern that lost ~$5,443 in live trading).

## Configuration

Located in `.claude/settings.local.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "command": "bash -c '...checks if file is src/*.py, runs pytest...'",
        "timeout": 60000,
        "description": "Auto-run quick tests after editing src/ Python files"
      }
    ]
  }
}
```

### Key Settings
- **matcher**: `Edit|Write` — fires on file edits and new file creation
- **timeout**: 60 seconds — enough for the test suite but prevents infinite loops
- **scope**: Only triggers for `src/**/*.py` files — won't fire on docs, configs, or tests themselves

## What It Doesn't Do

- Doesn't run on test file changes (avoids infinite loops)
- Doesn't run on knowledge-base or documentation changes
- Doesn't run the full walk-forward suite (use [[31-Tool-Backtest|/backtest]] for that)
- Doesn't block the edit if tests fail (it reports, doesn't prevent)

## Related

- [[CLAUDE]] — Testing requirements and quality standards
- [[31-Tool-Backtest]] — Full backtest reporting skill
- [[33-Tool-Protected-Files-Hook]] — Companion hook that blocks sacred file edits
- [[35-Tool-GSD2]] — GSD-2 also runs verification after execution phases

---

*Installed: 2026-03-20*
