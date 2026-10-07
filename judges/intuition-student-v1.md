# intuition-student-v1

- architecture: micro transformer encoder, d256, 6 layers, 8 heads
- params: 6.80M
- output: 3-way softmax over (-1, 0, +1)
- training: KL vs teacher soft probs, 3x weight on H > 1.0
- latency: 7.0ms (4-thread ARM), 6.2ms (1-thread x86)
- determinism: bit-identical logits across x86_64 and aarch64
- encoder: BPE 8k tokenizer (tokenizer.json)
- output convention: fixed order (neg, zero, pos), four decimals
