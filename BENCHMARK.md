# BENCHMARK.md — intuition-student-v1 latency record

The judge's cost claims live here. Every figure below names its
hardware, runtime, thread count, and statistic. Last corrected
2026-10-22 (F4 audit); see "History of the ~7 ms claim" at the bottom.

## How to run the published benchmark

The benchmark is `bench.py` in `SuperInstance/agent-inbox`,
`payloads/intuition-bench/` (public since 2026-10-07, alongside the
model and tokenizer — hashes in `judges/intuition-student-v1.md`):

```
git clone https://github.com/SuperInstance/agent-inbox.git
cd agent-inbox/payloads/intuition-bench
pip install onnxruntime tokenizers     # no torch, no GPU needed
python3 bench.py                       # writes bench_result.json
```

Method (from `bench.py` itself): 5 fixed short prompts; each encoded
with the published tokenizer, truncated to 64 ids, right-padded with
`[PAD]=0` into a `[1,64]` int64 tensor named `ids`; 15 warmup runs
(3 passes over the 5 prompts) then 50 timed `sess.run` calls per
config, timed with `time.perf_counter` around each single call;
reports mean / p50 / p95 / throughput. Two configs: 1 and 4 intra-op
threads (inter_op fixed at 1), CPUExecutionProvider. It also prints
one sample-logit vector (1-thread session) rounded to 4 decimals.

## Recorded results

| machine | arch | runtime | 1 thread | 4 threads | date / source |
|---|---|---|---|---|---|
| Jetson (Cortex-A78AE, 6-core) | aarch64 | ort 1.31.0, py 3.12.3 | **33.5 ms p50** (mean 33.6, p95 34.3) | **12.3 ms p50** (mean 13.3, p95 20.5) | 2026-10-22, F4 audit re-run of unmodified `bench.py` |
| same board, re-verification | aarch64 | ort 1.31.0, py 3.12.3 | 33.47 ms p50 (mean 33.49, p95 33.65) | 11.77 ms p50 (mean 11.83, p95 12.30) | 2026-10-22, audit-fixes branch, same method |
| laptop (training node) | x86_64 | ort 1.30 | 6.2 ms **mean** | 2.2 ms **mean** | 2026-10-07, `agent-inbox done/013…/task.md` (means only; no p50 recorded) |
| prospector cloud box (Kimi, shared vCPUs) | x86_64 | ort 1.30.0 | 25.78 ms p50 (mean 26.27) | 64.59 ms p50 (mean 65.71) | 2026-10-08, `done/013…/result.md` + `bench_result.json` |
| laptop, training-time probe | x86_64 | torch / ort, 1 thread, 64 tokens | 7.5 ms torch / **7.3 ms ONNX** | — | 2026-10-06, `done/009…/result.md` |

**The recorded ARM figure is 12.3 ms p50 at 4 threads** (Jetson
Cortex-A78AE, onnxruntime 1.31.0). There is no measured ARM result
anywhere near 7 ms in the public record.

Notes on the table:

- The prospector row's 4-thread figure being *slower* than 1-thread is
  shared-vCPU throttling on that cloud box; its own result notes say
  "do not read it as an architecture signal".
- Sample logits from the benchmark's logit probe agree at the printed
  4-decimal precision across all three environments that recorded one
  (x86 laptop ort 1.30, x86 cloud ort 1.30.0, aarch64 Jetson ort 1.31:
  `[0.0339, −0.0066, 0.2419]`). That is 4-decimal agreement, not
  bit-identity — see DETERMINISM.md.
- `bench.py` prompts are **bare strings** — no `[STATE]`/`[QUESTION]`
  wrapper — so the benchmark does not measure the production input
  path (see INPUT-CONTRACT.md). The mechanics (64-token window,
  padding, `[1,64]` shape) are identical, and every call pays the full
  padded 64-token window, so the numbers bound the short-prompt
  serving cost; long-content cost is the same per call because of the
  64-token truncation.

## History of the ~7 ms claim

Until 2026-10-22 the manifest said "latency: 7.0ms (4-thread ARM)" and
the README "judges at 7ms on ARM". The F4 audit (2026-10-22)
established that this figure was never measured on ARM: the benchmark
task's ARM leg was explicitly BLOCKED (`done/013…/result.md`), and the
only ~7 ms number in the record is 7.3 ms — ONNX, **1 thread, x86_64
laptop** (`done/009…/result.md`). The "7.0ms (4-thread ARM)" line
relabelled that x86 figure. The first ARM measurement on record is the
Jetson row above (12.3 ms p50 at 4 threads — 1.76× the withdrawn
claim). Single-digit ms on a flagship ARM core remains conjecture, not
artifact.
