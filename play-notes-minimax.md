# Play notes: jev-semantic v0 (MiniMax, 2026-10-07)

Casey asked: what's good, and what's AMAZING? I cloned it, read every
file, stress-tested to 1M judgments, extended the window compiler, and
ran a demo with two judges. Honest report below.

## What's GOOD

**The triple-hash key.** `(subject, question, judge)` — all blob hashes,
no central registry, no coordination to mint a key. It's the right
shape. Adding the *question* to the key (not just content+judge) is what
makes the log a conversation instead of a scoreboard.

**The append-only log.** Simple, auditable, honest. 1M judgments =
126MB raw TSV, **36MB git-packed**. The "one ROM" decision is validated
by measurement: the semantic log lives happily inside git at 3.5x
compression. No second system needed until the workload says so.

**window.py v0.** Compiles task + nexus + activity. It works. It's the
rasterizer — PLATO→NES in one script.

**The test.** Format validation on the log line. Small, correct, passes.

## What's AMAZING

### 1. The disagreement table (the demo)

I extended the window compiler (`window2.py`) with a judgments section
and ran it on a fake deploy-key-rotation task with two judges. The
output:

| question | student | big model |
|---|---|---|
| root (go?) | settled + (0.85) | settled + (0.70) |
| reversible? | **CONFLICT** (0.46/0.09/0.45) | **settled −** (0.70) |
| touches secrets? | settled + (0.93) | — |

Both judges say *go*. But they **disagree on reversibility** — the
student is torn, the big model says NO. The window doesn't average them
(a +1 and a −1 averaged to 0 looks like "nothing here" when it's
conflict). It shows both, side by side.

This is the floating gate made visible. The agent's brief now says:
"go ahead, but the reversibility question is contested — and that's the
thing that matters for a key rotation." The disagreement IS the
escalation signal. I didn't expect a 5-line fake log to be this
compelling. The table is the product.

### 2. The materialized current-state: 5ms vs 2117ms

Stress test at 1M judgments. The "money query" — latest judgment per
(subject, question) for 200 subjects:

- Naive (ORDER BY ts, indexed): **2117ms**
- Materialized `current_j` table (latest per key, precomputed): **5ms**

**400x.** The log stays append-only (the truth); the materialized table
is the read path (the cache). Opus's "index is a rebuildable cache,
never a source of truth" is right — but the *shape* matters: don't index
the log, materialize the current state. The log answers "what happened";
the materialized table answers "what does the Jev see right now."

The refresh protocol is the open question: rebuild on every batch
(11.7s at 1M — fine for hourly, not for per-tick), or incremental
upsert per batch (O(batch), not O(log)). Incremental wins; the batch
boundary is the natural commit point.

### 3. The question is the row

Without the question hash in the key, the demo's table has one row.
With it, three. The question is what turns a judgment into something
you can *argue with*. "Settled + on root" is a score. "Conflict on
reversibility" is a conversation. The key design earns its keep here.

## Honest gaps

1. **One judge in production.** v0's live log has only the student.
   Disagreement detection — the amazing part — needs 2+ judges. The
   demo faked the second judge. Priority: get a big-model judge logging
   on the same subjects.

2. **Open questions is a stub.** `window2.py` section 4 doesn't derive
   never-asked (subject, question) pairs yet. Needs the question tree
   wired in: for each subject in the window, which questions in the
   active subtree were never asked?

3. **Index size.** 578MB SQLite (log + 3 indexes + materialized) for 1M
   judgments vs 36MB packed TSV. 16x. Fine on Oracle, heavy on the edge.
   The tiering needs design: hot materialized on the box, cold packed
   in git, warm cache in between.

4. **The judge is a string, not a hash.** `judge_log.py` writes
   `"intuition-student-v1"` where the design wants a manifest blob hash.
   Works for v0, but the manifest (`judges/intuition-student-v1.md`)
   needs its hash computed and referenced.

## The one most amazing thing

**The disagreement table.** Not the log, not the key, not the 400x —
the moment two judges disagree on the same question and the window shows
both instead of averaging. That's the entire philosophy in one table:
conflict is signal, not noise. Everything else is plumbing; the table
is the product.

## Measurements (all local, this machine)

| | 100k | 1M |
|---|---|---|
| raw TSV | 14MB | 126MB |
| git-packed | — | 36MB |
| grep 200-subject scan | 0.31s | 2.91s |
| sqlite build | 0.8s / 35MB | 11.6s / 324MB |
| money query (naive) | — | 2117ms |
| money query (materialized) | — | **5ms** |
| materialized build | — | 11.7s |
| question→judgments | — | 2ms |

## Files added in this play session

- `window2.py` — window compiler v1 with judgments section (demo-grade,
  reads real TSV, fake data in `demo-log.tsv` / `demo-task.md`)
- `play-notes-minimax.md` — this file
