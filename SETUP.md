# Node Setup Guide — from blank WSL to judging node

*Recorded 2026-10-07 on a blank Ubuntu WSL (HP, Ryzen 5, 8GB). Every step as it happened.*

## Access (one-time, by the human)

1. In the blank WSL:
   ```
   sudo apt update && sudo apt install -y openssh-server && sudo service ssh start
   ssh-keygen -t ed25519 -f ~/.ssh/hp-node -N "" -C "hp-node"
   cat ~/.ssh/hp-node.pub
   ```
2. Send the public key to the foreman. Foreman installs it on the relay.
3. Run the reverse tunnel:
   ```
   ssh -R 2224:localhost:22 -i ~/.ssh/hp-node -o ServerAliveInterval=60 -N -f ubuntu@<relay>
   ```
4. Foreman generates its own key, human adds to HP's authorized_keys:
   ```
   echo '<foreman-pubkey>' >> ~/.ssh/authorized_keys
   ```

## Build (automated, by the foreman)

5. Inventory: `git` yes, `python3` yes, `pip` NO, `sudo` needs terminal.
6. Install pip without sudo:
   ```
   curl -sSL https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
   python3 /tmp/get-pip.py --user --break-system-packages --quiet
   ```
7. Install runtime deps:
   ```
   python3 -m pip install --user --break-system-packages --quiet onnxruntime tokenizers
   ```
8. Clone the repos:
   ```
   git clone https://github.com/SuperInstance/jev-semantic.git
   git clone --depth 1 https://github.com/SuperInstance/agent-inbox.git
   ```
9. Assemble the node:
   ```
   mkdir -p ~/node
   cp agent-inbox/payloads/intuition-bench/intuition_student.onnx* ~/node/
   cp agent-inbox/payloads/intuition-bench/tokenizer.json ~/node/
   cp jev-semantic/judge_log.py ~/node/
   # point judge_log.py MODEL_DIR at ~/node
   ```
10. First judgment:
    ```
    cd ~/node && python3 judge_log.py "test text" "question"
    ```

## Result

Blank WSL → judging node. First judgment logged on the HP at 2026-10-07.
The node judges at local speed, appends to its own log, and can verify
any other body's work by recomputation.

## What broke (honest)

- `pip` not installed; `ensurepip` missing. Used get-pip.py.
- PEP 668 (externally-managed-environment) blocks user installs without
  `--break-system-packages`.
- `sudo` requires a terminal — all installs must be `--user`.
- WSL sees 3.5GB of the 8GB. Still enough.
