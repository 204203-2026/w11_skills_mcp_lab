"""Generate the same SQLite fixture on every fresh initialization."""
import hashlib
import shutil
import sqlite3
import sys
import time
from pathlib import Path

path = Path(sys.argv[1] if len(sys.argv) > 1 else "data/app.db")
path.parent.mkdir(parents=True, exist_ok=True)
if path.exists():
    # Preserve any student data before replacing the fixture.
    shutil.copy2(path, path.with_name(path.name + ".bak_" + str(time.time_ns())))
    path.unlink()
with sqlite3.connect(path) as db:
    db.executescript("""
    PRAGMA foreign_keys = ON;
    CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL);
    CREATE TABLE boards (id INTEGER PRIMARY KEY, name TEXT NOT NULL, owner_id INTEGER REFERENCES users(id));
    CREATE TABLE cards (id INTEGER PRIMARY KEY, board_id INTEGER REFERENCES boards(id), title TEXT NOT NULL, status TEXT NOT NULL);
    CREATE TABLE votes (id INTEGER PRIMARY KEY, card_id INTEGER REFERENCES cards(id) ON DELETE CASCADE, user_id INTEGER REFERENCES users(id));
    """)
    for uid, name, password in [(1, "Alice", "alice-lab"), (2, "Bob", "bob-lab")]:
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), ("w11-lab-" + name).encode(), 100_000).hex()
        db.execute("INSERT INTO users VALUES (?, ?, ?)", (uid, name, digest))
    db.execute("INSERT INTO boards VALUES (1, 'Friday lab', 1)")
    db.executemany("INSERT INTO cards VALUES (?, 1, ?, ?)", [(1, 'Write a scanner', 'todo'), (2, 'Audit the app', 'doing')])
    db.execute("INSERT INTO votes VALUES (1, 1, 2)")
print("OK deterministic fixture: users (Alice, Bob), boards, cards, votes")
