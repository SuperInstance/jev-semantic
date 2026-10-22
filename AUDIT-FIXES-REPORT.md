# AUDIT-FIXES-REPORT — closing the F4 audit's gap list

Branch `audit-fixes`, 2026-10-22. Scope: the F4 audit
(`JEV-READINESS.md`, 2026-10-22) gap items 1–4 as instructed; no model
changes, no retraining, no skew fixes (documentation only), no new
dependencies. Everything below was verified first-hand on the audit's
Jetson before being written: payload re-hashed, graph re-inspected,
benchmark re-run, determinism re-checked (details at the end).

## Files changed

| file | change |
|---|---|
| `judges/intuition-student-v1.md` | latency line corrected; determinism line replaced; params made exact; artifact section added (hashes, sizes, blob SHAs, location, provenance); pointers to INPUT-CONTRACT / BENCHMARK / DETERMINISM |
| `README.md` | status paragraph corrected (latency + determinism) |
| `opus-the-amazing-thing.md` | dated correction note added after the header; **original essay text unmodified** |
| `BENCHMARK.md` | **new** — how to run the published benchmark, method, all recorded results with environment/statistic labels, history of the withdrawn ~7 ms claim |
| `INPUT-CONTRACT.md` | **new** — serve path, tokenizer, model I/O, training templates verbatim, train/serve skew stated plainly, reproduction snippet |
| `DETERMINISM.md` | **new** — canonical determinism/precision statement (referenced from the manifest) |
| `AUDIT-FIXES-REPORT.md` | **new** — this file |

## Claims corrected (old text → new text)

**1. Latency — manifest (`judges/intuition-student-v1.md:7`)**

- old: `latency: 7.0ms (4-thread ARM), 6.2ms (1-thread x86)`
- new: measured figures with hardware, runtime, thread count,
  statistic — 12.3 ms p50 at 4 intra-op threads and 33.5 ms p50 at 1
  thread on aarch64 (Jetson Cortex-A78AE, onnxruntime 1.31.0,
  2026-10-22); 6.2 ms mean at 1 thread and 2.2 ms mean at 4 threads on
  x86_64 laptop (onnxruntime 1.30); the "7.0ms (4-thread ARM)" figure
  explicitly withdrawn as never measured; full record in BENCHMARK.md.

**2. Latency — README (`README.md:29-30`)**

- old: `The student judges at 7ms on ARM, bit-identical across
  architectures.`
- new: 12.3 ms p50 on aarch64 (4 intra-op threads), 6.2 ms mean at
  1 thread on x86_64, pointers to BENCHMARK.md; determinism restated
  per configuration with pointer to DETERMINISM.md.

**3. Latency — essay (`opus-the-amazing-thing.md:7,10`)**

- old (kept verbatim): "costs 7 ms" / "any empty cell is 7 ms away"
- action: dated correction note at the top (flag, not rewrite — it is
  a 2026-10-07 document and the record of what was said then); the
  note gives the measured figures and links BENCHMARK.md.

**4. Determinism — manifest (`judges/intuition-student-v1.md:8`)**

- old: `determinism: bit-identical logits across x86_64 and aarch64`
- new: fp32, no quantization, deterministic **per configuration** —
  bit-exact reruns/sessions/thread counts at fixed settings, ~1e-7
  shifts across runtime settings, exact agreement at the four-decimal
  output convention across x86_64/aarch64; canonical statement in
  DETERMINISM.md.

**5. Determinism — README (`README.md:29-30`)** — covered in #2.

**6. Determinism — essay (`opus-the-amazing-thing.md:8,27`)** — covered
in #3's correction note ("bit-identical everywhere" → per
configuration; re-judge-and-subtract survives with pinned runtime
config and a 1e-6 noise floor).

**7. Manifest does its README job (`README.md:17-18`: "Each names the
encoder hash…")** — artifact section added: the three payload files
with size, full sha256, git blob SHA, public location
(`SuperInstance/agent-inbox` `payloads/intuition-bench/`), and
provenance (byte-identical to `SuperInstance/intuition@eeb1154`,
training details). `params: 6.80M` now carries the exact graph census:
6,803,843 initializer values (6,803,721 fp32 weights + 122 int64
export constants).

## Full-repo claim sweep (fix or flag, every hit)

Grep over all files on `main` for `7 ms / 7.0 / 7.3 / 6.2 / latency /
bit-identical / ARM / aarch64 / x86`:

- `judges/intuition-student-v1.md`, `README.md` — **fixed** (#1, #2, #4).
- `opus-the-amazing-thing.md` — **flagged** via correction note (#3).
- `play-notes-minimax.md:49,113` ("5ms vs 2117ms") — SQLite money-query
  benchmark, unrelated to judge latency; no change.
- `play-notes-minimax.md:92-95` (limitation #4: manifest "needs its
  hash computed and referenced") — a dated 2026-10-07 record; the gap
  it names is now closed by the artifact section. Left as written.
- `poc-cells/probe3.py:113` ("hash is bit-identical") — about git
  object hashes, not model determinism; no change.
- `semantic/SPEC.md`, `semantic/large-jev-design.md` — "latency"
  refers to alarm latency in the bootstrap-loop design; "4-core ARM
  box" is target hardware for the large-Jev loop, not a judge latency
  claim; no change.
- `SETUP.md` — node provisioning; its pointer to the public payload is
  what the audit confirmed correct; no change.
- `origin/gift/qthe-tavern-findings` (branch) — carries the same three
  wrong claims (README:29, manifest:7-8, essay:7-10) at its fork
  point. Not modified: it is a frozen gift branch; the correction
  lands on `main` via this branch. **Flagged here.**
- Outside this repo, flagged for the operator: `beam-quilt`
  `README.md:74` still reads "6.8M parameters, ~7 ms on ARM for short
  typed profiles", and `agent-inbox done/013…/result.md` says
  "Bit-level agreement … ✅" where the recorded evidence is 4-decimal
  agreement (the laptop vector it compares against was itself rounded
  to 4 decimals). Both are other repos; out of scope for this branch.

## Findings that refine (nothing contradicts) the audit's facts

1. **"Every tensor dtype=1 (float32)" is loose.** The graph has 105
   initializers: 82 fp32 tensors (6,803,721 values) **and 23 int64
   tensors** (122 values — `arange` positions, reshape shapes, slice
   indices introduced by export). All *weights* are fp32 and the
   no-quantization finding stands exactly (zero QuantizeLinear/
   DequantizeLinear/QDQ nodes, re-verified by full node census). The
   manifest states the census precisely rather than "every tensor".
2. **The x86 laptop figures are means, not p50s.** `done/013…/task.md`
   records "1-thread 6.2 ms mean, 4-thread 2.2 ms mean"; no percentile
   was recorded for that run. The manifest and BENCHMARK.md label them
   as means accordingly.
3. **The audit's ~1e-7 divergence figures reproduce at the same scale
   but not the same values on different probes** (audit: 1.08/1.38×10⁻⁷;
   my re-check on a different input: 2.4/3.6×10⁻⁷). Expected for
   ULP-scale effects; DETERMINISM.md records both with that caveat.
4. **benchmark re-run agrees**: p50 33.47 ms (1-thread) / 11.77 ms
   (4-thread) on this Jetson vs the audit's 33.5 / 12.3 — recorded in
   BENCHMARK.md as an independent re-verification row.

## Known gaps intentionally left open (with reasons)

- `judge_log.py:40` still writes the literal string
  `intuition-student-v1` in the judge column rather than a manifest
  blob hash (audit gap-list item 1's second half). Fixing it is a code
  change to the live log format; outside this brief's scope (docs +
  manifest). The limitation remains recorded in
  `play-notes-minimax.md` #4 and INPUT-CONTRACT.md §3.
- The v1 ONNX export script and v1 training log remain unpublished
  (they exist only for v2/v3 in the intuition repo); the manifest's
  artifact section now says so explicitly.
- The train/serve skew is **documented** (INPUT-CONTRACT.md §5), not
  fixed, per the brief's non-goals.

## Verification performed for this report (2026-10-22, this Jetson)

- sha256 + size + `git hash-object` of the three payload files,
  cross-checked between two independent downloads and the agent-inbox
  clone; blob SHAs matched `intuition@eeb1154` exactly (byte-identity
  re-confirmed).
- ONNX graph census (onnx 1.23.2): initializer count/values/dtypes,
  opset 17, input `ids` int64 `[batch,64]`, output `logits` fp32
  `[1,3]`, zero quantization ops; tokenizer vocab exactly 8000,
  specials `[PAD]=0 [UNK]=1 [STATE]=2 [QUESTION]=3`, no
  normalizer/post-processor/decoder.
- Unmodified `bench.py` re-run (ort 1.31.0, python 3.12.3): rows in
  BENCHMARK.md; sample logits identical at 4 decimals to all recorded
  vectors.
- Determinism: 20× same-session repeats and 1-vs-4-thread runs
  bit-identical; graph-opt level shifts at 2.4/3.6×10⁻⁷ (probe-dependent,
  see finding 3).
- `tests/test_log_format.py` passes (no code changed; sanity only).

`JEV-READINESS.md` and `BRIEF.md` were left untracked on purpose: the
audit states it was "not written inside any repository", and the brief
is the operator's instruction, not repo content.
