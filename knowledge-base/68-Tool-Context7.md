---
tags: [tooling, automation, documentation]
aliases: [context7, upstash-docs, live-docs-mcp]
related: [[CLAUDE]], [[34-Tool-Sequential-Thinking-MCP]], [[69-Tool-Superpowers]], [[35-Tool-GSD2]]
---

# Context7 — Live Documentation MCP / Plugin

## What It Does

Context7 (by Upstash) is a Claude Code plugin that pulls **up-to-date, version-specific documentation and code examples** from source repositories directly into the conversation context. It eliminates the "hallucinated API" problem — instead of Claude guessing what a library's function signature looks like from training data, Context7 fetches the current docs on demand.

Supports:
- npm packages
- Python packages (PyPI)
- GitHub repos (tags / branches / commits)

## How It Works

- Plugin registers an MCP server at `plugin:context7:context7` (command: `npx -y @upstash/context7-mcp`)
- Exposes tools the assistant can call to resolve a library reference and fetch the latest docs
- Runs a background docs-researcher agent so the main context stays lean (docs don't bloat the parent session)
- Also available as a slash command (e.g. `/context7:docs`) for manual lookups

## Install & Verify

Installed on **2026-04-17** from the official marketplace:

```bash
claude plugin install context7
# ✔ Successfully installed plugin: context7@claude-plugins-official (scope: user)
```

Verify:

```bash
claude plugin list        # context7@claude-plugins-official — enabled
claude mcp list           # plugin:context7:context7: npx -y @upstash/context7-mcp — ✓ Connected
```

### Scope
- **User scope** — enabled across every Claude Code project on this machine, not just Zeros Requiem.

### API key
Context7's backend parsing/crawling engines are private. Setup may prompt for OAuth / an Upstash API key on first use. If it does, save the key in the OS keychain (not in `.env`) — the plugin handles it transparently.

## Project-Specific Usage in Zeros Requiem

The project pulls heavily from third-party SDKs whose docs drift between versions. Context7 is most valuable for:

| Area | Why Context7 helps |
|---|---|
| **OANDA SDK** (`oandapyV20`) | Endpoints rename between minor versions — live docs prevent broken executor calls |
| **IBKR / `ib_insync`** | `util.df()` schema, contract qualification rules, historical-bar pagination quirks |
| **VectorBT** | API surface is huge and partially migrated toward VectorBT Pro — easy to hallucinate signatures |
| **pandas / numpy edge cases** | e.g., `tz_convert`/`tz_localize` (the exact bug fixed in Round 5's `is_session_blocked` patch) |
| **Binance / CCXT** | Crypto data fetcher evolution across exchanges |
| **mcp, claude-agent-sdk** | When building new Sovereign Quant Arbiters or custom MCP servers |

### When to invoke
- Before writing any code against a third-party API the model might "remember incorrectly"
- When a traceback mentions a symbol that should exist but doesn't (likely API rename)
- When upgrading a dependency — confirm the new contract before touching executor/live code

### When NOT to invoke
- Pure SBRS logic — the authoritative spec is [[CLAUDE|root CLAUDE.md]], not external docs
- Questions about project files — use `Read`/`Grep` directly

## Adaptation Notes

- Context7 **complements**, does not replace, the project's internal knowledge base. Internal strategy invariants (WMA>SMMA bullish, FVG weight 0.5, etc.) live in [[CLAUDE]] and the KB — Context7 is strictly for **external library surface area**.
- Does not conflict with [[69-Tool-Superpowers|Superpowers]] or [[34-Tool-Sequential-Thinking-MCP|Sequential Thinking]] — they occupy different layers.
- Token overhead: low. The docs-researcher agent runs on a cheaper model and only materialises relevant excerpts in the parent context.

## Gotchas

- Requires internet access at query time (docs are fetched live, not cached long-term)
- First use may trigger an OAuth flow — do **not** paste the resulting token into any project file
- If Context7's backend is down, Claude will fall back to training-data guesses — treat those as provisional until rechecked

## Related

- [[69-Tool-Superpowers]] — Methodology plugin (installed same day)
- [[34-Tool-Sequential-Thinking-MCP]] — Structured-reasoning MCP (installed same day)
- [[07-Guide-Python-Broker-APIs]] — The broker SDKs Context7 most often resolves
- [[45-Data-Pipeline]] — Data fetcher hot-path where API drift causes bugs

---

*Installed: 2026-04-17*
