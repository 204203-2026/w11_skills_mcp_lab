#!/usr/bin/env bash
# Week 11: dependency setup may use the network; check.sh never does.
ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
cd "$ROOT" || exit 1
missing=0
for tool in git python3 uv; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "MISSING $tool — install it using TASKS.md prerequisites"
    missing=$((missing + 1))
  fi
done
[ "$missing" -eq 0 ] || exit 1
mkdir -p data reports docs results
python3 scripts/seed.py || exit 1
uv sync --frozen || exit 1
if ! command -v codex >/dev/null 2>&1; then
  echo "INFO Codex is needed for the lab, not for offline grading. See TASKS.md."
fi
if ! command -v node >/dev/null 2>&1; then
  echo "INFO MISSING node — Step 8 needs Node 20+. See TASKS.md prerequisites; offline grading does not need it."
elif ! node_major=$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null) || [ "$node_major" -lt 20 ]; then
  echo "INFO node $(node --version) is too old — Step 8 needs Node 20+. See TASKS.md prerequisites; offline grading does not need it."
fi
if ! command -v npx >/dev/null 2>&1; then
  echo "INFO MISSING npx — Step 8 needs it. See TASKS.md prerequisites; offline grading does not need it."
fi
echo "OK workspace ready. Open TASKS.md and begin Step 0."
