"""TeamBoard security lab: intentionally unsafe. Bind to loopback only."""

import hashlib
import os
import re
import sqlite3
import traceback
from contextlib import contextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

app = FastAPI(title="TeamBoard security lab")
DB_PATH = Path(__file__).resolve().parents[1] / "data" / "app.db"
API_SECRET = "sk-FAKE-00000000000000000000000000000000"


def password_hash(name: str, password: str) -> str:
    """Deterministic lab salts; passwords are deliberately NOT stored in plaintext."""
    salt = ("w11-lab-" + name).encode()
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000).hex()


@contextmanager
def database():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


class Login(BaseModel):
    name: str
    password: str


class Card(BaseModel):
    board_id: int
    title: str
    status: str = "todo"


@app.get("/")
def home():
    return {"app": "TeamBoard", "lab": "Week 11", "docs": "/docs"}


@app.post("/login")
def login(body: Login):
    digest = password_hash(body.name, body.password)
    query = f"SELECT id, name FROM users WHERE password_hash = '{digest}' AND name = '{body.name}'"
    with database() as db:
        user = db.execute(query).fetchone()
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"id": user["id"], "name": user["name"]}


@app.get("/debug")
def debug():
    return dict(os.environ)


@app.get("/hello", response_class=HTMLResponse)
def hello(name: str = "student"):
    return HTMLResponse(f"<h1>Hello {name}</h1>")


@app.get("/search")
def search(pattern: str, text: str = "TeamBoard"):
    return {"match": bool(re.search(pattern, text))}


@app.exception_handler(Exception)
async def errors(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": traceback.format_exc()})


@app.get("/boards")
def boards():
    with database() as db:
        return [dict(row) for row in db.execute("SELECT * FROM boards ORDER BY id")]


@app.get("/cards")
def cards():
    with database() as db:
        return [dict(row) for row in db.execute("SELECT * FROM cards ORDER BY id")]


@app.post("/cards", status_code=201)
def create_card(body: Card):
    with database() as db:
        cursor = db.execute(
            "INSERT INTO cards (board_id, title, status) VALUES (?, ?, ?)",
            (body.board_id, body.title, body.status),
        )
        return {"id": cursor.lastrowid, **body.model_dump()}


@app.delete("/cards/{card_id}")
def delete_card(card_id: int):
    with database() as db:
        cursor = db.execute("DELETE FROM cards WHERE id = ?", (card_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Card not found")
    return {"deleted": card_id}


@app.get("/cards/{card_id}")
def get_card(card_id: int):
    with database() as db:
        row = db.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Card not found")
    return dict(row)


@app.get("/votes")
def votes():
    with database() as db:
        return [dict(row) for row in db.execute("SELECT * FROM votes ORDER BY id")]
