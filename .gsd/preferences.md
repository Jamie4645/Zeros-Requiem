# GSD Project Preferences: Zeros Requiem

## Project Context
Algorithmic trading system (Python). Two frameworks: SCAF 2.0 (backtesting) and SBRS 1.1 (live paper trading on OANDA). Sacred parameters exist that must NEVER be optimized without explicit user approval.

## Verification Commands
```bash
python -m pytest tests/quick_test.py --tb=short -q
```

## Coding Standards
- Python 3.10+
- pandas/numpy for data manipulation
- No type annotations on unchanged code
- No docstrings on unchanged functions
- Test after every change
- Risk-first: discuss MAE and Sharpe before profits

## Protected Files (NEVER modify without explicit approval)
- src/core/risk_manager.py
- src/regimes/sbrs_original_parameters.py
- Core SBRS parameters (WMA_PERIOD, SMMA_PERIOD, SWING_LOOKBACK)

## Commit Style
- Imperative mood, concise
- Prefix with area: `[SBRS]`, `[SCAF]`, `[engine]`, `[risk]`, `[live]`, `[docs]`

## Model Preferences
- Planning: Use thorough reasoning
- Execution: Fast and direct
- Verification: Always run tests

## Budget
- Conservative token usage
- Prefer targeted file reads over full codebase scans
- Use subagents for parallel research only when genuinely needed
