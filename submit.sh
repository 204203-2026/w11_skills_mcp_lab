#!/usr/bin/env bash
# Student submission helper. Running this explicitly publishes to your configured remote.
ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
cd "$ROOT" || exit 1
bash check.sh
if ! uv run --offline --frozen --no-sync python grader/gate.py; then
  uv run --offline --frozen --no-sync python -c '
import json
report = json.load(open("results/report.json"))
failed = ", ".join(item["name"] for item in report["results"] if item["status"] != "pass") or "unknown"
print("WARNING: required gate failed — score {}/{}; failing checks: {}. Continuing submission so CI can grade partial work.".format(
    report["score"], report["total"], failed
))
'
fi
for path in student.json .agents .codex app scripts tests reports docs results/report.json results/challenge_report.json; do
  [ ! -e "$path" ] || git add "$path" || exit 1
done
if ! git diff --cached --quiet; then
  git commit -m "w11_skills_mcp_lab submission" || exit 1
fi
branch=$(git branch --show-current)
git push -u origin "$branch" || {
  echo "Push failed. Check your remote and fetch the CI report commit before retrying."
  exit 1
}
echo "Submitted. Check the Actions tab for recomputed results."
