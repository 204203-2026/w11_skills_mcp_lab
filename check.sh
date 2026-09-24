#!/usr/bin/env bash
# Week 11 self-check. No set -e; pass/fail belongs in JSON, always exit 0.
ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
cd "$ROOT" || exit 0
export UV_OFFLINE=1 UV_PYTHON_DOWNLOADS=never
mkdir -p results
PASS=0
FAIL=0
TOTAL=0
BONUS=0
BONUS_DONE=0
REQ_ITEMS=""
BONUS_ITEMS=""
record() {
  TOTAL=$((TOTAL + 1))
  if [ "$2" = "PASS" ]; then
    PASS=$((PASS + 1))
    status=pass
  else
    FAIL=$((FAIL + 1))
    status=fail
  fi
  REQ_ITEMS="${REQ_ITEMS}{\"name\":\"$1\",\"status\":\"$status\"},"
  echo "$2 $1 - $3"
}
record_bonus() {
  BONUS=$((BONUS + 1))
  if [ "$2" = "DONE" ]; then
    BONUS_DONE=$((BONUS_DONE + 1))
    status=bonus
  else
    status=todo
  fi
  BONUS_ITEMS="${BONUS_ITEMS}{\"name\":\"$1\",\"status\":\"$status\"},"
  echo "$2 $1 (optional) - $3"
}
check_required() {
  if uv run --offline --frozen --no-sync python grader/check.py "$1"; then
    record "$1" PASS "$2"
  else
    record "$1" FAIL "$2"
  fi
}
check_bonus() {
  if uv run --offline --frozen --no-sync python grader/check.py "$1"; then
    record_bonus "$1" DONE "$2"
  else
    record_bonus "$1" TODO "$2"
  fi
}
echo "-- w11_skills_mcp_lab: Required --"
# Required numbering is the course contract: keep 1–7 in this order.
check_required student_json "1. student.json: non-empty name and student_id"
check_required skill "2. project security-scan skill frontmatter"
check_required scanner "3. >=5 detections on grader fixture, including SQLI"
check_required sqli "4. instructor exploit and tests/test_sqli.py pass"
check_required scan_drop "5. scan_before count > scan_after count"
check_required mcp "6. read-only sqlite MCP config and read_query evidence"
check_required er "7. mermaid config, all DB tables in ER, render evidence"
echo "-- Bonus --"
check_bonus red_first "1. SQLi test commit before fix commit"
check_bonus second_fix "2. another vulnerability fixed with its own test"
check_bonus scanner_all "3. scanner detects all nine issues"
check_bonus scan_flow "4. scan pipeline flowchart rendered via mermaid MCP"
# Keep prior reports before overwriting. No timestamps enter the grade JSON.
for report in results/report.json results/challenge_report.json; do
  if [ -e "$report" ]; then
    backup=$(mktemp -d results/.backup.XXXXXX)
    cp -p "$report" "$backup/$(basename "$report")"
  fi
done
printf '{"score":%s,"total":%s,"results":[%s]}\n' "$PASS" "$TOTAL" "${REQ_ITEMS%,}" > results/report.json
printf '{"bonus":%s,"bonus_total":%s,"results":[%s]}\n' "$BONUS_DONE" "$BONUS" "${BONUS_ITEMS%,}" > results/challenge_report.json
echo "Score: $PASS / $TOTAL required | $FAIL failed | Bonus: $BONUS_DONE / $BONUS"
echo "Reports: results/report.json + results/challenge_report.json"
exit 0
