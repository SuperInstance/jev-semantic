# jev-semantic

The semantic layer for the Jev: a judgment log, a window compiler, and
the question tree. The PLATO layer to git.pp's NES substrate.

## What this is

- **judge_log.py** — every Jev judgment, append-only:
  `(timestamp, subject, question, judge) → (neg, zero, pos)`.
  The log is the seed; the graph grows from it.
- **window.py** — the semantic projector v0. Compiles an agent's window:
  the task + nexus-linked precedents + recent activity. Not "search the
  repo" — *compile the window*.
- **questions/** — the question tree. Each file's identity is its blob
  hash. Hierarchy by directory nesting. `root.md` is the one question
  every Jev can condition on.
- **judges/** — judge manifests. Each names the encoder hash, the Jev
  hash, and the output convention.

## The key

Every judgment is keyed by `(subject, question, judge)` — all blob
hashes. A judgment is a measurement, not a derivation: verify by
tolerance, not by hash. Two bodies may log the same key; their
disagreement is data.

## Status

v0. The student judges at 7ms on ARM, bit-identical across
architectures. The log is live. The graph comes next.
