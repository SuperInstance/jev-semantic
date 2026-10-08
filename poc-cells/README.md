# poc-cells — nested addressable cells

Microcosm 6. Casey's seed: an addressable cell is an addressable cell —
task, observation, or sensor reading; nesting depth is a question of
hash-encoding resolution (IPv4 vs IPv6). Store = this repo's own git
object db (git framing per mc1).

Run: `python3 probe.py` (writes probe-output.txt).

## What worked

- **P1 nesting.** task → observations → readings, all content-addressed.
  A reading hash reaches 3 levels from the task hash alone. Reading
  shared by two observations dedups for free (mc4's T1 at cell scale).
- **P2 same protocol every layer.** claim → run → receipt is
  structurally identical at reading, observation, and task layers. No
  layer demanded a different cell shape. The "identical cell protocol"
  hypothesis SURVIVES structurally.
- **P4 nexus spin.** One pass over `cat-file --batch-all-objects` builds
  a reverse index; transitive closure from a reading lists every kind
  it lives under (observation, task, wrap0..wrap5). The spin works —
  but see below.

## What broke (the findings)

1. **Cardinality is not in the hash (P2 stress).** Two identical intents
   → one claim hash. Two runs of that claim are representable (both ref
   it), but "claim has descendants ⇒ done" now FALSELY PASSES for an
   unfinished branch. Content-addressing cannot distinguish "same intent
   twice" from "one intent"; multiplicity lives only in parent refs —
   above the substrate. The fix is protocol rule, not graph structure:
   a run is done iff *its own* receipt exists, never by claim ancestry.
   (This is mc2's transport-policy finding at cell scale, again.)
2. **Level is not stored (P4).** One nexus pass = direct parents only.
   "See every level it lives at" needs transitive closure, and the
   levels are reconstructed by BFS, not carried by the cells. Depth is
   a property of the walk, not the address. Compare mc3: the tree gives
   depth free, locks the view; the tensor/cells give re-projection free,
   charge for every constraint — depth included.
3. **Full-path addressing loses at depth 3 (P3).** 40-hex path per hop
   vs 72–140B cells: the path costs more than the payload by the
   reading layer. The IPv4/v6 analogy resolves like this: the hash has
   plenty of address *space*; the cost is carrying the *path*. Index-
   mediated addressing (walker follows one hash per hop) scales —
   6 extra wrap levels, 31 objects, no strain. The cost moved entirely
   into the walker/index. Same law as mc5's bank window: the view is
   cheap, the viewer is where the money goes.

## Cross-microcosm law — now six for six

**The substrate stores; the layer above constrains.** This tick's
variants: cardinality/staleness semantics (finding 1), level/depth
(finding 2), path cost (finding 3) — all live above. The cell protocol
being identical at every layer is real, but it buys addressing, not
semantics. Semantics remain a per-layer policy choice pinned beside the
cells (mc4's T6: pin the validator as an object, agree on its hash).

## Corollary for the reading layer (physical bodies lane)

A sensor reading can't be claimed before it exists in any honest sense —
the L0 "claim" is a prediction, and readings can violate it (sensor
says 25°C, intent said ~21). Nothing in the graph flags the surprise.
Surprise/judgment is necessarily above the substrate — which is exactly
the Jev's job in the embeddings lane: judgment distributions pinned
beside the cells they judge.
