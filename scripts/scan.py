"""Offline source scanner. Add at least three real detectors; keep this CLI."""
import re
import sys
from pathlib import Path

# Each detector emits one issue ID, source location, and explanation.
# Add SQLI and at least two more from XSS REDOS TRACE INPUT ENUM AUTH.
DETECTORS = {
    "SECRET": (r'["\']sk-FAKE-0+["\']', "Hardcoded secret"),
    "DEBUG": (r'@app\.get\(["\']/debug["\']', "Debug route exposes environment"),
}


def scan(directory):
    findings = []
    for path in sorted(Path(directory).glob("*.py")):
        for number, line in enumerate(path.read_text().splitlines(), 1):
            for issue, (pattern, message) in DETECTORS.items():
                if re.search(pattern, line):
                    findings.append(f"{issue} {path}:{number} {message}")
    return findings


if __name__ == "__main__":
    if len(sys.argv) != 2 or not Path(sys.argv[1]).is_dir():
        raise SystemExit("Usage: uv run --offline --frozen python scripts/scan.py app")
    findings = scan(sys.argv[1])
    print("\n".join(findings + [f"TOTAL: {len(findings)}"]))
