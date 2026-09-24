"""Offline predicates for check.sh. Exit status is internal, never the lab grade."""
import ast
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
IDS = {"SQLI", "SECRET", "DEBUG", "XSS", "REDOS", "TRACE", "INPUT", "ENUM", "AUTH"}
READ_TOOLS = {"list_tables", "describe_table", "read_query"}
WRITE_TOOLS = {"write_query", "create_table", "append_insight"}


def run(args, **kwargs):
    result = subprocess.run(args, text=True, capture_output=True, timeout=40, **kwargs)
    if result.returncode:
        raise ValueError((result.stdout + result.stderr)[-3000:])
    return result.stdout


def python(script, *args, cwd=ROOT):
    return run(["uv", "run", "--offline", "--frozen", "--no-sync", "--project", str(ROOT),
                "python", str(ROOT / "grader/offline.py"), str(script), *map(str, args)], cwd=cwd)


def student_json():
    data = json.loads(Path("student.json").read_text())
    assert isinstance(data, dict)
    assert all(isinstance(data.get(k), str) and data[k].strip() for k in ("name", "student_id"))


def skill():
    text = Path(".agents/skills/security-scan/SKILL.md").read_text().replace("\r\n", "\n").replace("\r", "\n")
    assert text.startswith("---\n"), "Start with YAML frontmatter"
    parts = re.split(r"(?m)^---[ \t]*$", text, maxsplit=2)
    assert len(parts) == 3, "Close the YAML frontmatter with ---"
    front = parts[1]
    # The lab uses scalar name and description; also accept YAML block descriptions.
    assert not re.search(r"(?m)^\s*allowed-tools\s*:", front), "Remove Claude-only allowed-tools"
    name = re.search(r"(?m)^name:\s*(.+)$", front)
    assert name and name[1].strip().strip("\"'") == "security-scan", "name must match folder"
    desc = re.search(r"(?m)^description:\s*(.*(?:\n[ \t]+.*)*)", front)
    assert desc and "Use when" in desc[1], "description must contain Use when"
    missing = sorted(report_id for report_id in IDS if report_id not in parts[2])
    assert not missing, f"SKILL.md body must list the report IDs; missing: {', '.join(missing)}"


def scan_output(text):
    lines = text.strip().splitlines()
    assert lines and re.fullmatch(r"TOTAL: \d+", lines[-1]), "End with TOTAL: N"
    entries = []
    for line in lines[:-1]:
        # The directory prefix is not graded: a scanner that echoes the path it
        # was given (fixture_app/main.py) is as correct as one that prints app/.
        # Identity is the issue ID plus the line number.
        match = re.fullmatch(r"([A-Z]+) \S*main\.py:(\d+) .+", line)
        assert match, "Use ISSUE_ID <path>/main.py:LINE explanation"
        entries.append((match[1], int(match[2])))
    assert int(lines[-1].split(":")[1]) == len(entries), "Count must equal finding lines"
    assert len(entries) == len(set(entries)), "Do not duplicate findings"
    return entries


def scanner_ids():
    fixture = ROOT / "grader/pristine/main.py"
    source = fixture.read_text()
    tree = ast.parse(source)
    spans = {}
    mapping = {"login": "SQLI", "debug": "DEBUG", "hello": "XSS", "search": "REDOS", "errors": "TRACE", "delete_card": "AUTH"}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in mapping:
            start = min([node.lineno] + [d.lineno for d in node.decorator_list])
            spans[mapping[node.name]] = range(start, node.end_lineno + 1)
        if isinstance(node, ast.ClassDef) and node.name == "Card":
            for field in node.body:
                if isinstance(field, ast.AnnAssign) and isinstance(field.target, ast.Name):
                    if field.target.id in ("title", "status"):
                        spans[{"title": "INPUT", "status": "ENUM"}[field.target.id]] = range(field.lineno, field.end_lineno + 1)
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "API_SECRET" for t in node.targets):
            spans["SECRET"] = range(node.lineno, node.end_lineno + 1)
    with tempfile.TemporaryDirectory(prefix="w11-scanner-") as scratch:
        target = Path(scratch) / "fixture_app"
        target.mkdir()
        (target / "main.py").write_text(source)
        entries = scan_output(python(ROOT / "scripts/scan.py", target, cwd=scratch))
        unexpected = sorted((issue, line) for issue, line in entries if issue not in IDS or line not in spans[issue])
        missing = sorted(set(spans) - {issue for issue, _ in entries})
        assert not unexpected and not missing, \
            f"Reported findings not in ground truth: {unexpected}; expected IDs missing: {missing}"
        # A scanner that always prints the same list cannot earn points.
        (target / "main.py").write_text('"""Empty negative control: no vulnerable code."""\n')
        assert not scan_output(python(ROOT / "scripts/scan.py", target, cwd=scratch)), "Scanner reports issues in empty control"
    return {issue for issue, _ in entries}


def scanner():
    ids = scanner_ids()
    print("Detected:", ", ".join(sorted(ids)))
    assert len(ids) >= 5 and "SQLI" in ids, "Need >=5 planted issues including SQLI"


def sqli():
    assert Path("tests/test_sqli.py").is_file(), "Write tests/test_sqli.py first"
    print(python(ROOT / "grader/exploit.py"))
    print(python(ROOT / "grader/pytest_runner.py", "tests/test_sqli.py"))


def count(path):
    text = Path(path).read_text()
    matches = re.findall(r"(?m)^TOTAL: (\d+)\s*$", text)
    assert len(matches) == 1, "Exactly one TOTAL: N required"
    return int(matches[0])


def scan_drop():
    assert count("reports/scan_before.txt") > count("reports/scan_after.txt"), "Record red scan before fixing SQLi, then re-scan"


def config():
    return tomllib.loads(Path(".codex/config.toml").read_text())["mcp_servers"]


def mcp():
    server = config()["sqlite"]
    assert server.get("enabled", True) is True, "Enable the sqlite server"
    assert server.get("command") == "uvx"
    args = server.get("args", [])
    assert args[:3] == ["--with", "mcp<2", "mcp-server-sqlite"] and \
        args[3:] == ["--db-path", "data/app.db"], \
        'args must be ["--with", "mcp<2", "mcp-server-sqlite", "--db-path", "data/app.db"]' \
        ' - the --with "mcp<2" guard is required: uvx re-resolves dependencies and mcp 2.x crashes this server'
    assert server.get("cwd") == "."
    enabled = server.get("enabled_tools")
    assert isinstance(enabled, list) and enabled and set(enabled) <= READ_TOOLS
    assert "read_query" in enabled
    assert not set(enabled) & WRITE_TOOLS
    assert "read_query" not in server.get("disabled_tools", []), "Do not disable read_query"
    assert WRITE_TOOLS <= set(server.get("disabled_tools", [])), "Deny each write tool by name"
    assert server.get("default_tools_approval_mode") == "prompt"
    evidence = Path("reports/mcp.md").read_text()
    assert "read_query" in evidence, "Quote one read_query call and result"
    blocks = re.findall(r"```json\s*\n(.*?)```", evidence, re.S)
    try:
        results = [json.loads(block) for block in blocks]
    except json.JSONDecodeError as error:
        raise AssertionError(
            "A ```json block in reports/mcp.md is not valid JSON - check for single quotes or stray prose inside the fence"
        ) from error
    def successful(result):
        return isinstance(result, (dict, list)) and bool(result) and not (
            isinstance(result, dict) and (result.get("isError") or "error" in result))
    assert any(successful(result) for result in results), "Paste a successful non-empty result in a fenced json block"


def er():
    server = config()["mermaid"]
    assert server.get("enabled", True) is True, "Enable the mermaid server"
    # mermaid-mcp-app is published on npm, not PyPI, so it launches with npx.
    assert server.get("command") == "npx", "mermaid-mcp-app is an npm package: command = \"npx\""
    args = [a for a in server.get("args", []) if a != "-y"]
    assert args == ["mermaid-mcp-app@0.4.4"], \
        "pin the reviewed version - an unpinned npx package can change under you"
    diagram = "\n".join(line for line in Path("docs/er.mmd").read_text().splitlines() if not line.lstrip().startswith("%%")).lstrip()
    assert diagram.startswith("erDiagram"), "Start docs/er.mmd with erDiagram"
    with sqlite3.connect("file:data/app.db?mode=ro", uri=True) as db:
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
    assert {"users", "boards", "cards", "votes"} <= tables, "Run init.sh for the full fixture"
    assert all(re.search(r"\b" + re.escape(table) + r"\b", diagram, re.I) for table in tables), "Name every database table"
    evidence = Path("reports/mcp.md").read_text().lower()
    for token in ("mermaid", "render", "docs/er.png"):
        assert token in evidence, f"reports/mcp.md is missing required Mermaid evidence token: {token}"


def red_first():
    # Inspect content history, not commit subjects. No checkout or executing old commits.
    commits = run(["git", "rev-list", "--reverse", "HEAD"]).splitlines()
    red = False
    for commit in commits:
        def show(path):
            result = subprocess.run(["git", "show", f"{commit}:{path}"], capture_output=True, text=True)
            return result.stdout if result.returncode == 0 else ""
        source, test = show("app/main.py"), show("tests/test_sqli.py")
        if not source or not test:
            continue
        vulnerable = 'query = f"SELECT' in source
        if vulnerable and "401" in test and "or" in test.lower():
            red = True
        elif red and not vulnerable and "401" in test:
            return
    raise ValueError("Commit the SQLi exploit test while login is vulnerable, then commit the parameterized fix")


def second_fix():
    assert Path("tests/test_second_fix.py").is_file(), "Bonus: test and fix a second vulnerability"
    print(python(ROOT / "grader/second_fix.py"))
    print(python(ROOT / "grader/pytest_runner.py", "tests/test_second_fix.py"))


def scanner_all():
    assert scanner_ids() == IDS, "Detect all nine planted issues"


def scan_flow():
    diagram = Path("docs/scan_flow.mmd").read_text().lower()
    assert diagram.lstrip().startswith("flowchart")
    assert all(word in diagram for word in ("scan", "audit", "fix", "re-scan"))
    assert Path("docs/scan_flow.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    evidence = Path("reports/mcp.md").read_text().lower()
    assert "mermaid" in evidence and "render" in evidence and "docs/scan_flow.png" in evidence


if __name__ == "__main__":
    try:
        globals()[sys.argv[1]]()
    except Exception as error:
        print(f"{type(error).__name__}: {error}")
        sys.exit(1)
