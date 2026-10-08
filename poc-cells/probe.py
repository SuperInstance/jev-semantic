#!/usr/bin/env python3
"""poc-cells: nested addressable cells — one cell protocol, every layer.

Casey's seed: an addressable cell is an addressable cell — task,
observation, or sensor reading. How you get to a cell is a question of
hash-encoding resolution (IPv4 vs IPv6). Microcosm questions:
  P1 nested cells — cells contain cells contain cells, all hashed.
  P2 same protocol every layer — claim/run/receipt at L0,L1,L2. If a
    layer needs a different protocol, that's a finding.
  P3 resolution limit — how deep before addressing costs more than the
    cells are worth? Practical limit, not theoretical.
  P4 nexus spin — given a deeply nested hash, see EVERY level it lives
    at, in one pass.

Store = this repo's own git object db (git framing, per mc1: the nexus
is content x framing, so pin through git hash-object).
"""
import json, subprocess, pathlib

ROOT = pathlib.Path(__file__).resolve().parent

def git(*args, stdin=None):
    return subprocess.run(["git", "-C", str(ROOT), *args], input=stdin,
                          capture_output=True, check=True).stdout

def pin(o):
    blob = json.dumps(o, sort_keys=True, separators=(",", ":")).encode()
    return git("hash-object", "-w", "--stdin", stdin=blob).decode().strip()

def cell(h):
    return json.loads(git("cat-file", "-p", h))

# The protocol — identical at every layer: claim -> run -> receipt.
# claim refs INTENT (what will exist), run refs claim + produces the
# subject, receipt refs run and attests. (intent-before-effect, mc2.)
def lifecycle(intent_obj, layer):
    claim = pin({"kind": "claim", "layer": layer, "intent": intent_obj})
    return claim  # run/receipt built by callers who have the subject

def run_receipt(claim, subject, layer, result="ok"):
    run = pin({"kind": "run", "layer": layer, "of": claim, "made": subject})
    rcpt = pin({"kind": "receipt", "layer": layer, "of": run, "result": result})
    return run, rcpt

out = []
def log(*a):
    s = " ".join(str(x) for x in a)
    out.append(s); print(s)

# ---------- P1: nested cells ----------
# L0 readings (sensor), L1 observations (ref readings), L2 task (ref observations)
r1 = pin({"kind": "reading", "t": "2026-10-07T16:20:00Z", "v": 21.5, "unit": "C"})
r2 = pin({"kind": "reading", "t": "2026-10-07T16:20:30Z", "v": 21.7, "unit": "C"})
r3 = pin({"kind": "reading", "t": "2026-10-07T16:20:60Z", "v": 22.1, "unit": "C"})
obs_a = pin({"kind": "observation", "refs": [r1, r2], "label": "warmup"})
obs_b = pin({"kind": "observation", "refs": [r2, r3], "label": "rise"})
task = pin({"kind": "task", "refs": [obs_a, obs_b], "label": "oven probe"})

log(f"P1 nested cells: task={task[:12]} obs={obs_a[:12]},{obs_b[:12]} readings={r1[:12]}..")
depth = {"reading": 0, "observation": 1, "task": 2}
def walk(h, d=0):
    c = cell(h)
    log("  " * d + f"[{c['kind']}] {h[:12]}")
    for r in c.get("refs", []):
        walk(r, d + 1)
walk(task)
log(f"P1 ok: {r1[:12]} reachable at 3 levels from task hash alone")

# ---------- P2: same protocol every layer ----------
log("P2 identical claim/run/receipt at L0,L1,L2:")
lifecycles = {}
for layer, intent in [("reading", {"will": "sample at :30"}),
                      ("observation", {"will": "observe 2 readings"}),
                      ("task", {"will": "track oven probe"})]:
    claim = lifecycle(intent, layer)
    subj = {"layer": layer, "payload": intent["will"]}
    sh = pin(subj)
    run, rcpt = run_receipt(claim, sh, layer)
    lifecycles[layer] = (claim, run, rcpt)
    log(f"  {layer}: claim={claim[:8]} run={run[:8]} receipt={rcpt[:8]}")

# stress: two readings with IDENTICAL intent — same claim hash?
c1 = lifecycle({"will": "sample hourly"}, "reading")
c2 = lifecycle({"will": "sample hourly"}, "reading")
log(f"P2 stress: identical intents -> same claim? {c1 == c2}  ({c1[:8]})")
# both runs ref the same claim — can the graph tell two samplings apart?
s1 = pin({"v": 20.0}); s2 = pin({"v": 20.5})
run1, _ = run_receipt(c1, s1, "reading")
run2, _ = run_receipt(c2, s2, "reading")
log(f"P2 stress: run1={run1[:8]} run2={run2[:8]} both children of claim={c1[:8]}")
r_all = git("cat-file", "--batch-all-objects", "--batch-check",
            stdin=None).decode().splitlines()
parents = {}
for line in r_all:
    h, *_ = line.split()
    try:
        c = cell(h)
    except Exception:
        continue
    for ref in c.get("refs", []) + ([c["of"]] if "of" in c else []) + ([c["made"]] if "made" in c else []):
        parents.setdefault(ref, set()).add(h)
shared = len(parents.get(c1, set()))
log(f"P2 stress: claim has {shared} children — fork is representable, "
    f"but staleness check 'claim with no descendants' now FALSELY PASSES for one branch")

# ---------- P3: resolution limit ----------
log("P3 addressing cost vs cell worth (40-hex path per hop):")
chain = [("task", task), ("observation", obs_a), ("reading", r1)]
pathlen = 0
for i, (name, h) in enumerate(chain):
    pathlen = 40 * (i + 1)
    sz = len(json.dumps(cell(h)))
    log(f"  depth {i+1} ({name}): full path={pathlen}B, cell={sz}B, "
        f"path {'COSTS MORE' if pathlen > sz else 'ok'}")
# practical: nexus walk doesn't carry full paths — index does the hops
log("  but expansion via reverse-index costs one hash PER HOP, not 40B*depth carried")
log("  crossover: if cells must be self-addressing by full path, depth 2 already loses")
deep = task
for i in range(6):
    deep = pin({"kind": f"wrap{i}", "refs": [deep]})
log(f"  wrapped 6 more levels ({len(git('cat-file','--batch-all-objects','--batch-check').decode().splitlines())} objects total) — store handles it; the COST moved entirely into the index/walker")

# ---------- P4: nexus spin ----------
# reverse index over the whole object db
def build_index():
    idx = {}
    for line in git("cat-file", "--batch-all-objects", "--batch-check").decode().splitlines():
        h, *_ = line.split()
        try:
            c = cell(h)
        except Exception:
            continue
        refs = c.get("refs", [])
        for key in ("of", "made"):
            if key in c:
                refs = refs + [c[key]]
        for ref in refs:
            idx.setdefault(ref, set()).add(h)
    return idx

parents = build_index()
log(f"P4 nexus spin on {r1[:12]} — direct parents (one pass):")
for h in sorted(parents.get(r1, set())):
    log(f"  direct: {h[:12]} kind={cell(h).get('kind')}")
# transitive closure: spin until no new parents
seen, frontier, levels = set(), [r1], {}
while frontier:
    nxt = []
    for f in frontier:
        for p in parents.get(f, set()):
            if p not in seen:
                seen.add(p); nxt.append(p)
    frontier = nxt
log(f"P4 transitive closure: {len(seen)} ancestors, kinds:",
    sorted({cell(h).get('kind') for h in seen}))
bykind = {}
for h in seen:
    bykind.setdefault(cell(h).get('kind'), []).append(h)
for k, hs in sorted(bykind.items()):
    log(f"  level-kind {k}: {len(hs)} cell(s), e.g. {[x[:8] for x in hs[:3]]}")

pathlib.Path(ROOT / "probe-output.txt").write_text("\n".join(out) + "\n")
log("output -> probe-output.txt")
