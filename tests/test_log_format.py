#!/usr/bin/env python3
"""Test: the judgment log format parses and the triple-hash key is well-formed."""
import re, sys

LINE_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\t"  # timestamp
    r"([0-9a-f]{40})\t"                          # subject (blob hash)
    r"([0-9a-f]{40})\t"                          # question (blob hash)
    r"(\S+)\t"                                   # judge
    r"(\d+\.\d{4})\t(\d+\.\d{4})\t(\d+\.\d{4})$"  # neg zero pos
)

def test_line():
    sample = "2026-10-07T14:47:01\t8c0ae2091089237ad9f8dbbe753c7cb8b6e774cf\tfab72e5b8f56300935fb47e1cb6ceb4261b81d1a\tintuition-student-v1\t0.0187\t0.0822\t0.8991"
    m = LINE_RE.match(sample)
    assert m, "log line does not parse"
    neg, zero, pos = float(m.group(5)), float(m.group(6)), float(m.group(7))
    assert abs((neg + zero + pos) - 1.0) < 0.001, "probs do not sum to 1"
    print("PASS: log format parses, triple-hash key well-formed, probs sum to 1")

if __name__ == "__main__":
    test_line()
