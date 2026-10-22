# DETERMINISM.md — intuition-student-v1 determinism and precision contract

Canonical statement (2026-10-22, F4 audit + re-verification on the
audit's Jetson). The manifest (`judges/intuition-student-v1.md`)
points here; claims elsewhere should defer to this file. This replaces
the manifest's former line "determinism: bit-identical logits across
x86_64 and aarch64", which overstated the record and is withdrawn.

## Precision

The model is plain **float32**: ONNX opset 17, weights stored as raw
fp32 external data (`intuition_student.onnx.data`), all 6,803,721
weight values fp32, the only non-float graph constants being 122 int64
shape/index values introduced by export. **No quantization ops exist
in the graph** (verified by full node census — no
QuantizeLinear/DequantizeLinear/QDQ/int8 anywhere). There is no
quantization contract to publish because no quantization was ever
done.

## The contract: deterministic per configuration

**Bit-exact, verified (same configuration):**

- same session, same input, repeated runs (20×) — bit-identical;
- fresh sessions of the same build on the same machine — bit-identical;
- 1 vs 4 intra-op threads — bit-identical.

**Not bit-exact across runtime settings (same machine, same weights):**

- changing only the ORT graph-optimization level shifts logits by
  ~1×10⁻⁷ (measured 2026-10-22: 1.08×10⁻⁷ BASIC-vs-ALL, 1.38×10⁻⁷
  DISABLE_ALL-vs-ALL; an independent re-check the same day on a
  different probe gave 2.4/3.6×10⁻⁷ — same scale, probe-dependent);
- published torch weights (`.pt`, torch 2.14 CPU) vs published ONNX
  (ort 1.31) with identical weights: 1.1–2.4×10⁻⁷ per logit —
  ULP-scale kernel divergence between runtimes.

**Across architectures:** no full-precision cross-architecture logit
record exists (all recorded vectors are 4-decimal). At the judge's
**four-decimal output convention**, exact agreement on the benchmark
sample probe across three machines, two architectures, two ORT
versions — x86_64 laptop (ort 1.30), x86_64 cloud (ort 1.30.0),
aarch64 Jetson (ort 1.31): `[0.0339, −0.0066, 0.2419]`. The
full-precision aarch64 vector behind those rounded values is
`0.03388854…, −0.00664945…, 0.24185745…` (F4 audit). Residual caveat:
a logit lying exactly on a 4-decimal rounding boundary could round
differently under 10⁻⁷ shifts — untested and inherently statistical.

## Policy

- **Supported claims:** deterministic reruns at fixed configuration
  (bit-exact); argmax-level and four-decimal-level agreement across
  the tested machines/architectures/ORT versions.
- **Not supported:** "bit-identical logits" across architectures,
  runtimes, or settings. Do not make unqualified bit-level claims.
- For re-judge-and-subtract workflows (compare a new student against
  the log): pin the ORT version, thread count, and graph-optimization
  level, and treat per-logit differences below 1×10⁻⁶ as runtime
  noise, not judgment changes. Comparisons at the four-decimal output
  convention are the documented cross-platform basis.
