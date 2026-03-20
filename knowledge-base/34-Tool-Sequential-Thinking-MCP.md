---
tags: [tool, MCP, debugging, reasoning]
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

Located in `.claude/settings.local.json`:

```json
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@anthropic/sequential-thinking-mcp"]
    }
  }
}
```

### Requirements
- Node.js installed (for `npx`)
- Internet access on first run (downloads the package)
- After first run, cached locally

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
