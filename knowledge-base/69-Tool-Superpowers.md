---
tags: [tooling, methodology, workflow]
aliases: [superpowers, obra-superpowers, dev-methodology-plugin]
related: [[CLAUDE]], [[35-Tool-GSD2]], [[34-Tool-Sequential-Thinking-MCP]], [[68-Tool-Context7]], [[65-Sovereign-Quant-Arbiters]]
---

# Superpowers — Disciplined Dev Methodology Plugin

## What It Does

Superpowers (by Jesse Vincent / obra) is a Claude Code plugin that installs a **skills library enforcing disciplined software-development workflows** on the assistant. Rather than providing new data (like [[68-Tool-Context7|Context7]]) or a new reasoning primitive (like [[34-Tool-Sequential-Thinking-MCP|Sequential Thinking]]), it reshapes **how** Claude approaches a task.

Core methodologies it installs:

| Skill cluster | What it enforces |
|---|---|
| **TDD / Red-Green-Refactor** | Write the failing test first, make it pass, then clean up — no "I'll add tests later" |
| **Four-phase debugging** | Reproduce → isolate → root-cause → fix. No symptom patching. |
| **Socratic brainstorming** | Forces explicit hypothesis framing before proposing solutions |
| **Subagent-driven code review** | Spawn a review subagent before declaring work done |
| **Composable skill authoring** | Templates for writing new project-specific skills cleanly |

## Install & Verify

Installed on **2026-04-17** from the official marketplace:

```bash
claude plugin install superpowers
# ✔ Successfully installed plugin: superpowers@claude-plugins-official (scope: user)
```

Verify:

```bash
claude plugin list
# superpowers@claude-plugins-official — Version: 5.0.7 — Status: enabled
```

### Scope
- **User scope** — active on every Claude Code project on this machine.

## Project-Specific Usage in Zeros Requiem

Zeros Requiem already has a strong disciplined workflow through [[35-Tool-GSD2|GSD2]], [[65-Sovereign-Quant-Arbiters|the Sovereign Quant Arbiter council]], and the `bug-hunter` / `strategy-validator` subagents. Superpowers layers **on top** of that, not in place of it.

| Scenario | Which Superpowers skill maps to it |
|---|---|
| Fixing a live-trading bug (e.g., `broker_closed`, SL placement) | Four-phase debugging — forces reproduction and root-cause before patch |
| Adding a new SBRS filter or indicator (ATR regime, volatility percentile) | TDD — write the failing unit test first before touching `sbrs_v2.py` |
| Implementing a new Sovereign Quant Arbiter or skill | Composable skill-authoring template |
| Declaring a Round N council validation "done" | Subagent-driven review pass before merge |
| Deciding whether a new parameter change is worth it | Socratic brainstorming — forces explicit success criteria upfront |

### How it interacts with the Sovereign Quant Arbiters

The Arbiter council ([[65-Sovereign-Quant-Arbiters]]) is **domain-specialist** — Gold, Forex, Indices, Risk, Execution, etc. Superpowers is **methodology-specialist** — TDD, debugging, review. They compose cleanly:

1. Council proposes a hypothesis (e.g., "session filter OFF for Gold")
2. Superpowers TDD skill writes the test that codifies success (WF ≥ 75%, PF ≥ 1.5)
3. Four-phase debugging skill investigates any failure
4. Review subagent double-checks the change before it's declared merged
5. Council re-convenes next cycle with the validated result in `shared-findings.md`

## Gotchas & Trade-offs

- **Token overhead.** Superpowers enforces multi-phase workflows, which means more intermediate output per task. Fine for strategy-critical code (engine, risk_manager, sbrs_v2); overkill for one-line tweaks — feel free to opt out on trivial edits.
- **Potential conflict with GSD2.** Both frameworks prescribe "how to approach work." In practice they overlap (both favour structured execution), but if guidance diverges on a specific task, **GSD2 wins** — it's been tuned for this project for months. Superpowers fills gaps GSD2 doesn't cover (TDD discipline, systematic debugging).
- **"Best for long-lived codebases"** — which Zeros Requiem is. 10+ years of historical data, 4 validated strategies, live-money paths. The per-task overhead pays off.
- **Skill autoloading.** Superpowers adds slash commands under `/superpowers/*` or similar prefix. Use `/help` or `claude plugin list` to enumerate once active.

## Adaptation into the Project

1. **Engine/risk changes must use the TDD skill.** `src/core/engine.py` and `src/core/risk_manager.py` are in the "ask-first / never-touch" tier per [[CLAUDE|CLAUDE.md]]. Superpowers TDD adds a second gate: a failing test must exist before any edit lands.
2. **Live-bug triage runs through four-phase debugging.** The existing `bug-hunter` agent already mirrors this; Superpowers reinforces it from the main-session side so one-off quick-fixes don't slip through.
3. **New skills/arbiters get authored via the Superpowers template.** Keeps the `arbiters/` folder style consistent.
4. **Before Merging a Round-N validation** (like Round 5), the review subagent runs as a final pass.

## When NOT to Use

- Exploratory conversations (just thinking out loud)
- Documentation edits (this file, for example)
- Obsidian-only work that never touches Python

## Related

- [[68-Tool-Context7]] — Live docs MCP, companion install
- [[34-Tool-Sequential-Thinking-MCP]] — Reasoning primitive, companion install
- [[35-Tool-GSD2]] — Existing task-management framework (complements Superpowers)
- [[65-Sovereign-Quant-Arbiters]] — Domain-specialist agent council (orthogonal)
- [[CLAUDE]] — Master strategy spec with file-modification tier rules

---

*Installed: 2026-04-17*
