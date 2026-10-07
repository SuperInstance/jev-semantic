#!/bin/bash
# seed.sh — drop a new agent on a fresh instance.
# Usage: curl -sSL <url>/seed.sh | bash
# Or: git clone <repo> && ./seed.sh
set -e
echo "=== Agent Seed ==="
echo "[1/5] Installing pip..."
curl -sSL https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
python3 /tmp/get-pip.py --user --break-system-packages --quiet 2>&1 | tail -1
echo "[2/5] Installing runtime..."
python3 -m pip install --user --break-system-packages --quiet onnxruntime tokenizers 2>&1 | tail -1
echo "[3/5] Cloning repos..."
cd ~
git clone --quiet https://github.com/SuperInstance/jev-semantic.git 2>&1 | head -1
git clone --quiet --depth 1 https://github.com/SuperInstance/agent-inbox.git 2>&1 | head -1
echo "[4/5] Assembling node..."
mkdir -p ~/node
cp agent-inbox/payloads/intuition-bench/intuition_student.onnx* ~/node/ 2>/dev/null || echo "  (model not in inbox yet)"
cp agent-inbox/payloads/intuition-bench/tokenizer.json ~/node/ 2>/dev/null || true
cp jev-semantic/judge_log.py ~/node/ 2>/dev/null || true
echo "[5/5] First judgment..."
cd ~/node && python3 judge_log.py "New node online via seed." "is-this-a-good-node" 2>&1 | head -1 || echo "  (judge not ready)"
echo "=== Seed complete ==="
