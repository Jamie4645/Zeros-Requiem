--
tags: [tool, configuration, claude-code]
aliases: [CLAUDE-md, autoload]
related: [[CLAUDE]], [[00-MOC-Zeros-Requiem]]
---

# CLAUDE.md Auto-Loading

## What It Does

By renaming `claude.md` → `CLAUDE.md` (uppercase), Claude Code **automatically loads the file at the start of every conversation**. This means every new session starts with full knowledge of:

- SBRS strategy spec and sacred parameters
- Entry/exit logic (5-step process)
- Elite benchmarks and current scores
- File modification rules
- Communication protocols
- Known issues and fixes

## Why It Matters

Previously, the file was `claude.md` (lowercase). Claude Code only auto-loads `CLAUDE.md` (uppercase). Every new session required either:
- Manually asking Claude to read the file
- Claude stumbling through the codebase without context
- Repeating instructions already documented

With auto-loading, zero setup is needed. Open Claude Code, start working.

## What Gets Auto-Loaded

The [[CLAUDE]] file contains:

1. **Identity** — Sovereign Quant-Tactician persona and philosophy
2. **Mark Douglas fundamentals** — 5 Fundamental Truths, probabilistic thinking
3. **SBRS specification** — Sacred parameters, entry logic, exit conditions
4. **Architecture** — Project structure and file modification rules
5. **Benchmarks** — Elite targets (Sharpe ≥1.5, PF ≥1.5, etc.)
6. **Portfolio status** — What's validated, testing, and rejected
7. **Known issues** — Direction bug, shorts underperformance, session filter
8. **Next steps** — Priority-ordered roadmap

## Configuration

No configuration needed. Just having a file named `CLAUDE.md` in the project root is sufficient. Claude Code detects it automatically.

### File Location
```
C:/Users/jamie/OneDrive/Documents/Jamie VS Code/Git/Zeros Requiem/CLAUDE.md
```

### How Auto-Loading Works
```
User opens Claude Code in project directory
    ↓
Claude Code scans for CLAUDE.md in project root
    ↓
Found → loads entire file into system context
    ↓
Every response is informed by strategy spec
```

## Related

- [[CLAUDE]] — The actual strategy spec file
- [[00-MOC-Zeros-Requiem]] — Map of Content linking everything
- [[35-Tool-GSD2]] — GSD-2 also reads CLAUDE.md for project context

---

*Installed: 2026-03-20*
