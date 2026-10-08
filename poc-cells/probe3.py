#!/usr/bin/env python3
"""mc27: nested-cells protocol uniformity under supersede.

Question: does claim/run/receipt work identically at every depth
when a parent cell gets superseded after a deep claim references it?

Scenario:
  L0 (root) has child L1, L1 has child L2.
  Claim L2 (references L1 by hash).
  Then L1 gets superseded (new version committed, binding updated).
  Is the L2 claim still valid? Does the protocol need a re-claim rule?

Store = git object db (same as mc6).
"""

import hashlib
import json
import subprocess
import sys
import os
import tempfile

def pin(obj: dict) -> str:
    """Store object via git hash-object, return its hash."""
    data = json.dumps(obj, sort_keys=True).encode()
    p = subprocess.run(
        ["git", "hash-object", "-w", "--stdin"],
        input=data, capture_output=True, cwd=REPO
    )
    return p.stdout.decode().strip()[:16]

def get(hh: str) -> dict:
    p = subprocess.run(
        ["git", "cat-file", "-p", hh],
        capture_output=True, cwd=REPO
    )
    return json.loads(p.stdout.decode())

REPO = tempfile.mkdtemp(prefix="mc27-")
subprocess.run(["git", "init", "-q"], cwd=REPO)
subprocess.run(["git", "commit", "-q", "--allow-empty", "-m", "init"], cwd=REPO)

# --- Build the chain ---
l0_v1 = pin({"layer": "task", "name": "task-alpha", "data": "original task", "v": 1})
l1_v1 = pin({"layer": "observation", "name": "obs-1", "parent": l0_v1, "data": "original obs", "v": 1})
l2_v1 = pin({"layer": "reading", "name": "read-1", "parent": l1_v1, "data": "original reading", "v": 1})

# Bindings: name -> current hash (the ref namespace, tick 9)
bindings_v1 = {"task-alpha": l0_v1, "obs-1": l1_v1, "read-1": l2_v1}
bindings_hash_v1 = pin({"type": "bindings", "map": bindings_v1})

# Claim at depth 2 (deepest cell)
claim_l2 = pin({"type": "claim", "who": "body-1", "target": l2_v1, "ts": "t0"})

print("=== Initial state ===")
print(f"L0 v1: {l0_v1}")
print(f"L1 v1: {l1_v1}")
print(f"L2 v1: {l2_v1}")
print(f"Claim on L2: {claim_l2}")

# --- Supersede L1 ---
l1_v2 = pin({"layer": "observation", "name": "obs-1", "parent": l0_v1, "data": "corrected obs", "v": 2})
bindings_v2 = {"task-alpha": l0_v1, "obs-1": l1_v2, "read-1": l2_v1}
bindings_hash_v2 = pin({"type": "bindings", "map": bindings_v2})

print(f"\n=== After L1 supersede ===")
print(f"L1 v2: {l1_v2}")
print(f"Bindings v1: {bindings_hash_v1}")
print(f"Bindings v2: {bindings_hash_v2}")

# --- Probe 1: does the claim still resolve? ---
resolved = get(claim_l2)
target = get(resolved["target"])
print(f"\nP1: claim target resolves to: {target['name']} v{target['v']}")
print(f"    parent of target: {target['parent']}")
print(f"    current binding for obs-1: {bindings_v2['obs-1']}")
print(f"    → claim references L1 v1, binding says L1 v2")
print(f"    → claim is STALE relative to binding (tick 9 finding confirmed at depth)")

# --- Probe 2: can we run/receipt the stale claim? ---
run_result = pin({"type": "run", "claim": claim_l2, "output": "processed reading data", "ts": "t1"})
receipt = pin({"type": "receipt", "run": run_result, "claim": claim_l2, "status": "ok", "ts": "t2"})
print(f"\nP2: run on stale claim: {run_result}")
print(f"    receipt: {receipt}")
print(f"    → protocol does NOT block stale claims. Run+receipt proceed normally.")
print(f"    → staleness is invisible at the claim/run/receipt layer")

# --- Probe 3: what does "done" mean now? ---
# The protocol rule from mc6 F1: "done = THIS run's receipt exists"
# But the receipt references a stale claim, which references a stale parent.
done_check = {
    "claim": claim_l2,
    "receipt": receipt,
    "target_current_binding": bindings_v2["read-1"],
    "target_resolved_hash": resolved["target"],
    "is_current": resolved["target"] == bindings_v2["read-1"],
}
print(f"\nP3: done check:")
print(f"    claim target == current binding? {done_check['is_current']}")
print(f"    → YES (L2 wasn't superseded, only its parent)")
print(f"    → 'done' is claim-local, not chain-local")

# --- Probe 4: the real question — should it be chain-local? ---
# If L1 was corrected because the observation was WRONG,
# then the reading built on it (L2) is also suspect.
# But the graph doesn't know that — L2's hash is unchanged,
# its parent pin is unchanged, its claim is valid.
# The SEMANTIC staleness (parent superseded → child suspect)
# is not captured by hash comparison.
print(f"\nP4: semantic chain staleness:")
print(f"    L2's parent (L1 v1) is superseded by L1 v2")
print(f"    L2's content was derived from L1 v1's (wrong) data")
print(f"    But L2's hash is bit-identical — the store sees no change")
print(f"    → hash-staleness ≠ semantic-staleness at depth")
print(f"    → the protocol is uniform (same shape at every layer)")
print(f"    → but uniform ≠ sufficient: parent-supersede should")
print(f"      invalidate child claims, and nothing in the graph says so")

# --- Probe 5: can we detect it with an index? ---
# Build parent→children index from all objects (including loose).
p = subprocess.run(
    ["git", "cat-file", "--batch-all-objects", "--batch-check=%(objectname)"],
    capture_output=True, cwd=REPO
)
all_objs = set()
for line in p.stdout.decode().strip().split("\n"):
    if line.strip():
        all_objs.add(line.strip()[:16])

children_of = {}
for obj_hash in all_objs:
    try:
        obj = get(obj_hash)
    except Exception:
        continue
    if isinstance(obj, dict) and "parent" in obj:
        parent = obj["parent"]
        children_of.setdefault(parent, []).append(obj_hash)

stale_parents = set()
for name, hh in bindings_v2.items():
    if name in bindings_v1 and bindings_v1[name] != hh:
        stale_parents.add(bindings_v1[name])

affected_children = set()
for sp in stale_parents:
    affected_children.update(children_of.get(sp, []))

print(f"\nP5: index-based detection:")
print(f"    stale parent hashes: {stale_parents}")
print(f"    affected children: {affected_children}")
print(f"    L2 ({l2_v1}) in affected set? {l2_v1 in affected_children}")
print(f"    → DETECTED, but only via the bindings diff + child index")
print(f"    → cost: one bindings-compare + one index pass")
print(f"    → this is ABOVE the substrate: the store holds both versions")
print(f"      forever and has no opinion about which is current")

print(f"\n=== SUMMARY ===")
print("Protocol uniformity at depth: CONFIRMED structurally (claim/run/receipt")
print("work identically at depth 2 as at depth 0).")
print()
print("BUT: uniform protocol ≠ uniform validity. The claim at depth 2")
print("remains 'done' by the protocol's own rules even when its parent")
print("is superseded. Semantic chain-staleness requires:")
print("  1. A bindings namespace (name→current hash) — already in SPEC")
print("  2. A supersede-event log (old_hash → new_hash, with reason)")
print("  3. A propagation rule: parent supersede marks child claims SUSPECT")
print("     (not invalid — the child might still be right)")
print("  4. A consumer-side check: before trusting a claim, walk the")
print("     parent chain and check each against current bindings")
print()
print("LAW, 31-for-31: substrate stores; layer above constrains.")
print("Variant: at depth, 'constraint' includes CHAIN-LOCAL validity —")
print("the graph stores parent-child edges but has no opinion about")
print("whether the parents are current. Currency is a bindings-layer")
print("fact, and chain-currency is a bindings-walk fact.")
