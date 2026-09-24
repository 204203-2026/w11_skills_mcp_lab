"""Accept an independently observed second fix; student regression must also pass."""
import ast
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from app import main

root = Path(__file__).resolve().parents[1]
fixed = []
with tempfile.TemporaryDirectory(prefix="w11-second-") as scratch:
    target = Path(scratch) / "app.db"
    with sqlite3.connect(f"file:{root / 'data/app.db'}?mode=ro", uri=True) as source:
        with sqlite3.connect(target) as destination:
            source.backup(destination)
    main.DB_PATH = target
    os.environ["W11_FAKE_CANARY"] = "sk-FAKE-00000000000000000000"
    os.environ["W11_PUBLIC_CANARY"] = "w11-environment-must-stay-private"
    with TestClient(main.app, raise_server_exceptions=False) as client:
        debug = client.get("/debug")
        if debug.status_code in (403, 404) or (debug.status_code == 200 and all(
            value not in debug.text for value in ("W11_FAKE_CANARY", "sk-FAKE-00000000000000000000", "W11_PUBLIC_CANARY", "w11-environment-must-stay-private"))):
            fixed.append("DEBUG")
        hello = client.get("/hello", params={"name": "<script>alert(1)</script>"})
        if hello.status_code == 200 and "<script>" not in hello.text:
            fixed.append("XSS")
        error = client.get("/search", params={"pattern": "["})
        if error.status_code in (400, 422, 500) and "Traceback" not in error.text:
            fixed.append("TRACE")
        for issue, body in [("INPUT", {"board_id": 1, "title": "", "status": "todo"}),
                            ("ENUM", {"board_id": 1, "title": "Test", "status": "invalid-status"})]:
            if client.post("/cards", json=body).status_code in (400, 422):
                fixed.append(issue)
        if client.delete("/cards/1").status_code in (401, 403):
            fixed.append("AUTH")
    tree = ast.parse((root / "app/main.py").read_text())
    if not any(isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.startswith("sk-FAKE-") for node in ast.walk(tree)):
        fixed.append("SECRET")
    # Bounded-input proof: reject this known nested quantifier before matching it.
    with TestClient(main.app, raise_server_exceptions=False) as client:
        regex = client.get("/search", params={"pattern": "(a+)+$", "text": "aaaa!"})
        if regex.status_code in (400, 422):
            fixed.append("REDOS")
assert fixed, "No independently observed second fix (see TASKS.md bonus examples)"
print("PASS second fix:", ", ".join(fixed))
