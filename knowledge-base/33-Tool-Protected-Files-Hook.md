--
tags: [tooling, risk, automation]
aliases: [file-protection, sacred-files]
related: [[CLAUDE]], [[16-Risk-Management-Elite-System]], [[32-Tool-Auto-Test-Hook]]
---

# Protected Files Hook — PreToolUse

## What It Does

A Claude Code **hook** that **blocks** any attempt to edit sacred files. If Claude (or any tool) tries to modify `risk_manager.py` or `sbrs_original_parameters.py`, the edit is rejected before it happens.

## How It Works

```
Claude attempts to edit src/core/risk_manager.py
    ↓
PreToolUse hook fires BEFORE the edit executes
    ↓
Hook checks: does the file path contain a protected filename?
    ↓
YES → prints "BLOCKED: This file is protected"
    ↓
Exit code 1 → edit is PREVENTED
    ↓
Claude must ask user for explicit approval before retrying
```

## Protected Files

| File | Why It's Protected |
|------|-------------------|
| `src/core/risk_manager.py` | 5-layer risk management is locked. Changes here can blow up accounts. |
| `src/regimes/sbrs_original_parameters.py` | Reference copy of sacred SBRS parameters from real trading. |

## Why It Matters

From [[CLAUDE|the strategy spec]]:
> *"NEVER TOUCH risk_manager.py without explicit approval"*
> *"If I catch you optimizing WMA_PERIOD, SMMA_PERIOD, or SWING_LOOKBACK, we have a problem."*

These aren't suggestions — they're hard rules. The difference between a hook and a CLAUDE.md instruction:

| | CLAUDE.md Rule | PreToolUse Hook |
|---|---|---|
| Enforcement | Advisory (Claude tries to follow) | Deterministic (code prevents it) |
| Can be forgotten | Yes, especially in long sessions | No, runs every time |
| Context rot | Degrades as context fills | Immune to context |
| Bypass | Claude might "improve" things | Requires user intervention |

## Configuration

Located in `.claude/settings.local.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "command": "bash -c '...checks if file matches protected list...'",
        "timeout": 5000,
        "description": "Block edits to sacred files"
      }
    ]
  }
}
```

### Adding More Protected Files

To protect additional files, edit the grep pattern in the hook command. Add filenames separated by `|`:

```
grep -qE "(risk_manager\\.py|sbrs_original_parameters\\.py|NEW_FILE\\.py)"
```

## What It Doesn't Do

- Doesn't protect files from being **read** (reading is always allowed)
- Doesn't protect the CLAUDE.md file itself (that should remain editable)
- Doesn't prevent creating **new** files with similar names
- Doesn't block git operations (checkout, reset, etc.)

## Related

- [[CLAUDE]] — Sacred parameters and file modification rules
- [[16-Risk-Management-Elite-System]] — The risk management system being protected
- [[32-Tool-Auto-Test-Hook]] — Companion hook for testing after changes
- [[35-Tool-GSD2]] — GSD-2 also respects protected files via preferences

---

*Installed: 2026-03-20*
