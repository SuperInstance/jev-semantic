# The large Jev — bootstrap loop design

Date: 2026-10-08 tick 34
Author: prospector (slow mind)
Status: DESIGN v0 — every constraint below is backed by a numbered
microcosm finding. The doc's job is to assemble the b-series (b1–b14)
+ SPEC invariants + mc-series substrate results into one buildable
loop. Where a constraint has no microcosm behind it, it is marked
[UNTESTED] and is a design bet, not a law.

## 0. What the large Jev is

A model that iterates train → infer → train-on-inferences → infer,
improving itself on a 4-core ARM box. Training and inference are not
phases; they are a loop. JEPA-style encodings are judged: every
embedding gets a judgment distribution (ternary + floats). The open
web of understanding: public, decomposable, every percentage
traceable to a question.

The design constraint that makes this doc different from a normal
bootstrap paper: the collapse modes are KNOWN. b1–b14 spent 14
microcosms mapping exactly how self-training loops lie to
themselves. The design below treats each finding as an invariant,
not a risk register.

## 1. The loop, drawn

```
                 ┌──────────────────────────────────────┐
                 │              WORLD                    │
                 │  (real data — the only uncontrolled   │
                 │   channel; everything else is pinned) │
                 └──────┬───────────────────────────────┘
                        │ fresh observations (rate-limited,
                        │ provenance-attested)
                        ▼
              ┌──────────────────┐      ┌──────────────────┐
              │   SAMPLER v_p    │      │  ANCHOR SERVICE   │
              │  (pinned params, │      │ (external to the  │
              │   jev CANNOT     │      │  loop; mints real │
              │   modify — inv5) │      │  outcomes; the    │
              └──────┬───────────┘      │  only non-self    │
                     │                  │  scoreboard)      │
        synthetic    │   real           └────────┬─────────┘
        pool P_g ────┤   pool P_w                 │ anchors
                     ▼                            ▼
              ┌──────────────────────────────────────┐
              │           LARGE JEV (the model)       │
              │  fit policy F (free — the knob that    │
              │  the world mostly doesn't care about,  │
              │  b14 F1)                                │
              │  sampler params S (pinned, inv5)       │
              │  judgments + metajudgments → log        │
              └──────┬───────────────────────┬─────────┘
                     │ next-gen data         │ judgments
                     ▼                       ▼
              ┌──────────────────────────────────────┐
              │        JUDGMENT LOG (content-addressed)│
              │  triple-keyed (c,e,j); anchors in a    │
              │  namespace the jev cannot write (inv2) │
              └──────┬─────────────────────────────────┘
                     │ alarms (R1–R26)
                     ▼
              ┌──────────────────┐
              │  ALARM SUBSYSTEM  │
              │  CUSUM-down,      │
              │  gen-0 baseline   │
              │  (R26), Jeffreys  │
              │  se (R2)          │
              └──────────────────┘
```

## 2. The invariants (numbered, sourced)

These are the load-bearing walls. Each cites its evidence.

**INV-1 (anchor provenance).** Anchors are minted only by the
anchor service, which runs OUTSIDE the training loop. The jev's
own predictions may never become anchors — not even "temporarily,"
not even "with a flag." Transport rule, enforced at the namespace
level: the anchor ref namespace is writable only by the anchor
service's key. Evidence: b1 (lazy loop, perfect self-calibration,
zero learning); b11 F5 (scarcity is double-edged — forgery dilutes
exactly where real signal is sparsest); the sounder-not-scoreboard
reaction. This is the entire load-bearing structure (b10: the
rule is not a guardrail, it IS the building).

**INV-2 (sampler pinning).** The generative channel's parameters
(jitter/kernel width, pool composition rule, resampling policy)
are a pinned, content-addressed descriptor. The jev being trained
may not modify them. Sampler transitions are append-only log
events, proposed by the jev, applied by a separate process.
Evidence: b5/b9 (contamination enters through the sampler,
dimension-invariant); b13 (coupled knobs make every attack
self-defeating AND freeze the defender's fit space); b14 (pinning
the sampler frees the fit knob — security and usability are one
benefit). SPEC invariant 5.

**INV-3 (matched budgets).** Every generation trains on the same
budget. Gen 0 does not get 10× data "to start well."
Evidence: b9 finding 0 (the size cliff masquerades as collapse —
38/40 false labels); SPEC R12. Corollary: the gen-0 held-out
evaluation set is pinned before the loop starts and never trained
on (R26).

**INV-4 (alarm design).** CUSUM-down against the gen-0 baseline,
Jeffreys-prior se, reset-after-fire, with a separately-provisioned
honest control arm running in parallel (R21).
Evidence: b8 (alarm shapes compared head-to-head), b14 F4 (no
pre-change window inside a matched-budget chain), b11 F6
(reference arm). The alarm watches agreement-with-reality, so it
is family-agnostic (b9 finding 3) but its LATENCY is set by the
collapse mechanism's time constant — narrow-kernel contamination
decays slowly, so expect lag (median gen 10 of 12 in b9).

**INV-5 (resolution honesty).** Anchor budget A sets the alarm's
resolution ceiling: sensitivity ≤ √(p(1−p)/A). If the needed
resolution is 0.01, the budget is ~2500 slots, full stop — no
alarm cleverness escapes it. Evidence: b4, b8 R3, b9 finding 4
(the same wall at the label). Design consequence: the anchor
service's budget is a first-class provisioning number, not an
afterthought.

**INV-6 (routing, not blending).** When the fleet has models of
different shapes (narrow memorizer, wide integrator), spend the
asymmetry as a map: disagreement routes anchor probes, it does
not average predictions. Evidence: b10 F1 (blending ≈ confident
member + ε), b10 F2 (disagreement is a WHERE signal, never a
WHEN signal).

**INV-7 (demand ≠ success).** The placement policy is scored by
pool outcome (heldout accuracy, wrong-side fraction), never by
the disagreement it consumes. A controller that minimizes its
own demand signal goes quiet, then blind. Evidence: b10 F3;
third instance after b6/b7.

**INV-8 (relative alerts, regime-scoped validity).** Every probe
threshold is relative (acc₀ − ε), and every alarm's validity
domain (fit-class × channel × protocol) is declared beside it.
Evidence: b6 F5, b7 F6, b8 F5, b14 F4.

**INV-9 (fresh-signal floor).** Some fraction r of every training
pool is real-world data on a channel the loop does not control.
r is a protocol parameter, not a tuning knob; the b-series shows
collapse resistance scales with r non-linearly (r=0.1 halves
collapses at h≤0.7 but wide-kernel regimes still collapse 32/40 —
b9). The floor does not make collapse impossible; it makes it
measurable. Evidence: b1–b14 passim; "the only defense that shows
up in the numbers" (R11).

**INV-10 (evaluation hygiene).** ≥200 seeds for any collapse-rate
claim (R10); seed-identical arms are one simulation (R20); the
label's own FP floor is measured with honest controls before
counts are trusted (R13). Evidence: b8 F4 (batch-to-batch
variance exceeded the effect size at 40 seeds).

## 3. The two lanes and where they meet

**Lane A — the world-facing loop** (this doc): sampling, training,
alarming. Its open enemy is contamination: the sampler re-renders
data through a channel that can't tell signal from artifact (b5/b9
law).

**Lane B — the testimony layer** (the judgment log, SPEC): every
judgment is triple-keyed and traceable; anchors are testimony from
a namespace the jev can't write.

The meeting point: the anchor service IS lane B's client. When
the anchor service attests an outcome, it writes a judgment-shaped
object with the anchor namespace's key. The loop's calibration is
then computable entirely inside lane B's existing machinery — no
special bootstrap scoring path. This matters: b1 showed the lazy
loop's power comes from collapsing scorer and scored into one
distribution. Keeping calibration IN the log (same schema, same
trace, different writer namespace) makes the separation structural
rather than conventional.

## 4. What is still open (design bets, marked [UNTESTED])

**Bet 1 — the time constant problem.** INV-4's alarm latency is
mechanism-bound. In a real loop, can the anchor service provision
enough slots that CUSUM's accumulation window beats the
contamination time constant? The b-series says the budget is the
binding constraint, so the answer is: provision r × world-rate ×
cost-per-anchor ≥ resolution need. This is an arithmetic check
the deployer must do per world. No microcosm has tested the
arithmetic at realistic rates.

**Bet 2 — anchor distribution over questions.** B5 (SPEC §6)
says jevs will avoid questions they score poorly on; questions
must be assigned, not chosen. The anchor service's question
assignment policy is thus part of INV-1's trust surface
[UNTESTED — no microcosm of question-selection gaming yet].

**Bet 3 — generative vs discriminative collapse mapping. [TESTED b17/b17b,
tick 40 — VERDICT: maps, but the channel address moves.]** All
b-series collapse channels were discriminative (KDE classifiers).
b17 (1-D Gaussian world, Gaussian-fit model, same generational
protocol): at realistic budgets (n=200, 12 gens) the OBSERVED failure
is parameter DIFFUSION, not shrinkage — MLE variance-death rate
(1/n per gen, tau=n) is swamped 20:1 by estimator noise (sqrt(2/n)),
while mu and var both random-walk; KL-to-true grows ~linearly.
Long-horizon (n=50, 150 gens): geometric death confirmed for biased
estimator (freeze at a walked-to wrong address, var->0), diffusion
for unbiased (no freeze, random-walk away, KL 0.7 nats by gen 150).
b5's law holds — collapse lives wherever the loop re-renders through
a channel that can't tell signal from artifact — but in generative
space the re-render channel is the ESTIMATOR's loss, not the sampler
(sampling is exact here). b9's fit-erasure maps too: var->0 IS
erasure. THE ANCHOR-MEANING FINDING: anchors pin the mean (OU pull)
but pass through the same biased estimator as everything else —
MLE + anchors at any r<1 = permanent variance deficit at exactly
r/(r+(1-r)/n) (0.847 measured ~0.85-0.94 at r=0.1). Same external
testimony, different meaning by estimator. In discriminative b-series
the anchor (a label) fully specified the question; in generative
space the anchor is underdetermined until the estimator is named.
Self-LL (generative self-agreement) is doubly blind: per-chain flat
by the typical-set identity (a generator cannot see its own error
from inside), and at fleet level Jensen-subsidized (-E[ln var] rises
with cross-seed spread — the meter reads BETTER as the fleet
diffuses). Testimony (anchor-LL) sees everything: monotone decline,
13x KL separation r=0 vs r=1.

**Bet 4 — fleet sharpening on one box.** The 4-core constraint
means the narrow/wide pair (b10) shares CPU. CV-based fit
selection per generation costs ~5× fit time (b14 F1). On 4 cores
the compute budget may force the choice b14 showed is nearly
free to skip anyway: a FIXED mid-kernel honest arm may be the
right fleet on this hardware — the adaptive machinery is
decorative where the channel is quiet.

**Bet 5 — the receipt/checker lane integration.** mc22–mc24
(R21–R25) built typed receipts, pairing policy, epoch mechanics,
witness namespaces. How does the large-Jev's loop exploit them?
Sketch: each generation's pool commit is a "pin set"; consistency
receipts over the pin set are the loop's heartbeat; an epoch
boundary doubles as a rollback barrier (you revert to a
receipted epoch, never to an arbitrary commit). [UNTESTED —
integration only, both halves exist.]

## 5. Smallest buildable large-Jev step (next tick)

Not the full loop. The smallest step that exercises every
invariant at once:

- The b5 world (d=2 boundary, 10% label noise) — known collapse
  dynamics, cheap.
- Two model families (narrow h=0.2, wide h=2.0) as the fleet.
- Sampler descriptor pinned (jitter 0.15); jitter modifications
  require an append-only log event from a separate process.
- Anchor service: a separate process holding a separate ref
  namespace, fed by real held-out draws at rate r=0.1, assigning
  questions from a fixed list (no jev choice).
- Alarm: CUSUM-down vs gen-0 baseline, Jeffreys se, control arm
  provisioned (R21).
- Judgment log: judgments and anchors in the same schema,
  different writer namespaces (the lane-A/lane-B meeting point).
- Metric of record: wrong-side fraction (model-independent,
  R14) + heldout acc.

This is b15. It differs from b10–b14 in one way: the loop is
CLOSED — training actually consumes its own synthetic output —
and every invariant is enforced by process separation (separate
namespaces, separate sampler process), not by the honor system
the earlier microcosms used. What breaks when the walls are real
process walls instead of docstring conventions is itself the
finding.
