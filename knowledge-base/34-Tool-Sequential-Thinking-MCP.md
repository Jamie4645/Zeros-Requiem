--
tags: [tooling, automation]
aliases: [sequential-thinking, MCP-server]
related: [[CLAUDE]], [[35-Tool-GSD2]], [[31-Tool-Backtest]]
---

# Sequential Thinking MCP Server

## What It Does

An MCP (Model Context Protocol) server that gives Claude access to a **structured reasoning tool** for complex, multi-step problems. Instead of trying to hold an entire debugging chain in a single response, Claude can break problems into explicit sequential steps, revise earlier assumptions, and maintain context across long reasoning chains.

## When It's Useful

| Scenario | Example in Zeros Requiem |
|----------|------------------------|
| **Complex debugging** | "Why are 11/12 live trades exiting as `broker_closed`?" — requires tracing through runner → executor → OANDA API → order placement → SL logic |
| **Multi-hypothesis analysis** | "Is the Sharpe degradation from data quality, parameter drift, or regime change?" |
| **Architecture decisions** | "Should we merge SCAF and SBRS into one framework or keep them separate?" |
| **Walk-forward interpretation** | "Why did windows 3 and 7 fail while others passed?" |

## How It Works

The MCP server provides Claude with a `sequential_thinking` tool that:

1. **Structures thought into numbered steps** — each step builds on previous ones
2. **Allows revision** — can go back and update earlier steps when new evidence appears
3. **Maintains context** — doesn't lose track of the problem across long chains
4. **Separates reasoning from action** — thinks through the problem before suggesting changes

This is especially valuable for trading system debugging where a wrong conclusion can lead to parameter changes that destroy edge.

## Configuration

Canonical source: `@modelcontextprotocol/server-sequential-thinking` (npm). Reinstalled on **2026-04-17** using the Claude Code MCP CLI:

```bash
claude mcp add sequential-thinking -- npx -y @modelcontextprotocol/server-sequential-thinking
```

This writes to `C:\Users\jamie\.claude.json` at the project scope. Verify with:

```bash
claude mcp list
# sequential-thinking: npx -y @modelcontextprotocol/server-sequential-thinking - ✓ Connected
```

### Requirements
- Node.js installed (for `npx`)
- Internet access on first run (downloads the package)
- After first run, cached locally

### Project-specific usage in Zeros Requiem

Use the `sequential_thinking` MCP tool in these SBRS scenarios:

| Trigger | Why sequential thinking helps |
|---|---|
| Walk-forward window failure ("Why did W7 GBPUSD collapse?") | Forces explicit hypothesis → evidence → revision chain, preventing premature parameter tweaks |
| Cross-arbiter synthesis disagreements | When arbiter-forex says one thing and arbiter-execution another, sequential thinking reconciles the contradiction |
| Ablation artefact diagnosis (e.g., MA-convention PF 5.23 chimera) | Breaks the "too-good-to-be-true" result into testable sub-steps |
| Live-trading bug root cause | Complements [[65-Sovereign-Quant-Arbiters\|bug-hunter agent]] by structuring the hypothesis tree |

## When NOT to Use

- Simple, single-step tasks ("add a print statement")
- Standard backtests (use [[31-Tool-Backtest|/backtest]] instead)
- Quick status checks (use [[30-Tool-Live-Status|/live-status]] instead)

It's designed for the hard problems — the ones where you'd normally spend hours staring at code trying to figure out what's wrong.

## Related

- [[CLAUDE]] — Strategy spec and known issues requiring investigation
- [[35-Tool-GSD2]] — GSD-2 for structured task execution (complementary)
- [[31-Tool-Backtest]] — Backtest skill for standard validation
- [[25-Walk-Forward-Full-Results]] — Walk-forward results that may need deep analysis

---

*Installed: 2026-03-20*
