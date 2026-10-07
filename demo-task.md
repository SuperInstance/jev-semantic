# 014: rotate the deploy key

Rotate the production deploy key before Friday. The old key has been
in use for 18 months. Steps: generate new key, add to GitHub, update
the server, verify, remove old key.

Risk: if the new key doesn't work, deploys break.
