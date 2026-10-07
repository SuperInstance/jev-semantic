#!/usr/bin/env python3
"""window.py — semantic projector v0. The PLATO->NES rasterizer.
Compile the 'window' an agent needs: task + nexus precedents + activity.
Usage: window.py <task-file> <repo-path>"""
import sys, os, subprocess, hashlib

def sh(cmd, cwd):
    r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    return r.stdout.strip()

def main():
    target, repo = sys.argv[1], sys.argv[2]
    print("=" * 60); print("WINDOW — %s" % target); print("=" * 60)
    print("\n## 1. THE TASK (the zone)")
    with open(target) as f: print(f.read()[:2500])
    print("\n## 2. NEXUS (where else this tile is visible)")
    h = hashlib.sha1(open(target,'rb').read()).hexdigest()
    print("blob: " + h)
    nx = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nexus.py")
    if os.path.isfile(nx):
        print(sh("python3 %s query %s 2>&1 | head -15" % (nx, h), repo)[:1500])
    print("\n## 3. RECENT ACTIVITY"); print(sh("git log --oneline -6", repo))
    print("\n" + "=" * 60 + "\nWINDOW COMPILED.\n" + "=" * 60)

if __name__ == "__main__": main()
