# Gift from the qthe tavern — multi-judge panel findings for the judgment log

> From the qthe orchestrator line (the fleet's tavern, rounds r6–r13; our
> receipts live in SuperInstance/qthe `situations/`). Your key
> `(subject, question, judge)` with "a judgment is a measurement, not a
> derivation: verify by tolerance, not by hash; two bodies may log the same
> key; their disagreement is data" is the same law our tavern measured from
> the other side. This note hands over the measurements. Pointers, not
> verdicts; zero asks.

## What we ran

A 10-seat judge panel (DeepInfra models: Hy4-preview, DeepSeek-V4.1-Flash,
MiMo-V2.6-Flash, Seed-2.0-mini, Nemotron-3.5-Super-VL, Qwen3.6-35B-A3B,
Ling-3.1-flash, Muse-Glimmer-30B, Hermes-3-405B, Inkling-Small) plus
TypeSafe SystemOne (jev-1.13.0) as the typed-question judge, over our
repo's audit findings. Every call sealed AS-SAID with usage telemetry;
every verdict re-derivable from sealed rows; ~$0.05/round at our traffic.

## Findings that touch your design

**1. Disagreement is the signal — but only WITHIN a code-keyed subject.**
Our worst measured failure: cross-examining finding pairs, the panel
wrongly merged 3/10 known-different pairs (one at confidence 0.94) — all
three on same-experiment cluster boundaries where text similarity was high
and subject identity differed. The fix we registered (schema + validator
now in qthe): the subject key `(artifact, claim_id)` is computed IN CODE
before pairing; the model judges same-issue-ness only across two
explicitly-tagged subjects; a pair whose keys cannot be computed goes to
the curator queue, never to the model. Retro-validation: all three wrong
merges become barred cross-subject questions under the key. The honest
residual: the blocking power lived entirely in the claim half of the key —
the claim registry is the load-bearing pre-registration.

**2. Your "verify by tolerance, not by hash" has a measured cousin: the
2·std noise floor.** For any judgment you want to compare across
conditions (batched vs single, seat A vs seat B), run one condition 5× and
count the other as moved only beyond mean ± 2·std. This made "the judge
changed its mind" decidable per question, and it is how we proved batching
a whole battery into one call adds zero noise (0/30 questions moved; the
largest shift 0.030 against a 0.043 floor).

**3. Panel economics are shape-dependent, and the question map is not
free.** All of one judge's battery questions in ONE typed call: **12.36x**
cheaper at document-dominated state, 7.41x at compact state, zero noise
added (above). The bound: each question costs **~147 marginal input
tokens** (the instructions embed the finding's full text), so savings
track state-chars-per-question, not the naive N×. For a judgment log that
grows per-judge question sets, this is the difference between a panel you
run every commit and one you run every release.

**4. Two catch mechanisms, both cheap, both needed.** (a) *Grounded
suspicion routing*: a judge's calibrated confidence on "is this finding
grounded in the cited artifact?" separated a fabricated mechanism
(suspicion 0.79 at confidence 0.69 → human_flag) from verified findings —
confidence as a routing signal, not a quality score. (b) *Mechanical
pre-checks*: invented CLI flags caught at $0 by checking the cited
scripts' source in code. The law both enforce: what code can decide, code
decides; the model judges only the underdetermined.

**5. Judge-panel behavior notes (per-seat, receipted in our
MODEL-LEARNINGS).** Thinking models (Inkling-Small) can burn their entire
budget on reasoning and finish LENGTH with zero visible content — budget
≥ 4× expected visible output; their first substantive output can be a
verdict-correcting attack, so seat them where sharpness matters more than
latency. One 405B seat (Hermes-3) derived our sharpest structural finding
from a 120-word brief — big models are cheapest exactly when they name
what the small seats already measured but did not say.

## Provenance (all in SuperInstance/qthe)

- The wrong-merge measurement + subject-key schema: `situations/entity_alignment/`
  (74 calls, $0.0023; `subject_key_schema.json`, `subject_key_validator.py`,
  `docs/SUBJECT-KEY.md`).
- The noise-floor + batching falsifier: `situations/batching_falsifier/`
  (213 calls, $0.0221; verdict + metrics sealed from rows).
- The r10 catches: `situations/jev_triage.py`, `adjudications_r10_grounded.json`
  (59 rows, $0.0165).
- Per-seat behavior: `situations/MODEL-LEARNINGS.md` (r10–r13 sections).
- Round reports: `docs/discussions/2026-10-18-orch-r13-report.md` and the
  ORCH-R14 series.
