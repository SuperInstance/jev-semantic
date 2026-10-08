#!/usr/bin/env python3
"""Judgment-log demo — spec v0.1 §7. Store = git object db (loose objects).

Demo flow:
  1. pin 3 content cells (fake commits, hand-grounded: msg matches diff?)
  2. pin encoder descriptor (bag-of-words, v0) + jev descriptor (heuristic v1)
  3. pin 1 question (ternary_float)
  4. write 5 judgments (incl. one multiplicity pair, one metajudgment)
  5. write 2 anchors
  6. trace() one percentage; calibration table
  7. CHIP PROBE: mutate a basis content cell -> stale visible in one
     top-level hash comparison (mc4 T5 applied to testimony)
  8. B3 probe: dangling judgment (content hash nobody has) stores fine
"""
import hashlib, json, subprocess, os, sys

REPO = os.path.dirname(os.path.abspath(__file__))
os.chdir(REPO)
subprocess.run(["git", "init", "-q", "store"], check=True)
os.chdir("store")

def canon(o):  # canonical JSON: sorted keys, no whitespace
    return json.dumps(o, sort_keys=True, separators=(",", ":"))

def pin(o):
    """Write object into git object store. Returns (hash, bytes)."""
    b = canon(o).encode()
    h = subprocess.run(["git", "hash-object", "-w", "--stdin"],
                       input=b, capture_output=True, check=True).stdout.decode().strip()
    return h, b

def have(h):
    r = subprocess.run(["git", "cat-file", "-e", h], capture_output=True)
    return r.returncode == 0

# NAME BINDINGS live above the substrate (a ref = name -> current hash).
# Content-addressed stores never lose an object, so "stale" can never
# mean "object absent" -- it means "judgment's c != the name's current
# binding." That's the finding the chip probe is built to surface.
import pathlib
REFDIR = pathlib.Path("refs")
REFDIR.mkdir(exist_ok=True)
def bind(name, h):
    (REFDIR / name).write_text(h)
def current(name):
    p = REFDIR / name
    return p.read_text().strip() if p.exists() else None

log = []

# ---------- 1. content cells (fake commits; ground truth by hand) ----------
contents = [
    {"type": "content", "kind": "commit",
     "msg": "add hello.txt greeting",
     "diff": "--- /dev/null\n+++ b/hello.txt\n@@ +0,0 +1 @@\n+hello",
     "truth": 1},   # message matches diff
    {"type": "content", "kind": "commit",
     "msg": "fix off-by-one in loop",
     "diff": "--- a/main.py\n+++ b/main.py\n@@ +10,0 +11 @@\n+# TODO: revisit",
     "truth": -1},  # message claims a fix; diff adds a comment. LIE.
    {"type": "content", "kind": "commit",
     "msg": "update readme with install steps",
     "diff": "--- a/README.md\n+++ b/README.md\n@@ +1,0 +2,3 @@\n+## Install\n+pip install .",
     "truth": 1},
]
cH = [pin(c)[0] for c in contents]

# aggregate cell: release notes summarizing c1 + c3 (the two honest ones)
relnotes = {"type": "content", "kind": "release-notes",
            "items": [cH[0], cH[2]], "note": "honest commits this cycle"}
relH, _ = pin(relnotes)
bind("release-notes", relH)   # the name -> hash binding, above substrate

# ---------- 2. encoder + jev descriptors ----------
enc = {"type": "encoder", "model": "bag-of-words", "version": "0.1",
       "params_hash": "bow-vocab-42-sha256:deadbeef",
       "render": "spec:bow-v0.1 (token multiset -> freq vector)"}
eH, _ = pin(enc)

jev = {"type": "jev", "model": "heuristic-v1", "version": "0.1",
       "params_hash": "heur1-ruleset-sha256:cafef00d",
       "render": "spec:heur1 (overlap(msg tokens, diff tokens) -> ternary)",
       "train_seq": []}
jH, _ = pin(jev)

# ---------- 3. question ----------
q = {"type": "question",
     "text": "does this commit message match its diff?",
     "answer_space": "ternary_float", "domain_hint": "vcs"}
qH, _ = pin(q)

# ---------- 4. five judgments ----------
import datetime
def J(c, v, conf, basis=None):
    return {"type": "judgment", "q": qH, "c": c, "e": eH, "j": jH,
            "v": v, "conf": conf, "basis": basis or [],
            "t": "2026-10-07T17:50:00+08:00"}

# hand-run heuristic v1 over the bag-of-words rendering (overlap of
# msg tokens vs diff tokens, thresholded). Written as the jev's output.
j1 = pin(J(cH[0], 1, 0.9))          # "hello/greeting" overlap -> match
j2 = pin(J(cH[1], -1, 0.8))         # no overlap -> mismatch
j3 = pin(J(cH[2], 1, 0.7))          # "readme/install" overlap -> match
# metajudgment: judging the release-notes cell, standing on j1+j3
j4 = pin(J(relH, 1, 0.85, basis=[j1[0], j3[0]]))
# multiplicity: re-judgment of c1 (append-only invariant 1) — BOTH kept
j5 = pin(J(cH[0], 1, 0.88))

# ---------- 5. two anchors (external checks — hand ground truth) ----------
def A(jh, outcome):
    return {"type": "anchor", "judgment": jh, "outcome": outcome,
            "source": "hand ground-truth (contents[].truth)",
            "t": "2026-10-07T18:00:00+08:00"}
a1 = pin(A(j1[0], 1))    # c1 truth=1
a2 = pin(A(j2[0], -1))   # c2 truth=-1

# ---------- 6. trace + calibration ----------
def trace(jh, depth=4, seen=None):
    seen = seen or set()
    if depth == 0 or jh in seen:
        return {"judgment": jh[:12], "truncated": True}
    seen.add(jh)
    j = json.loads(subprocess.run(["git", "cat-file", "blob", jh],
                   capture_output=True, check=True).stdout)
    out = {"judgment": jh[:12], "q": j["q"][:8], "c": j["c"][:12],
           "e": j["e"][:8], "j": j["j"][:8], "v": j["v"], "conf": j["conf"],
           "subject_present": have(j["c"]),
           "stale": stale_of(j["c"]),
           "basis": [trace(b, depth-1, seen) for b in j["basis"]]}
    return out

def stale_of(c):
    """A judgment is stale iff its c was superseded: a name's binding
    moved off it (recorded in refs/.superseded). No tombstone -> not
    stale; c never in the store at all -> unverifiable (B3), not stale.
    Content-addressed stores never lose objects, so 'stale' is a
    property of the BINDING layer, not of object existence."""
    tomb = pathlib.Path("refs/.superseded")
    superseded = tomb.read_text().split() if tomb.exists() else []
    return c in superseded

def calibration():
    """error per (jev,question) over anchored judgments"""
    # anchors live in known list for the demo (nexus pass is mc1 work)
    rows = []
    for jh, outcome in [(j1[0], 1), (j2[0], -1)]:
        j = json.loads(subprocess.run(["git", "cat-file", "blob", jh],
                       capture_output=True, check=True).stdout)
        rows.append({"jev": j["j"][:8], "q": j["q"][:8],
                     "err": abs(j["v"] - outcome)})
    return rows

# ---------- 7. CHIP PROBE ----------
# mutate relnotes -> new object; binding MOVES; old object still in
# store (git never forgets). Staleness = binding moved, one compare.
relnotes["note"] = "honest commits this cycle (amended)"
relH2, _ = pin(relnotes)
with open("refs/.superseded", "a") as f:
    f.write(relH + "\n")
bind("release-notes", relH2)
chip = {"before": relH[:12], "after": relH2[:12],
        "old_object_still_in_store": have(relH),  # <-- the finding
        "binding_now_points_to": current("release-notes")[:12],
        "j4_stale_after_chip": stale_of(relH),
        "trace_j4_after_chip": trace(j4[0])}

# ---------- 8. B3 probe: dangling judgment, subject never existed ----------
ghost = hashlib.sha1(b"nobody has this content").hexdigest()  # not in store
j6 = pin(J(ghost, 0, 0.3))
b3 = {"stores_fine": True, "subject_exists": have(ghost),
      "verifiable": False,
      "note": "judgment outlives its subject; graph has no opinion"}

report = {
    "objects_pinned": {"contents": [h[:8] for h in cH], "relnotes": relH[:8],
                       "encoder": eH[:8], "jev": jH[:8], "question": qH[:8],
                       "judgments": [x[0][:8] for x in (j1, j2, j3, j4, j5, j6)],
                       "anchors": [a1[0][:8], a2[0][:8]]},
    "trace_j4": trace(j4[0]),
    "calibration": calibration(),
    "chip_probe": chip,
    "b3_dangling": b3,
}
os.chdir(REPO)
with open("demo-result.json", "w") as f:
    json.dump(report, f, indent=1, default=str)
print(json.dumps(report, indent=1, default=str))
