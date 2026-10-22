# intuition-student-v1

- architecture: micro transformer encoder, d256, 6 layers, 8 heads
- params: 6.80M — 6,803,843 initializer values in the published graph (6,803,721 fp32 weights + 122 int64 export constants)
- output: 3-way softmax over (-1, 0, +1)
- training: KL vs teacher soft probs, 3x weight on H > 1.0
- latency (measured; full record in BENCHMARK.md): aarch64 Jetson Cortex-A78AE, onnxruntime 1.31.0 — 12.3 ms p50 at 4 intra-op threads, 33.5 ms p50 at 1 thread (2026-10-22); x86_64 laptop, onnxruntime 1.30 — 6.2 ms mean at 1 thread, 2.2 ms mean at 4 threads. The former "7.0ms (4-thread ARM)" was never measured on ARM and is withdrawn.
- determinism (canonical statement in DETERMINISM.md): fp32, no quantization; deterministic per configuration — bit-exact reruns/sessions/thread counts at fixed settings, ~1e-7 logit shifts across runtime settings (graph-optimization level, torch-vs-ONNX), exact agreement at the four-decimal output convention across x86_64/aarch64
- encoder: BPE 8k tokenizer (tokenizer.json)
- output convention: fixed order (neg, zero, pos), four decimals
- input contract: INPUT-CONTRACT.md

## artifact

Public since 2026-10-07 in `SuperInstance/agent-inbox`, `payloads/intuition-bench/`, byte-identical (same git blob SHAs) to `SuperInstance/intuition@eeb1154` (`models/intuition_student{.onnx,.onnx.data}`, `models/tokenizer/tokenizer.json`):

- `intuition_student.onnx` (graph, opset 17) — 47,336 B — sha256 `0fc8b8dcb1dac759f946be00fc3cbbb7efe593fd136630152efde2646ca0d750` — git blob `ad57423c128d790d756a8c3f3d304a198f7ef5f9`
- `intuition_student.onnx.data` (external weights) — 27,262,976 B — sha256 `53da6a3e7265e92fed153e9e228e793f77224efd85ce2bb83d55b12439bff587` — git blob `44fac9eeb0f370735d3886314b6a9a7cb721b257`
- `tokenizer.json` (BPE, vocab exactly 8000) — 556,800 B — sha256 `117d0e213560b4c0224158c932c74852be9847119961b803d4e8eaaa7b99c842` — git blob `97ecbf83c0c0970b966cb71d00bb2883e8fac2d2`

All weights are float32 (external-data layout); no quantization ops exist in the graph. Input `ids` int64 `[batch,64]`; output `logits` fp32 `[1,3]`. Hashes and sizes verified 2026-10-22 against the published payload (F4 audit, re-verified on the audit's Jetson).

Provenance: trained by `SuperInstance/intuition` `src/train_student.py` at `eeb1154` ("intuition student: trained laser rangefinder (task 009)", 2026-10-06), seed 7, 3100-example teacher corpus (`data/graded.jsonl`). The v1 torch weights (`intuition_student.pt`), the v1 ONNX export script, and the v1 training log are published only in the intuition repo, not in agent-inbox.
