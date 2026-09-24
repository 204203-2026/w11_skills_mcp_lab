"""CI gate: missing, malformed, reordered, or incomplete required results fail."""
import json
from pathlib import Path

expected = ["student_json", "skill", "scanner", "sqli", "scan_drop", "mcp", "er"]
data = json.loads(Path("results/report.json").read_text())
assert data["total"] == 7 and data["score"] == 7, "Not all seven required checks pass"
assert data["results"] == [{"name": name, "status": "pass"} for name in expected], "Missing or failed required checks"
print("PASS: all seven required checks")
