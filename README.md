# w11_skills_mcp_lab

**This is the graded lab (Fri 25 Sep).** It ships a small FastAPI app with
nine planted security weaknesses. Your job is to write a project skill,
extend a repeatable scanner, fix SQL injection with a test, and connect
read-only SQLite + Mermaid MCP tools.

## Start here

1. **Use this template** → owner `204203-2026`, name `w11_skills_mcp_lab-<SID>`
   (replace `<SID>` with your student ID), **Private**.
2. Pick where you work — **Track A** a local machine (lab machine or your own
   Ubuntu/Mac) or **Track B** your own VM over SSH. `TASKS.md` Step 0 sets up
   either; grading is identical. Install its prerequisites on the machine
   where you run the lab.
3. Clone your copy there, then run `bash init.sh`. It installs the locked
   Python environment with uv and generates `data/app.db`.
4. Open `TASKS.md` and follow it top to bottom. It is the lab sheet.

`pyproject.toml` and `uv.lock` live at the **repo root**. Run all lab commands
there. `bash check.sh` writes seven required checks to `results/report.json`
and optional bonuses to `results/challenge_report.json`. CI recomputes both
reports; all seven required checks must pass. Bonus never changes your grade.

**The app is intentionally vulnerable.** Use only the supplied fake lab
credentials. Start it on `127.0.0.1:56734`; never expose it publicly or put
real secrets in its environment. Alice and Bob are the only seeded users;
passwords are hashed on purpose.

TASKS.md is the only file you follow; this README is how to get in the door.
