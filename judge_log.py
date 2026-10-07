#!/usr/bin/env python3
"""judge_log.py — the judgment log, v0. Start of the semantic layer.
Every judgment: (subject, question, judge) -> (neg, zero, pos).
Append-only. The log is the seed; the graph grows from it.

Usage: judge_log.py <text-or-file> [question]
"""
import sys, os, hashlib, json, time
import onnxruntime as ort
from tokenizers import Tokenizer

MODEL_DIR = "/tmp/inbox-bench/payloads/intuition-bench"
LOG = os.path.expanduser("~/judgment-log.tsv")

def blob_hash(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()

def main():
    src = sys.argv[1]
    question = sys.argv[2] if len(sys.argv) > 2 else "root"
    if os.path.isfile(src):
        text = open(src).read()
    else:
        text = src

    # Load student (cached in process)
    tok = Tokenizer.from_file(os.path.join(MODEL_DIR, "tokenizer.json"))
    sess = ort.InferenceSession(os.path.join(MODEL_DIR, "intuition_student.onnx"),
                                providers=["CPUExecutionProvider"])
    enc = tok.encode("[STATE] " + text[:500] + " [QUESTION] " + question)
    ids = enc.ids[:64] + [0] * max(0, 64 - len(enc.ids))
    import numpy as np
    logits = sess.run(None, {"ids": np.array([ids], dtype=np.int64)})[0][0]
    # softmax
    e = np.exp(logits - logits.max()); probs = e / e.sum()
    neg, zero, pos = probs

    subject = blob_hash(text.encode())
    qhash = blob_hash(question.encode())
    judge = "intuition-student-v1"  # manifest hash goes here when we have judges/
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")

    line = f"{ts}\t{subject}\t{qhash}\t{judge}\t{neg:.4f}\t{zero:.4f}\t{pos:.4f}\n"
    with open(LOG, "a") as f:
        f.write(line)

    reading = "settled -" if neg > 0.6 else "settled +" if pos > 0.6 else "settled 0" if zero > 0.6 else "conflict" if neg > 0.3 and pos > 0.3 else "ignorance" if max(probs) < 0.5 else "lean"
    print(f"judged: {reading} (-1:{neg:.3f} 0:{zero:.3f} +1:{pos:.3f})")
    print(f"logged: {subject[:12]}...")

if __name__ == "__main__":
    main()
