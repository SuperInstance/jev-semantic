# Judgment Log — Spec v0.1

The semantic half of the window compiler. window.py compiles structure
(task + nexus + activity → an agent's window). This is the layer that
makes the window *mean* something: a growing graph of questions,
judgments, and anchors, keyed so every percentage is traceable.

Status: SPEC ONLY. No implementation this tick. Microcosm next.

---

## 1. Core law

An embedding is testimony, not the thing. (The sounder isn't the
scoreboard — reaction fragment, 2026-10-07.) Therefore a judgment must
be keyed by everything that shaped it:

```
(content-hash, encoder-hash, jev-hash)
```

- **content-hash** — WHAT was judged. Git object hash of the artifact.
- **encoder-hash** — HOW it was rendered into the space the Jev sees.
  Encoder = model + version + params, itself pinned and content-addressed.
- **jev-hash** — WHO judged. The judge's weights + config, pinned.

Same content under a new encoder = a DIFFERENT question. Refusing to
collapse the triple into one key is the spec's central decision.

## 2. Object types

All objects are canonical JSON, content-addressed in the git object
store (hash-object, loose or packed). Four types:

### 2.1 question

```json
{
  "type": "question",
  "text": "Is this claim consistent with the cited evidence?",
  "answer_space": "ternary_float",
  "domain_hint": null
}
```

`answer_space` ∈ {`ternary_float` (v ∈ {-1,0,1} + confidence),
`unit_float` (v ∈ [0,1]), `rank` (ordering only)}.

Identity = hash of canonical serialization. Editing the text re-pins
a new question; old judgments stay bound to the old hash. Question
drift is visible, not silent.

### 2.2 encoder / jev descriptors

```json
{
  "type": "encoder",
  "model": "<name>",
  "version": "<semver-or-hash>",
  "params_hash": "<hash-of-weight-file-or-config>",
  "render": "<spec-ref: how content becomes a vector>"
}
```

Jev descriptor: same shape, plus `train_seq: ["<jev-hash>", ...]`
(the bootstrap lineage — which jev trained this one). The lineage is
the collapse-detection surface: a jev whose ancestors converge to
itself is a sounder listening to itself.

### 2.3 judgment

```json
{
  "type": "judgment",
  "q":  "<question-hash>",
  "c":  "<content-hash>",
  "e":  "<encoder-hash>",
  "j":  "<jev-hash>",
  "v":  0.73,
  "conf": 0.61,
  "basis": ["<judgment-hash>", ...],
  "t": "2026-10-07T17:20:00+08:00"
}
```

`basis` = the graph edges. What other judgments informed this one.
Metajudgments need NO special type: a judgment whose `c` is another
judgment's hash IS a metajudgment. Same cell protocol as mc6 —
structurally identical at every layer, buying addressing, not
semantics.

### 2.4 anchor

```json
{
  "type": "anchor",
  "judgment": "<judgment-hash>",
  "outcome": 0.91,
  "source": "<hash-or-description of the external check>",
  "t": "2026-10-08T09:00:00+08:00"
}
```

The scoreboard. Anchors are the ONLY objects allowed to cite
outside-the-loop outcomes. Everything else is inference.

## 3. Invariants (the substrate will NOT enforce these)

The graph stores; the layer above constrains (the law, 7-for-7):

1. **Append-only.** Judgments are never updated in place. Two
   judgments with the same (q,c,e,j) are BOTH kept — multiplicity
   lives in refs, not hashes (mc6 P1). Consumers choose: latest-wins,
   or distribution over time.
2. **Anchor provenance.** An anchor MUST cite an external check.
   Transport rule, not graph property (mc2): a jev may not author
   anchors for its own judgments. Enforcement = push policy on the
   shared log.
3. **No basis cycles among live judgments.** Cycles are storable;
   they're caught by the validator (walk from each new judgment).
   The validator itself is a pinned object — agree on its hash
   (mc4 T6). Validation becomes addressable, versioned, forkable.
4. **Encoder drift orphans, visibly.** New encoder version → old
   (c,e) judgments hash-mismatch the current encoder descriptor.
   Staleness is a hash comparison, not a metadata flag. Deliberate:
   drift forces re-judgment; orphans are history, not garbage.
5. **Sampler provenance.** In generational training loops, the
   sampler (the channel that re-renders data between generations —
   jitter width, kernel bandwidth, augmentation params) is a pinned,
   content-addressed descriptor. Sampler parameters may NOT be
   modified by the jev being trained. Transitions are append-only
   events logged beside the judgments. Rationale: b5/b9 showed
   contamination enters through the re-rendering channel identically
   at every dimension — the sampler IS the rewrite site; b6/b7 showed
   a self-controlled sampler can be manipulated to launder
   disagreement into blur (wide) or fossilize error (narrow), and
   no calibration alarm sees either, because blur degrades heldout
   accuracy, not self-agreement. "What is your kernel width and who
   set it" must be answerable from the log (R7). This is B1's
   transport rule applied to the channel one level down: anchors
   must be external (invariant 2), AND the sampler must be external
   (invariant 5).

## 4. Calibration — why anchors exist

Per (jev, question) the calibration table is:

```
for each anchor on judgments by jev of question q:
    error = |v - outcome|
group by jev, by question
```

The bootstrap loop (train → infer → train on inferences) floats free
without this. WITH it, jev lineage + calibration = the collapse
alarm: a lineage whose calibration degrades generation-over-generation
is the sounder listening to itself, measurable.

A judgment is good if a better-informed future judgment would agree
(mc7's law, stated for testimony): that's what an anchor approximates.

## 4.1 Alarm design rules (from microcosms b1–b10)

The calibration alarm is the bootstrap's collapse detector. Eleven
microcosms of alarm and attack shapes produced these rules:

**R1. Never running-min.** Rise-over-running-min compares each
observation against an extreme order statistic of the past. At A_SLOTS=40
it fires in 85–100% of honest runs (b8). Use CUSUM against a fixed
robust baseline (median of first k≥3 warmup generations), one-sided
toward the collapse direction, drift k=0.5σ, threshold h=5σ, reset
after fire (b8: 1–5 FP runs across all arms).

**R2. The estimator's own formula is an attack surface.** Plug-in
binomial se = √(p̂(1-p̂)/n) returns ZERO at p̂ ∈ {0,1} — which happens
at high agreement with finite slots. Any σ-scaled band collapses to
hair-trigger. Fix: Jeffreys-prior posterior std, a=k+0.5, b=n−k+0.5,
se = √(ab/((a+b)²(a+b+1))). This dropped floor_rob FP from 12/39 to
5/39 at r=0.1 and 6/40 to 0/40 at r=1.0 (b8). Without the prior, a
lazy loop gaming toward p̂=1.0 gets MORE alarm-sensitive to noise,
not less — the se is anti-correlated with alarm usefulness.

**R3. Alarm sensitivity ≤ √(p(1−p)/A_SLOTS).** Full stop. The
resolution wall (b4, b8): collapse signal (0.03–0.05) sits at the
per-generation estimator noise. No alarm shape escapes this. CUSUM
accumulates across generations (trading latency for resolution) but
cannot manufacture signal that isn't there. Want 0.01 resolution →
~2500 anchor slots.

**R4. Derivative alarms are blind to frozen error.** A degradation
alarm detects CHANGE, not OFFSET. A chain frozen at |δ|=0.2 from gen 0
shows flat calibration forever (b4: alarm_rate 0.0 on collapsed
chains). Need an absolute floor alongside the rise detector — and the
floor's baseline must itself be robust (median of warmup, not gen-0
draw; a single noisy gen-0 draw manufactures false floors).

**R5. Alerts must be relative, never absolute.** Thresholds inside
the noise band (e.g. 0.85 when acc₀ = 0.866) manufacture false-alert
machines (b6 F5). Use acc₀ − ε. Regime-crossing controllers break
absolute calibration (b7 F6).

**R6. Alarm validity is regime-scoped.** Self-agreement alarms work
within a fit-class (narrow kernel: quiet AND healthy) but a controller
crossing regimes produces non-monotonic responses that no fixed
threshold interprets (b7). The alarm's validity domain is the
fit-class, not the run.

**R7. Provenance of the channel beats output of the channel.**
"What is your kernel width and who set it" is load-bearing;
"do you agree with yourself" is arrival-shaped (b6 F2, b7 F7).
Controller trajectories are loop-visible metadata regardless of
direction (ratchet up or freeze down — both fingerprint).

**R8. Anchor value is regime-dependent.** Wide kernel: anchors help
(integration averages label noise, fresh signal counters contamination).
Narrow kernel: anchors hurt (each wrong real point is a local error
that can't be smoothed) (b7 F5). Spatial form: R19.

**R9. Sampler integrity, not just anchor provenance.** A lazy loop
can attack the channel that re-renders data (widen jitter to launder
disagreement into blur) even when anchors are honest (b5, b13).
Blur-laundering needs decoupled knobs; coupled knobs are self-defeating
(b6). Freeze-laundering fails because narrowing amplifies the churn
it was meant to hide (b7).

**R10. Evaluation protocol: ≥200 seeds.** Collapse rate at r=0 was
3/40 in b8's seed batch vs 11/40 in b4's. At 40 seeds, the variance
across seed batches exceeds the difference between alarm shapes —
any comparison is noise. Alarm-shape claims need ≥200 seeds or
the ranking is underpowered.

**R11. Fresh-signal probes on uncontrolled channels are the only
defense that shows up in the numbers.** Every metadata-level check is
forgeable or evadable (b1 A1–A3). Anchors on the sampler's input —
not its output — are the load-bearing structure.

**R12. Generational protocols must hold the training budget constant.**
b9's gen 0 fit on 2000 points, later gens on ~200; the collapse label
`acc_last < acc0 − 0.05` then measured the size cliff — honest arms
(r=1.0, zero self-sampling) "collapsed" 38/40 and 24/40. Re-label
against the first matched-size generation (gen 1) and run alarm
warmup there too. Budget-mismatched baselines manufacture collapse.

**R13. Calibrate the label's own FP rate before trusting collapse
counts.** Even with matched budgets, wide-h fits vary draw-to-draw;
b9's honest h=2.0 arms "collapsed" ~55% under a fixed 0.05 threshold
with fresh data every generation. Honest-control arms measured with
the same threshold give the label's false-collapse floor; only
counts above the floor are signal. (The R3 resolution wall applies
to evaluation exactly as to alarms.)

**R14. Mechanism invariance note (b9).** The sampler channel is
dimension-invariant — contamination enters through the re-rendering
channel (jitter × inherited labels) identically at d=2 and d=20.
What dimension changes is the FIT's ability to express the boundary
(isotropic high-d fits erase the boundary from the signal axis:
40–75% boundary-less chains). Diagnose channels separately: measure
pool contamination (model-independent) before attributing collapse
to the estimator.

**R15. Sharpening pairs route, never blend (b10 F1).** Probability-
averaged ensemble ≈ the confident member + ε (0.758 vs 0.754) —
blending averages away which model knew what. An asymmetric pair
realizes its value by anchor-budget ROUTING: probes follow
disagreement. Directed placement beat uniform 28-12 paired,
+0.054 acc_last, collapses 27→21 at zero budget increase. The
asymmetry is spent as a map, not a mixer.

**R16. Disagreement is a WHERE signal, never a WHEN signal
(b10 F2).** Early disagreement ranks where wide-model anchors pay
(tercile gradient +0.014/+0.052/+0.102) but cannot predict decay
timing or magnitude (corr 0.06–0.083, pooled wrongside corr 0.171 —
directionally right, too weak to alarm with). Placement policy
consumes disagreement; the collapse alarm does not. One-line form:
probes follow disagreement, alarm does not. Extends R6's regime-
scoping: not just which alarm is valid where, but which signal is
valid for what.

**R17. Demand signal must not double as success metric
(b10 F3, third instance after b6/b7).** Directed placement
extinguishes the disagreement that drives it (terminal dis 0.015
vs uniform's 0.033) while the pool is no cleaner (wrongside 0.232
≈ 0.238) — the gain is placement, not decontamination. A
controller minimizing disagreement goes quiet, then blind. Score
a placement policy by pool outcome (heldout/wrongside), never by
the disagreement it consumes.

**R18. Agreement is absence of evidence, never confirmation
(b10 F4).** A pair disagrees only where both have opinions;
contamination absorbed into a global average is pair-invisible
(b4's wrong-attractor IS a high-agreement state). Deliberate
asymmetry's failure mode is prior-harmonization — the pair
agreeing because the wide member converged onto the narrow one's
error.

**R19. Anchor value is shape-dependent: regime IS location
(b10 F5, extends R8).** R8's regime dependence has a spatial
form: narrow prices spread coverage (directed placement cost it
−0.024, 14-26 paired), wide prices boundary-band coverage. A
placement policy must price what each member actually buys.

**R20. Seed-identical arms are one simulation (b10 design note).**
Arms sharing seeds and protocol are the same run counted twice;
single-model baselines must be separately run or the comparison is
within-pair only. With R10: an invalid control at 400 seeds is
still invalid — independence first, then count.

**R21. Every self-agreement alarm ships with a fixed well-tuned
honest control arm run in parallel (b11 F6).** Probes catch decay,
not laziness — an arm that decays for benign reasons (found a
good regime early) passes the probe exactly as a lazy arm does.
Without a reference arm, the alarm grades against the fleet
default, and the fleet default may be the easiest thing in the
system to beat. The comparator is infrastructure, not evaluation:
provision it, pin it, and budget for it like an anchor slot.
Evaluation edition of b9 finding 0 — label validity is regime-
scoped, and "regime" includes the comparator's quality.

## 4.2 Receipt design rules (from microcosms mc21–mc24)

The checker lane (contention detection → assigned checker →
consumption gate → level-typing → epoch mechanics) produced its own
rule set. Receipts are the judgment log's answer to mc5 P5
(availability without proof): a claim that a consistency check RAN.

**R21. Receipts are typed objects: (epoch, level, pair, method).**
Untyped receipts misrender. mc24 F5: a cross-epoch receipt (epoch
field = the older member's epoch) renders BYTE-IDENTICAL to an
in-epoch receipt, but its level no longer means "one reduction
round" — consumers reading level as a global round-count
misinterpret every cross-epoch receipt in the store. Type is not
metadata; it is the field that makes level meaningful. Receipt
schema gains: `"epoch": <int>, "level": <int>, "pair": [a, b],
"method": "cone-check@v<n>"` — all four pinned, all four load-bearing.

**R22. Pairing policy is load-bearing; specify it or starvation is
silent (mc22 F3, poc-gate F3, mc23 F1).** Receipts are second-order
objects — R(a,b) needs both pins present, so they serialize against
their inputs, and odd/unpaired pins starve by construction. Under
batched arrival (not serialized — mc23 regime note), naive window-
close pairing starves 100% of chains including the root. The relief
valves, in order: (a) level-typing converts O(pins²) candidate pairs
to O(levels²) — but only if levels are carried across windows; (b)
carry-forward under batching produces a forest, not a tree
(mc23 F2) — root-commitment is a SET-CLOSURE concept, achievable
only at close+drain or when n = 2^k; (c) epoch boundaries relocate
the serialization point from pair-time to set-close (mc24).
"Who pairs with whom, when" is protocol, not convenience.

**R23. Partition parameters are encoder geometry (mc24 F4, 4th
instance after mc20/mc25/mc26).** Epoch size, super-epoch size,
pairing rule, and close policy together determine the root set.
Same pins, different partition params → different roots, both
internally consistent. A root claim WITHOUT a pinned partition
descriptor is ambiguous — "the root" is only meaningful relative
to the spec that produced it. Pin the partition descriptor as a
content-addressed object (mc4 T6: validation becomes addressable);
root comparisons must cite it.

**R24. Receipt verification is a pure function; assignment is a
role; trust is an incentive. Do not conflate (mc22 P3–P7).** A
receipt is a pure function of (pin_a, pin_b, method) — anyone
recomputes it in one hash-op, so no checker-checker role exists.
WHAT needs checking is enumerable (level-typed pairs), so checker
ABSENCE is detectable: receipt-count vs expected-pair-count
(mc22 P4 — lie-by-omission shape, mc2). But moral hazard is a
LATENCY problem: a backlogged checker catches errors later, never
less (mc22 P7). The consumption gate (no read without a
receipt-hash on the pin) is the right polarity but has no middle
setting — cheap check ⇒ theater (quarantine ≈ 0.5), expensive
check ⇒ writer starvation (poc-gate F1). The gate relocates the
incentive problem; it does not solve it.

**R25. Audit circularity needs an independent witness namespace
(poc-gate F2).** Receipts verified against the checker's own hand
are self-attestation — fabricated-pair receipts pass. Verification
must dereference a namespace the checked party cannot write
(invariant 2's transport rule at the receipt layer). B1's shape,
sixth address (entropy, salt, targets-covered, lineage, metric,
receipts).

**R26. In matched-budget generational protocols, the alarm baseline
must come from gen-0 held-out data (b14 F4).** R12 fixes labels by
matching budgets — but it also destroys CUSUM's pre-change window:
in generational contamination the change starts at gen 1, so the
warmup generations (first 3) are already post-change. There is no
pre-change window inside the chain. b14: CUSUM-down fired 1–3/40
even on arms collapsing 29–37/40. The baseline must be gen-0
performance on data the chain never trained on (gen-0 fit precedes
contamination by construction). Corollary: the gen-0 held-out set
is itself an anchor-class object — pin it, budget for it, and never
let any generation train on it.

## 5. Trace — "where did you get that percentage?"

```
trace(judgment_hash):
    expand judgment → q, c, e, j, basis[]
    for each basis hash: recurse (depth-limited)
    render: question text, content snippet, encoder id, jev id,
            basis chain with each link's v/conf
```

Every percentage decomposes into: the question, the rendering, the
judge, and the prior judgments it stood on. The web of understanding
is this graph at scale — public, decomposable, inspectable.

Path-carrying cost warning (mc6 P3): basis chains deepen quadratically.
Scale answer = nexus reverse index (mc1 + mc6 P4): one pass builds
"which judgments cite this one." The view is cheap; the viewer is
where the money goes (mc5 P4).

## 6. Predicted breakages (to test in the microcosm)

B1. **Anchor forgery pressure.** Anchors are expensive (real
    outside-the-loop work). A lazy loop will mint judgments whose
    predicted outcomes are then recorded as anchors. Transport rule
    #2 resists, but who audits the auditor? Prediction: this is THE
    failure mode of the bootstrap, and it will look like success
    first (calibration LOOKS good when anchors come from the same
    distribution).

B2. **Basis cycle via metajudgment.** A judges B, B judges C, C judges
    A — through three different questions so it isn't obvious. The
    validator catches it, but only when run. Substrate stores happily.

B3. **Dangling judgment.** Judge a content hash nobody has (mc4 T2,
    mc5 P5). Stores fine; expands only when content appears. A
    judgment can outlive its subject — is a dangling judgment a
    prediction? (Corollary: L0 claims are predictions too, mc7.)
    If the subject NEVER appears, the judgment is unverifiable —
    the graph has no opinion (availability ≠ integrity, mc5 P5).

B4. **Question aliasing.** Two question objects, near-identical text,
    different hashes, judgments split across both. The nexus can't
    correlate them (they're different objects). Semantic dedup is
     ABOVE the substrate — needs an encoder-side similarity judgment,
    which is itself a judgment in the log. Recursion, deliberate.

B5. **Calibration table gaming.** Once calibration is computed per
    (jev, question), a jev is incentivized to avoid questions where
    it scores poorly. Question-selection bias: the scoreboard only
    covers questions the jev chose to answer. Fix: questions are
    assigned by the task layer, not chosen by the jev. (The window
    compiler's job — structural half feeds the semantic half.)

## 7. Smallest demo (next tick)

- 1 question ("does this commit message match its diff?")
- 3 content items (real commits, pre-judged by hand for ground truth)
- 1 encoder (whatever's on the box — even a bag of words; the spec
  doesn't care about encoder quality, only that it's PINNED)
- 1 jev (hand-coded heuristic v1 — also fine; pinned)
- 5 judgments, 2 anchors
- trace() walks and renders one percentage's decomposition
- calibration table after anchors land

Then chip one basis content hash (mc4 T5 probe): every judgment
built on it goes visibly stale in one top-level comparison.
Composition's dividend — integrity propagation — applied to testimony.

## 8. Open questions

- Q1: Should basis[] be ordered (argument sequence) or a set? Ordered
  feels right for trace rendering; unordered dedups. Test in demo.
- Q2: confidence — jev-self-reported or computed (margin over the
  distribution)? Leaning computed: self-reported confidence is the
  sounder's opinion of itself.
- Q3: the log's transport — one repo (shared ref namespace) or
  federated (per-jev repos, pull requests as delivery)? mc5 P5 says
  availability receipts matter once federated. Start centralized;
  federation is a transport swap, not a schema change (same lesson
  as the inbox).
