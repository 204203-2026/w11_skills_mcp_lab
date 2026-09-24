import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from app import main


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Every test receives an isolated fixture; destructive tests never change data/app.db.
    target = tmp_path / "app.db"
    with sqlite3.connect(Path(__file__).resolve().parents[1] / "data/app.db") as source:
        with sqlite3.connect(target) as destination:
            source.backup(destination)
    monkeypatch.setattr(main, "DB_PATH", target)
    with TestClient(main.app, raise_server_exceptions=False) as test_client:
        yield test_client
