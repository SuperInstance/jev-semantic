# INPUT-CONTRACT.md — intuition-student-v1 input/output contract

Written from the code, 2026-10-22. Two sources define what the judge
actually accepts: the serving path (`judge_log.py`, this repo) and the
training path (`SuperInstance/intuition`, `src/train_student.py` at
`eeb1154` — the commit whose model files are byte-identical to the
published artifact). They do **not** agree; §"Train/serve skew"
describes the divergence exactly as the code shows it. Companion
docs: `BENCHMARK.md` (cost), `DETERMINISM.md` (precision contract),
`judges/intuition-student-v1.md` (artifact hashes).

## 1. Serving: what `judge_log.py` does

Call: `judge_log.py <text-or-file> [question]` — `text` is a literal
string, or a path (the file's contents are read); `question` is any
string, defaulting to `"root"`.

The input profile is assembled as one string (`judge_log.py:30`):

```
"[STATE] " + text[:500] + " [QUESTION] " + question
```

- the subject text is truncated to its first **500 characters** before
  assembly; the question is not truncated;
- `questions/root.md` is **never read**. The default question string
  `"root"` coincides with that file's name; nothing in the code
  tokenizes the file's text ("Is this good?").

Then (`judge_log.py:31-33`):

```
enc.ids[:64] + [0] * max(0, 64 - len(enc.ids))
→ int64 tensor [1,64] named "ids" → sess.run → logits fp32 [1,3]
```

- truncate to the first **64 token ids** (the 500-char cap above can
  still produce more than 64 ids — then this window silently drops the
  tail, including possibly the `[QUESTION] …` section on long text);
- right-pad with `[PAD]=0` to exactly 64;
- batch dimension is always 1 at serving.

Padding is masked, not averaged: the graph's pooling is PAD-aware
(`Equal`/`Where`/`ReduceSum` mean pool), matching the torch source's
`src_key_padding_mask` on `padding_idx=0`.

## 2. Tokenizer (published `tokenizer.json`, vocab exactly 8000)

- BPE (`models.BPE`), `unk_token="[UNK]"`, trained with vocab size
  8000, special tokens `[PAD]=0`, `[UNK]=1`, `[STATE]=2`,
  `[QUESTION]=3`;
- ByteLevel pre-tokenizer; **no** normalizer, **no** post-processor,
  **no** decoder — so `encode(s)` and `encode(s,
  add_special_tokens=False)` produce identical output (the training
  path uses the latter, serving the former);
- case-sensitive; text is never lowercased or normalized before BPE.

## 3. Model I/O signature (published ONNX graph, opset 17)

- input: `ids` — int64, shape `[batch, 64]` (serving always batch 1);
- output: `logits` — float32, shape `[1, 3]`, **pre-softmax scores** in
  fixed class order **(neg, zero, pos)** = classes (−1, 0, +1);
- softmax is computed by the caller (`judge_log.py:35`), then the
  three probabilities are logged to **four decimals** — the judge's
  output convention (manifest; enforced in spirit by the log-line
  regex in `tests/test_log_format.py`):
  `ts \t subject-blob-sha1 \t question-blob-sha1 \t judge \t neg \t zero \t pos`
  (note: the judge column is the literal string
  `intuition-student-v1`, not a manifest hash — known limitation,
  `play-notes-minimax.md` #4).

## 4. Training: what the model was actually trained on

Verbatim from `intuition/src/train_student.py@eeb1154` — every
training example was assembled as:

```python
STATE_PREFIX = {
    "load-bearing": "Design task: a discriminator agent judges a builder agent's work across rounds. Candidate question: ",
    "coherence": "Reviewing a candidate statement for logical soundness. Statement: ",
    "go-no-go": "Triaging a proposed action for a team. Proposed action: ",
}
QUESTION = {
    "load-bearing": "How load-bearing is this question for the design task?",
    "coherence": "Does this statement cohere logically?",
    "go-no-go": "Should this action proceed?",
}
r["input"] = "[STATE] " + STATE_PREFIX[r["family"]] + r["text"] + " [QUESTION] " + QUESTION[r["family"]]
```

i.e. `[STATE] <family prefix> <text> [QUESTION] <family question>`,
over a 3100-example teacher-graded corpus (`data/graded.jsonl`, three
families), tokenized with the same tokenizer, same `[:64]`
truncation, same right-padding to 64. There was **no** 500-char cap at
training time.

## 5. Train/serve skew (documented, not fixed)

The production input path and the training input path differ in three
ways, plus a benchmark gap:

1. **Serving drops the family prefixes.** Training placed one of three
   long STATE prefixes between `[STATE] ` and the text; `judge_log.py`
   inserts nothing. Whether this was intentional is not recorded
   anywhere in the three repos.
2. **The question vocabulary is uncontrolled at serve time.**
   Training used exactly the three fixed family questions above —
   those are the only question strings the model was trained to
   answer. Serving passes an arbitrary string, and its default
   `"root"` is a string the model never saw in training (see §1 on
   `questions/root.md`).
3. **Serving adds a 500-char pre-truncation** of the text before
   tokenization; training had none. In effect mostly moot (the
   `[:64]` id window dominates), but it is a preprocessing difference.
4. **The published benchmark measures neither format.** `bench.py`
   (see BENCHMARK.md) tokenizes bare prompts with no
   `[STATE]`/`[QUESTION]` wrapper — so the recorded latencies, while
   mechanically representative (same window/padding/shape), are not
   measurements of the production input path.

A reimplementer following only this repo would otherwise guess the
model expects bare `[STATE] <text> [QUESTION] <arbitrary question>`;
the trainer is the only record of the family prefixes and the three
trained question strings. This section is that record.

Terminology note: companion docs (beam-quilt) call the judge's input a
"short typed profile"; the concrete format in this repo is the
`(text, question)` pair wrapped as in §1.

## 6. Minimal reproduction of the serving pipeline

```python
import numpy as np, onnxruntime as ort
from tokenizers import Tokenizer
D = "<dir with the three artifact files>"
tok = Tokenizer.from_file(f"{D}/tokenizer.json")
sess = ort.InferenceSession(f"{D}/intuition_student.onnx",
                            providers=["CPUExecutionProvider"])
def judge(text: str, question: str = "root") -> tuple[float, float, float]:
    enc = tok.encode("[STATE] " + text[:500] + " [QUESTION] " + question)
    ids = enc.ids[:64] + [0] * max(0, 64 - len(enc.ids))
    logits = sess.run(None, {"ids": np.array([ids], dtype=np.int64)})[0][0]
    e = np.exp(logits - logits.max()); p = e / e.sum()
    return tuple(round(float(x), 4) for x in p)   # (neg, zero, pos)
```
