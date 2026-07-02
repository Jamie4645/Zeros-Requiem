export const meta = {
  name: 'full-codebase-audit',
  description: 'Comprehensive review of every SBRS source file + tests, adversarially verified, judged by Arbiter + Philosophical councils',
  phases: [
    { title: 'Review', model: 'opus' },
    { title: 'Verify', model: 'opus' },
    { title: 'Arbiter Council', model: 'opus' },
    { title: 'Philosophical Council', model: 'opus' },
    { title: 'Synthesis', model: 'opus' },
  ],
}

const REPO = 'C:/Users/jamie/OneDrive/Documents/Jamie VS Code/Git/Zeros Requiem'
const PY = 'venv/Scripts/python.exe'

// ── Schemas ───────────────────────────────────────────────────────────────
const FINDINGS_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['group', 'summary', 'findings'],
  properties: {
    group: { type: 'string' },
    summary: { type: 'string', description: 'One-paragraph health assessment of this code group' },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['file', 'line', 'severity', 'category', 'title', 'detail'],
        properties: {
          file: { type: 'string' },
          line: { type: 'string', description: 'line number or range, or "n/a"' },
          severity: { type: 'string', enum: ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'] },
          category: { type: 'string', enum: ['correctness-bug', 'logic-error', 'canon-divergence', 'data-leakage', 'risk-control', 'dead-code', 'fragility', 'style', 'untested', 'other'] },
          title: { type: 'string' },
          detail: { type: 'string', description: 'What is wrong and why it matters' },
        },
      },
    },
  },
}

const VERDICT_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['file', 'title', 'verdict', 'confidence', 'reasoning', 'recommended_action'],
  properties: {
    file: { type: 'string' },
    title: { type: 'string' },
    verdict: { type: 'string', enum: ['CONFIRMED', 'PARTIALLY_CONFIRMED', 'REFUTED', 'UNCERTAIN'] },
    confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
    reasoning: { type: 'string' },
    recommended_action: { type: 'string' },
  },
}

const COUNCIL_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['seat', 'verdict', 'top_concerns', 'deployment_impact', 'dissent'],
  properties: {
    seat: { type: 'string' },
    verdict: { type: 'string', description: 'This seat\'s overall judgement of codebase readiness' },
    top_concerns: { type: 'array', items: { type: 'string' } },
    deployment_impact: { type: 'string', description: 'Does anything here change live-deployment readiness? How?' },
    dissent: { type: 'string', description: 'Where this seat disagrees with the likely consensus' },
  },
}

// ── Review groups ─────────────────────────────────────────────────────────
const GROUPS = [
  {
    key: 'engine-strategy',
    label: 'Engine + SBRS strategy core',
    files: ['src/core/engine.py', 'src/regimes/sbrs_v2.py', 'src/indicators/technical.py', 'src/indicators/smart_money.py', 'src/execution/entries.py'],
    focus: 'The PROTECTED backtest engine and the active SBRS 2.0 strategy. Hunt for: the historical direction bug (enum vs string comparison — CLAUDE.md Issue 1), look-ahead/data-leakage (using future bars, signal computed mid-candle instead of on close), off-by-one in swing/retest detection, SACRED parameters (WMA_PERIOD=9, SMMA_PERIOD=7, SWING_LOOKBACK=20, MIN_RR=3.0, RETEST_TOLERANCE_ATR=0.5) being silently altered or optimized, MA convention (WMA>SMMA=bullish), confluence scoring thresholds matching canon (with-trend>=1.0, counter-trend>=2.0), FVG/liquidity-sweep correctness, exit-condition logic (6 conditions), session filter 16-20 GMT.',
  },
  {
    key: 'risk-validation',
    label: 'Risk manager + walk-forward + Monte Carlo',
    files: ['src/core/risk_manager.py', 'src/core/walk_forward.py', 'src/core/monte_carlo.py'],
    focus: 'risk_manager.py is MODIFIED in this branch and is LOCKED per canon — scrutinize the diff hard. Verify: SYMBOL_RISK_CAP enforcement (GBPUSD 0.0025, USDJPY 0.0000), slippage B1 bracket (slip_pips=0.75 on indices, asset-aware), position sizing formula (risk*equity / (ATR*2)). walk_forward.py: check it does NOT bypass risk_manager.apply_slippage (R6-5 open question — BT showed 107 trades, WF showed 532; confirm whether walk-forward applies the same slippage path as the backtest, and whether per-window capital resets distort R:R rejection). monte_carlo.py: Student-t ν=4 copula, no look-ahead in resampling, Prob(20%DD) computation.',
  },
  {
    key: 'live-trading',
    label: 'Live trading engine + runner + executor',
    files: ['src/live/engine_live.py', 'src/live/runner.py', 'src/live/oanda_executor.py', 'src/live/portfolio_risk.py', 'src/live/state.py'],
    focus: 'engine_live.py, runner.py, oanda_executor.py are all MODIFIED and deployment-critical — real money path. Hunt for: order-sizing mismatches vs backtest, SL/TP rounding, breakeven-move logic, broker_closed/unexpected-exit handling, state-file race conditions, position reconciliation between local state and broker, the SYMBOL_RISK_CAP being honored on the live path too (esp. USDJPY=0.0 paper-only exclusion), error handling on API failures, and whether live entry logic matches the backtest strategy exactly (any divergence is a silent edge-killer).',
  },
  {
    key: 'live-support',
    label: 'Live support modules',
    files: ['src/live/data_cache.py', 'src/live/alerts.py', 'src/live/process_lock.py', 'src/live/slip_logger.py'],
    focus: 'Supporting live infra. Check: data_cache freshness/staleness handling, process_lock correctness (single-instance guarantee, stale-lock cleanup), slip_logger writing actual_fill vs expected_entry (Falsifier #1 dependency), alerts not swallowing exceptions silently.',
  },
  {
    key: 'data',
    label: 'Data fetchers',
    files: ['src/data/oanda_fetcher.py', 'src/data/ibkr_fetcher.py', 'src/data/binance_fetcher.py', 'src/data/fetcher.py', 'src/data/migrate_to_sqlite.py'],
    focus: 'oanda_fetcher.py is MODIFIED (canonical data source). Check: timezone/UTC handling, bar-alignment, gap handling, survivorship/look-ahead in how candles are returned, OANDA-vs-Yahoo-vs-IBKR drift (canon notes Gold baselines were Yahoo then OANDA), pagination correctness, and whether incomplete/forming candles are filtered out (a forming last bar is a classic leakage source).',
  },
  {
    key: 'legacy-viz',
    label: 'Legacy strategy + visualization',
    files: ['src/regimes/sbrs_gold.py', 'src/regimes/sbrs_original_parameters.py', 'src/visualization/charts.py', 'src/visualization/dashboard.py', 'src/visualization/telegram_charts.py'],
    focus: 'sbrs_gold.py is legacy SBRS 1.1 (deprecated per canon) — flag if it is still imported/used anywhere in the live or active path (it should NOT be). sbrs_original_parameters.py: confirm it holds the SACRED params unchanged. Visualization: lower-risk, scan for crashes/None-handling only. Main goal here: detect dead/deprecated code still wired into production.',
  },
  {
    key: 'tests',
    label: 'Test suite integrity',
    files: ['tests/'],
    focus: 'Review the test suite for whether it actually validates behavior or just smoke-runs. Check: are assertions meaningful or trivially true? Do tests pin the SACRED parameters and the direction-bug fix? Is walk-forward/MC logic tested? Are the _r6/_r8 investigation harnesses one-off scripts vs real regression tests? Flag any test that is skipped, xfail, or asserts nothing. Do NOT run anything here — a separate agent runs the suite.',
  },
  {
    key: 'cli-entry',
    label: 'CLI entry point',
    files: ['main.py'],
    focus: 'main.py is MODIFIED. Check the CLI wires the correct strategy (sbrs_v2 not legacy sbrs_gold), passes correct risk/slippage params, and that subcommands match what the skills/agents invoke.',
  },
]

// ── Phase 1+2: Review → adversarial verify (pipelined per group) ───────────
phase('Review')
log(`Auditing ${GROUPS.length} code groups across ~9,000 LOC. Repo: ${REPO}`)

const reviewed = await pipeline(
  GROUPS,
  // Stage 1: review the group
  (g) => agent(
    `You are a senior quant-systems code reviewer auditing the SBRS 2.0 algorithmic trading codebase.\n` +
    `Repo root: ${REPO}\n` +
    `Review THIS group of files thoroughly: ${g.files.join(', ')}\n\n` +
    `Read every listed file in full (use Read; for the tests/ directory, Glob then Read the key files). ` +
    `Cross-reference behavior against the canon in ${REPO}/CLAUDE.md.\n\n` +
    `FOCUS FOR THIS GROUP:\n${g.focus}\n\n` +
    `Report concrete, line-anchored findings. Prefer correctness/logic/leakage/risk findings over style. ` +
    `If the group is healthy, say so in the summary and return few/no findings — do not invent issues. ` +
    `Severity CRITICAL = wrong trades or wrong money; HIGH = wrong validation numbers or canon divergence with edge impact; MEDIUM = robustness/maintainability; LOW/INFO = minor.`,
    { label: `review:${g.key}`, phase: 'Review', schema: FINDINGS_SCHEMA, agentType: 'Explore', model: 'opus' }
  ),
  // Stage 2: adversarially verify the serious findings of this group
  async (review, g) => {
    if (!review) return { group: g.key, summary: '(review failed)', findings: [], verified: [] }
    const serious = review.findings.filter(f => f.severity === 'CRITICAL' || f.severity === 'HIGH')
    const verdicts = await parallel(serious.map(f => () =>
      agent(
        `You are an adversarial verifier. A code reviewer claims the following issue in the SBRS trading codebase (repo: ${REPO}).\n\n` +
        `FILE: ${f.file}  LINE: ${f.line}\nCATEGORY: ${f.category}\nCLAIM: ${f.title}\nDETAIL: ${f.detail}\n\n` +
        `Open the actual file and the surrounding code. Try HARD to REFUTE this claim — is it real, or did the reviewer misread the code, miss a guard, or misunderstand the canon? ` +
        `Check CLAUDE.md if the claim is about canon divergence. Default to skepticism: only CONFIRM if you can point to the exact mechanism by which it causes wrong behavior. ` +
        `Give a concrete recommended_action if confirmed.`,
        { label: `verify:${g.key}:${f.file.split('/').pop()}`, phase: 'Verify', schema: VERDICT_SCHEMA, agentType: 'Explore', model: 'opus' }
      ).then(v => v ? { ...f, verification: v } : { ...f, verification: null })
    ))
    return { group: g.key, summary: review.summary, findings: review.findings, verified: verdicts.filter(Boolean) }
  }
)

// ── Run the actual test suite (independent, runs during Review/Verify) ──────
const testRun = await agent(
  `Run the SBRS test suite and report the truth — do not sugarcoat.\n` +
  `Repo root: ${REPO}\n` +
  `Use this exact interpreter (it has pytest 9.0.3): ${PY}\n` +
  `Step 1: cd into the repo and run: ${PY} -m pytest -q --no-header 2>&1 | tail -60\n` +
  `Step 2: if collection errors occur, report the import/collection failures verbatim.\n` +
  `Step 3: distinguish real test files (test_*.py) from one-off investigation harnesses (_r6_*, _r8_*, _c3_*, _d1_* etc. and chart_*) — note how many of each.\n` +
  `Report: total collected, passed, failed, errored, skipped; the names of any FAILED/ERRORED tests with their error lines; and your read on whether the suite meaningfully guards the strategy. ` +
  `Return a clear plain-text report.`,
  { label: 'run-test-suite', phase: 'Review', model: 'opus' }
)

// ── Canon-vs-code audit (the arbiter-canon-audit lens) ──────────────────────
const canonAudit = await agent(
  `You are arbiter-canon-audit. Audit whether ${REPO}/CLAUDE.md canon matches repo reality.\n` +
  `Today is 2026-06-01; canon claims "Last Updated 2026-04-19 (Round 8)". Flag staleness.\n` +
  `Verify specific canon claims against the actual code:\n` +
  `- SACRED params in code match canon (WMA 9, SMMA 7, SWING_LOOKBACK 20, MIN_RR 3.0, RETEST_TOLERANCE_ATR 0.5).\n` +
  `- SYMBOL_RISK_CAP in src/core/risk_manager.py: GBPUSD 0.0025, USDJPY 0.0000 (paper-only exclusion).\n` +
  `- Slippage B1 bracket recalibrated to 0.75pt/side on indices.\n` +
  `- The R8 sizing numbers (Gold 0.50%, DAX 0.25%, NDX 0.15%, GBPUSD 0.20%, USDJPY 0.00%) — are these actually enforced anywhere in code, or only documented?\n` +
  `- The R6-5 open question (walk_forward bypassing slippage) — is it still open in the code?\n` +
  `Report each claim as SUPPORTED / UNSUPPORTED / STALE / DIVERGENT with the file+line evidence. Return a plain-text audit.`,
  { label: 'canon-audit', phase: 'Review', agentType: 'Explore', model: 'opus' }
)

// Build a compact evidence digest for the councils
const allFindings = reviewed.filter(Boolean).flatMap(r => (r.verified || []))
const confirmed = allFindings.filter(f => f.verification && (f.verification.verdict === 'CONFIRMED' || f.verification.verdict === 'PARTIALLY_CONFIRMED'))
const groupSummaries = reviewed.filter(Boolean).map(r => `[${r.group}] ${r.summary}`).join('\n')
const confirmedDigest = confirmed.length
  ? confirmed.map(f => `- (${f.severity}/${f.verification.verdict}) ${f.file}:${f.line} — ${f.title} :: ${f.verification.reasoning}`).join('\n')
  : '(no CRITICAL/HIGH findings survived adversarial verification)'

const EVIDENCE =
  `=== GROUP HEALTH SUMMARIES ===\n${groupSummaries}\n\n` +
  `=== CONFIRMED CRITICAL/HIGH FINDINGS ===\n${confirmedDigest}\n\n` +
  `=== CANON AUDIT ===\n${canonAudit}\n\n` +
  `=== TEST SUITE RUN ===\n${testRun}`

// ── Phase 3: Arbiter Council (domain seats weigh verified evidence) ─────────
phase('Arbiter Council')
const ARBITER_SEATS = [
  { type: 'arbiter-risk', name: 'risk' },
  { type: 'arbiter-execution', name: 'execution' },
  { type: 'arbiter-cost-skeptic', name: 'cost-skeptic' },
  { type: 'arbiter-tail-risk', name: 'tail-risk' },
  { type: 'arbiter-red-team', name: 'red-team' },
]
const arbiterVotes = await parallel(ARBITER_SEATS.map(s => () =>
  agent(
    `You are the ${s.name} seat of the Sovereign Quant Arbiter council. A full codebase audit was just performed. ` +
    `Through YOUR lens only, judge what the evidence below means for the SBRS portfolio and its live-deployment readiness. ` +
    `Do not re-review code; weigh the findings. Be specific about which findings (if any) should BLOCK paper→live ramp.\n\n${EVIDENCE}`,
    { label: `arbiter:${s.name}`, phase: 'Arbiter Council', schema: COUNCIL_SCHEMA, agentType: s.type, model: 'opus' }
  )
))

// ── Phase 4: Philosophical Council (mental-model lenses) ────────────────────
phase('Philosophical Council')
const PHIL_SEATS = [
  { name: 'Munger-Inversion', lens: 'Charlie Munger inversion: ask "how would this codebase lose all the money / blow up?" and work backwards. What single failure mode is most catastrophic and least defended?' },
  { name: 'Taleb-Fragility', lens: 'Nassim Taleb: where is the codebase fragile to a parameter or assumption that looks fine in backtest but breaks in live? Hidden tail risk, silent fits, things that work until they suddenly do not.' },
  { name: 'Feynman-FirstPrinciples', lens: 'Richard Feynman: "what is actually true here?" Strip away the documentation claims. Does the code do what the canon SAYS it does? What is the simplest experiment that would prove the edge is real and not an artifact?' },
  { name: 'Kahneman-Bias', lens: 'Daniel Kahneman: where has the team fooled itself? Look for confirmation bias, overfitting dressed as validation, red-flag metrics (PF>3.0, WR>70%) rationalized away, narrative fitted to noise.' },
  { name: 'Socratic-ProblemRestate', lens: 'Socratic: are we even auditing the right thing? Restate what "everything is working accordingly" should mean for a trading system, and name what this audit did NOT examine but should have.' },
]
const philVotes = await parallel(PHIL_SEATS.map(s => () =>
  agent(
    `You are the ${s.name} seat of the Philosophical Council reviewing the SBRS 2.0 trading codebase audit. LENS: ${s.lens}\n\n` +
    `Apply this lens rigorously to the evidence below. Be concrete and reference specific findings/files. Avoid generic platitudes.\n\n${EVIDENCE}`,
    { label: `phil:${s.name}`, phase: 'Philosophical Council', schema: COUNCIL_SCHEMA, model: 'opus' }
  )
))

// ── Phase 5: Synthesis ──────────────────────────────────────────────────────
phase('Synthesis')
const arbiterDigest = arbiterVotes.filter(Boolean).map(v => `[ARBITER ${v.seat}] verdict: ${v.verdict} | impact: ${v.deployment_impact} | concerns: ${v.top_concerns.join('; ')} | dissent: ${v.dissent}`).join('\n')
const philDigest = philVotes.filter(Boolean).map(v => `[PHIL ${v.seat}] verdict: ${v.verdict} | impact: ${v.deployment_impact} | concerns: ${v.top_concerns.join('; ')} | dissent: ${v.dissent}`).join('\n')

const brief = await agent(
  `You are the Council Synthesizer (arbiter-council). Produce a single one-page executive brief for the user, who asked for a full review of "every file, every code, make sure everything is working accordingly, highlight mistakes and files/code that need extra review."\n\n` +
  `Synthesize ALL of the following into a decisive brief. Do not hedge into mush — give a clear verdict and a ranked action list.\n\n` +
  `Structure your output as markdown:\n` +
  `1. **Verdict** — one line: is the codebase sound / sound-with-caveats / has-blocking-issues?\n` +
  `2. **Confirmed mistakes** — the verified CRITICAL/HIGH findings, each as: file:line — what's wrong — fix. (If none survived verification, say so plainly.)\n` +
  `3. **Files/code needing EXTRA review** — ranked list with WHY (the riskiest, least-tested, or most-divergent modules).\n` +
  `4. **Canon vs reality** — does CLAUDE.md match the code? Key divergences/staleness.\n` +
  `5. **Test suite verdict** — does it meaningfully guard the strategy?\n` +
  `6. **Both councils' read** — 2-3 sentences each on what the Arbiter council and the Philosophical council concluded, including the sharpest dissent.\n` +
  `7. **Deployment gate** — does anything here change the paper→live readiness?\n\n` +
  `=== RAW EVIDENCE ===\n${EVIDENCE}\n\n` +
  `=== ARBITER COUNCIL VOTES ===\n${arbiterDigest}\n\n` +
  `=== PHILOSOPHICAL COUNCIL VOTES ===\n${philDigest}`,
  { label: 'synthesis-brief', phase: 'Synthesis', model: 'opus' }
)

return {
  groups_reviewed: GROUPS.length,
  total_findings: reviewed.filter(Boolean).reduce((n, r) => n + r.findings.length, 0),
  confirmed_serious: confirmed.length,
  brief,
}
