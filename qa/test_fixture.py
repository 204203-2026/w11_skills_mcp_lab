"""Instructor fixture regression: the nine advertised weaknesses stay reproducible."""
import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient
from grader.pristine import main


def test_nine_planted_issues_and_hashed_passwords(tmp_path, monkeypatch):
    target = tmp_path / "app.db"
    with sqlite3.connect(Path(__file__).resolve().parents[1] / "data/app.db") as source:
        with sqlite3.connect(target) as destination:
            source.backup(destination)
    monkeypatch.setattr(main, "DB_PATH", target)
    monkeypatch.setenv("W11_FAKE_CANARY", "sk-FAKE-00000000000000000000")
    with sqlite3.connect(target) as db:
        rows = db.execute("SELECT name, password_hash FROM users ORDER BY id").fetchall()
    assert [r[0] for r in rows] == ["Alice", "Bob"]
    assert rows[0][1] == main.password_hash("Alice", "alice-lab")
    assert all(len(r[1]) == 64 for r in rows)
    with TestClient(main.app, raise_server_exceptions=False) as client:
        assert client.post("/login", json={"name": "admin' OR '1'='1", "password": "wrong"}).status_code == 200
        assert main.API_SECRET.startswith("sk-FAKE-0000")
        assert client.get("/debug").json()["W11_FAKE_CANARY"].startswith("sk-FAKE-")
        assert "<script>" in client.get("/hello", params={"name": "<script>"}).text
        # Tiny input demonstrates regex control without running an expensive ReDoS.
        assert client.get("/search", params={"pattern": "(a+)+$", "text": "aaa"}).json()["match"]
        error = client.get("/search", params={"pattern": "["})
        assert error.status_code == 500 and "Traceback" in error.json()["error"]
        card = client.post("/cards", json={"board_id": 1, "title": "", "status": "not-a-status"})
        assert card.status_code == 201  # Missing title and enum validation.
        assert client.delete(f"/cards/{card.json()['id']}").status_code == 200
