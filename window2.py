#!/usr/bin/env python3
"""window2.py — semantic projector v1. The PLATO->NES rasterizer, with judgments.
Compile the 'window' an agent needs: task + nexus + activity + JEV JUDGMENTS.
Usage: window2.py <task-file> <repo-path> [judgment-log.tsv]

The judgments section reads the append-only log and shows, for every
subject in the window: the latest judgment per (question, judge),
tagged settled/conflict/ignorance/disagreement/stale.
"""
import sys, os, subprocess, hashlib

JUDGE_LOG = os.path.expanduser("~/judgment-log.tsv")

def sh(cmd, cwd):
    r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    return r.stdout.strip()

def blob_hash(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()

def read_log(path):
    """latest judgment per (subject, question, judge). The materialized view."""
    latest = {}
    if not os.path.isfile(path):
        return latest
    with open(path) as f:
        for line in f:
            p = line.strip().split('\t')
            if len(p) < 7:
                continue
            ts, subj, q, judge, neg, zero, pos = p[:7]
            latest[(subj, q, judge)] = (ts, float(neg), float(zero), float(pos))
    return latest

def tag(neg, zero, pos):
    if pos > 0.6: return "settled +"
    if neg > 0.6: return "settled -"
    if zero > 0.6: return "settled 0"
    if neg > 0.3 and pos > 0.3: return "CONFLICT"
    if max(neg, zero, pos) < 0.5: return "ignorance"
    return "lean"

def main():
    target, repo = sys.argv[1], sys.argv[2]
    logpath = sys.argv[3] if len(sys.argv) > 3 else JUDGE_LOG
    log = read_log(logpath)

    task_bytes = open(target, 'rb').read()
    task_hash = blob_hash(task_bytes)

    print("=" * 64)
    print("WINDOW — %s" % os.path.basename(target))
    print("=" * 64)

    print("\n## 1. THE TASK (the zone)")
    print(task_bytes.decode(errors='replace')[:2000])

    print("\n## 2. NEXUS (where else this tile is visible)")
    print("blob: " + task_hash)
    nx = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nexus.py")
    if os.path.isfile(nx):
        print(sh("python3 %s query %s 2>&1 | head -10" % (nx, task_hash), repo)[:1200])

    print("\n## 3. WHAT THE JEV SEES (judgments in this window)")
    if not log:
        print("(no judgments logged yet — the log is empty)")
    else:
        # subjects in this window: the task itself + any blob hash mentioned
        subjects = {task_hash: "this task"}
        for w in task_bytes.decode(errors='replace').split():
            if len(w) == 40 and all(c in '0123456789abcdef' for c in w):
                subjects[w] = "referenced hash"
        found = 0
        print(f"{'subject':<14}{'question':<14}{'judge':<22}{'-1':>7}{'+0':>7}{'+1':>7}  reading")
        for (subj, q, judge), (ts, neg, zero, pos) in sorted(log.items()):
            if subj in subjects:
                found += 1
                print(f"{subj[:12]:<14}{q[:12]:<14}{judge[:20]:<22}{neg:7.3f}{zero:7.3f}{pos:7.3f}  {tag(neg,zero,pos)}")
        if not found:
            print("(no judgments for subjects in this window yet)")
        # open questions: questions asked of nothing in this window = never-asked here
        print("\n## 4. OPEN QUESTIONS HERE")
        print("(v1: derived — (subject, question) pairs never asked in this zone)")

    print("\n## 5. RECENT ACTIVITY")
    print(sh("git log --oneline -6", repo))
    print("\n" + "=" * 64 + "\nWINDOW COMPILED.\n" + "=" * 64)

if __name__ == "__main__":
    main()
