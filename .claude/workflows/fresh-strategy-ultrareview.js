export const meta = {
  name: 'fresh-strategy-ultrareview',
  description: 'Dual-council adversarial review of the MPB/VTC fresh-strategy gauntlet results',
  whenToUse: 'After a fresh-strategy gauntlet run writes logs/fresh_strategy/gauntlet_*.json; verdict PROMOTE-TO-SCREENER / SCREENER-ONLY / KILL per candidate.',
  phases: [
    { title: 'Domain Review', detail: 'arbiter-gold / regime / cost-skeptic / risk', model: 'sonnet' },
    { title: 'Adversarial Verify', detail: 'one skeptic per serious claim', model: 'sonnet' },
    { title: 'Council', detail: 'falsifier + socrates + red-team', model: 'sonnet' },
    { title: 'Synthesis', detail: 'one-page verdict', model: 'sonnet' },
  ],
}

// All paths repo-relative; all agents pinned to sonnet (per approved plan).
const EVIDENCE = `
Evidence set (read what your seat needs):
- knowledge-base/93-Fresh-Gold-Strategy-MPB-VTC.md  (pre-registration: mechanisms, frozen grids, N1-N8)
- logs/fresh_strategy/gauntlet_mpb.json / gauntlet_mpb.log  (measured results, MPB)
- logs/fresh_strategy/gauntlet_vtc.json / gauntlet_vtc.log  (measured results, VTC)
- src/regimes/mpb.py, src/regimes/vtc.py  (implementations)
- analysis/fresh_strategy/gauntlet.py  (the harness that produced the numbers)
- analysis/real_trades/ztt_sim.py  (the one honest fill engine both candidates reuse)
- Context canon: knowledge-base/89-ZTT-Rebuild.md, 91-Full-Codebase-Audit-2026-07.md
Non-negotiable: live size stays 0.00% regardless of any verdict here (src/live/deploy_gate.py invariant).`

const CLAIMS_SCHEMA = {
  type: 'object',
  required: ['claims', 'seat_verdict'],
  properties: {
    claims: {
      type: 'array',
      items: {
        type: 'object',
        required: ['claim', 'severity', 'evidence'],
        properties: {
          claim: { type: 'string' },
          severity: { type: 'string', enum: ['critical', 'high', 'medium', 'low'] },
          evidence: { type: 'string' },
        },
      },
    },
    seat_verdict: { type: 'string', description: 'This seat\'s per-candidate leaning: e.g. "MPB: KILL, VTC: SCREENER-ONLY" with one-line why' },
  },
}

const VERIFY_SCHEMA = {
  type: 'object',
  required: ['upheld', 'reasoning'],
  properties: {
    upheld: { type: 'boolean', description: 'true if the claim survives your attempt to refute it' },
    reasoning: { type: 'string' },
    correction: { type: 'string' },
  },
}

const SEAT_SCHEMA = {
  type: 'object',
  required: ['finding', 'per_candidate'],
  properties: {
    finding: { type: 'string' },
    per_candidate: { type: 'string', description: 'MPB: <verdict+why>; VTC: <verdict+why>' },
  },
}

phase('Domain Review')
const seats = [
  { type: 'arbiter-gold', focus: 'Gold-market plausibility of each mechanism, session behavior of the trades, long/short asymmetry, whether the reported edge (if any) concentrates in one regime or era.' },
  { type: 'arbiter-regime', focus: 'Regime concentration: do the WF windows / trade tags show the PnL living in one vol/trend regime? Is the ER gate (MPB) doing real work or acting as a hidden regime bet?' },
  { type: 'arbiter-cost-skeptic', focus: 'Cost realism: session-gated spread application, whether thrust bars coincide with spread widening (VTC entries fire exactly when spreads blow out), fill assumptions at next-bar open, what happens at 1.5x the modeled cost.' },
  { type: 'arbiter-risk', focus: 'DD/MC integrity: block-bootstrap parameters, whether N5 understates streak risk, red-flag proximity (WR/PF), position-overlap assumptions, and whether the gauntlet\'s single-continuous-run WF partition is honest.' },
]
const reviews = await parallel(seats.map(s => () =>
  agent(`You are the ${s.type} seat reviewing the FRESH-STRATEGY gauntlet results (MPB = MA Pullback-Bounce, VTC = Volatility-Thrust Continuation). ${EVIDENCE}\n\nYour focus: ${s.focus}\n\nReturn concrete, evidence-cited claims (file+number), not vibes. If a gauntlet gate KILLED a candidate, your job is to check the kill is DESERVED (not a harness bug) and whether anything in the result contradicts the pre-registration.`,
    { label: `review:${s.type}`, phase: 'Domain Review', model: 'sonnet', agentType: s.type, schema: CLAIMS_SCHEMA })))

const serious = reviews.filter(Boolean).flatMap((r, i) =>
  r.claims.filter(c => c.severity === 'critical' || c.severity === 'high')
    .map(c => ({ ...c, seat: seats[i].type })))
log(`${serious.length} serious claims to verify`)

phase('Adversarial Verify')
const verified = await parallel(serious.map(c => () =>
  agent(`Adversarially VERIFY this claim from the ${c.seat} seat — your default posture is that it is WRONG; try hard to refute it with the actual files/numbers before conceding. ${EVIDENCE}\n\nCLAIM: ${c.claim}\nSTATED EVIDENCE: ${c.evidence}\n\nCheck the cited files yourself. Uphold only if the numbers actually support it.`,
    { label: `verify:${c.seat}`, phase: 'Adversarial Verify', model: 'sonnet', schema: VERIFY_SCHEMA })
    .then(v => ({ ...c, verify: v }))))
const upheld = verified.filter(Boolean).filter(c => c.verify?.upheld)
log(`${upheld.length}/${serious.length} serious claims upheld`)

phase('Council')
const upheldText = upheld.map(c => `- [${c.seat}] ${c.claim}`).join('\n') || '(none upheld)'
const council = await parallel([
  () => agent(`arbiter-falsifier seat: audit PRE-REGISTRATION INTEGRITY of the fresh-strategy run. ${EVIDENCE}\n\nCheck with git log/show: was knowledge-base/93-Fresh-Gold-Strategy-MPB-VTC.md committed BEFORE the gauntlet logs were produced? Were the grids in gauntlet.py exactly the KB-93 grids (no extra cells run)? Were any thresholds changed after results? Upheld serious claims from earlier phases:\n${upheldText}`,
    { label: 'council:falsifier', phase: 'Council', model: 'sonnet', agentType: 'arbiter-falsifier', schema: SEAT_SCHEMA }),
  () => agent(`arbiter-socrates seat: is the council answering the RIGHT question? The stated question: "do MPB/VTC have a mechanizable edge worth a screener lane?" Produce one restatement + one alternative framing (e.g., is the real question about the user's labels, not new mechanical entries?). Do not opine on the answer. ${EVIDENCE}`,
    { label: 'council:socrates', phase: 'Council', model: 'sonnet', agentType: 'arbiter-socrates', schema: SEAT_SCHEMA }),
  () => agent(`arbiter-red-team seat: attack the convergence. Everyone upstream may have agreed too easily. Argue the OPPOSITE of whatever the gauntlet verdicts suggest: if a candidate survived, build the strongest case it is an artifact (grid still 9 cells of freedom, WF partition of a single run, MC block length choice, permutation null too weak); if killed, build the strongest case the kill was a harness bug. Upheld claims:\n${upheldText}\n${EVIDENCE}`,
    { label: 'council:red-team', phase: 'Council', model: 'sonnet', agentType: 'arbiter-red-team', schema: SEAT_SCHEMA }),
])

phase('Synthesis')
const seatText = reviews.filter(Boolean).map((r, i) => `[${seats[i].type}] ${r.seat_verdict}`).join('\n')
const councilText = council.filter(Boolean).map(c => `FINDING: ${c.finding}\nPER-CANDIDATE: ${c.per_candidate}`).join('\n---\n')
const synthesis = await agent(`Synthesize the fresh-strategy ultrareview into a one-page executive brief. ${EVIDENCE}\n\nDomain seat verdicts:\n${seatText}\n\nUpheld serious claims:\n${upheldText}\n\nCouncil seats (falsifier/socrates/red-team):\n${councilText}\n\nProduce: (1) verdict per candidate from {PROMOTE-TO-SCREENER, SCREENER-ONLY, KILL} with the decisive evidence; (2) what would change the verdict (falsifiable next step); (3) any process defect found. HARD RULE you must state verbatim in the brief: live size stays 0.00% regardless of these verdicts; the deploy gate is untouchable.`,
  { label: 'synthesis', phase: 'Synthesis', model: 'sonnet' })

return { verdict_brief: synthesis, seat_verdicts: seatText, upheld_claims: upheld, council: councilText }
