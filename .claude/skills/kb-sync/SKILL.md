---
name: kb-sync
description: Sync knowledge-base/*.md files with latest backtest, walk-forward, or Monte Carlo results. Use when the user says "update knowledge base", "kb sync", "obsidian update", "document results", or "update docs".
user_invocable: true
argument-hint: [topic]
allowed-tools: Read, Edit, Grep, Glob
---

# /kb-sync — Knowledge Base ↔ Code Truth Sync

Keeps `knowledge-base/*.md` (Obsidian vault) aligned with current backtest/WF/MC reality so future sessions load correct context.

## Protocol

### Step 1 — Identify target file(s)
Map topic → file:
| Topic | File |
|---|---|
| Walk-forward | `25-Walk-Forward-Full-Results.md` |
| Monte Carlo | `28-P4-Monte-Carlo.md` |
| Ablation | `48-Ablation-Study-Results.md` (if exists) |
| New pair | `55-Multi-Asset-Expansion.md` |
| Parameters | `46-SBRS-Parameters-Reference.md` |
| Portfolio / live | `29-P5-P7-P8-OANDA-Portfolio.md` |
| SBRS 2.0 | `47-SBRS-2.0-Upgrade.md` |
| Root index | `00-MOC-Zeros-Requiem.md` + `CLAUDE.md` (root) |

If no clear match, Glob `knowledge-base/*.md` and ask user which to update.

### Step 2 — Read current content
Read target file. Identify the "Current Status" / "Latest Results" section.

### Step 3 — Build the delta
Compare old-vs-new. ONLY update:
- Numbers (trade count, WR, Sharpe, PF, DD, consistency)
- Date stamps (`*Last Updated: YYYY-MM-DD*`)
- Tier classification if it changed (Tier 1/2/3/4)
- Status labels (Ready for Live / Paper / Not Ready)

### Step 4 — Edit surgically
Use `Edit` with `old_string` / `new_string`. Do NOT:
- Rewrite whole sections
- Add new prose beyond what the result justifies
- Touch unrelated sections
- Add emojis unless already present in the file

### Step 5 — Cross-update
If Tier changed for a symbol:
1. Update root `CLAUDE.md` "Current Portfolio Status"
2. Update `knowledge-base/CLAUDE.md` mirror
3. Update `00-MOC-Zeros-Requiem.md` if it references the tier

### Step 6 — Report
```
═══════════════════════════════════════════════════════
  KB SYNC SUMMARY
═══════════════════════════════════════════════════════
  Files updated:
    knowledge-base/25-Walk-Forward-Full-Results.md
      - Gold 1H: 6/8 → 7/8 consistency
      - Date: 2026-04-05 → 2026-04-16
    CLAUDE.md
      - Gold moved from "Tier 1 (75%)" → "Tier 1 (88%)"
═══════════════════════════════════════════════════════
  Commit suggestion: [DOCS] Update WF results for Gold 1H (7/8)
```

## Guardrails
- NEVER invent numbers. If you don't have fresh output, run `/walk-forward` or `/monte-carlo` first.
- NEVER create a NEW knowledge-base file without user approval.
- NEVER change sacred parameter docs without a matching `/param-guard` gate.
- Preserve Obsidian `[[wikilinks]]` — do not flatten them to plain text.
