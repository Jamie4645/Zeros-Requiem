---
name: arbiter-council
description: Convene the Sovereign Quant Arbiter council. Fires domain arbiters (optionally in parallel), then invokes the Council arbiter to synthesize a one-page executive brief. Use when the user says "run the council", "council session", "arbiter council", or "convene arbiters".
user_invocable: true
argument-hint: [mode]
allowed-tools: Bash, Read, Glob, Grep, Agent
---

# /arbiter-council — Convene the Sovereign Quant Arbiters

A council session runs the 10 domain-specialist arbiters, reads their findings, and produces an executive brief for the Sovereign Quant Tactician.

## Protocol

### Step 1 — Parse mode

| Mode | Default? | Behaviour |
|---|---|---|
| `brief` | ✅ yes | Council agent alone reads all logs + findings + hypotheses and synthesizes. Token-conservative. |
| `full` |  | Fire all 9 domain arbiters in parallel, then the Council agent synthesizes. Heavy — use for weekly council. |
| `targeted:<name>` |  | Fire ONE domain arbiter (e.g. `targeted:gold`), then Council synthesizes just that. |

### Step 2 — Mandatory pre-reads (state on screen)

Before firing anything, read into the parent context:
1. `knowledge-base/arbiters/council-charter.md`
2. `knowledge-base/arbiters/shared-findings.md`
3. `knowledge-base/arbiters/next-hypotheses.md`

This anchors the parent session so it can intelligently interpret what the arbiters return.

### Step 3 — Fire arbiters (only if mode is `full` or `targeted`)

For `full`: fire 9 domain arbiters in ONE message with parallel Agent calls:
- arbiter-gold
- arbiter-indices
- arbiter-forex
- arbiter-crypto
- arbiter-regime
- arbiter-risk
- arbiter-execution
- arbiter-data
- arbiter-ablation

Each agent receives:
- Their standing instructions (from their agent file)
- A pointer to open hypotheses assigned to them
- A token budget reminder

For `targeted:<name>`: fire only that one.

### Step 4 — Synthesize

After domain arbiters return (or immediately in `brief` mode), fire `arbiter-council` with:
- Instruction to read every other arbiter's log
- Instruction to produce the executive brief in the exact format from its agent file

### Step 5 — Present brief to user

Output the Council's brief verbatim. Do NOT paraphrase — the user wants the structured format.

### Step 6 — Offer next actions

After the brief, offer the user:
- **Approve top-3 tests** — council queues them via `next-hypotheses.md` updates
- **Flag red-items for immediate handling** — escalate to direct agent invocation
- **Dismiss and re-convene tomorrow** — standard rhythm

## Hard rules

- NEVER fire the council if you just fired it <6 hours ago without a new canon entry (prevents noise loops)
- NEVER synthesise without reading the charter first — it binds the entire system
- NEVER act on a council recommendation that contradicts CLAUDE.md without user approval
- NEVER modify sacred files based on council output — council proposes, user disposes

## Why this skill exists

The council is the learning loop. Each session:
- Adds to canonical findings
- Closes old hypotheses
- Generates new ones
- Updates tier rankings

Over time, the shared brain compounds — later sessions start smarter than earlier ones. Running the council regularly IS the learning rhythm.

## Related

- `knowledge-base/65-Sovereign-Quant-Arbiters.md` — system overview
- `knowledge-base/arbiters/council-charter.md` — binding mission & hard rules
- `knowledge-base/arbiters/shared-findings.md` — canonical findings log
