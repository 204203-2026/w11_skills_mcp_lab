# w11_skills_mcp_lab — Lab Sheet (Fri 25 Sep)

**This is the graded lab.** This is self-study: expect about **4–5 hours solo**
over several sittings. Friday's 2 hours are drop-in help, not the time budget.
The repo stays open until **Mon 28 Sep, 23:59** (the grader reads the last CI
run). You work in
**Codex CLI**, signed in with your ChatGPT account. Where to run: **your
choice** — Track A (a local machine: the lab machine or your own Ubuntu/Mac)
or Track B (your own VM over SSH). Step 0 sets up either one. Grading is
identical on both.

This app is vulnerable on purpose. Your job is the **evaluator around the
app**: a skill, a scanner, a test that proves one fix, and outside tools with
limited permissions. Use only fake lab credentials and keep the server on
`127.0.0.1`. Do not deploy it or load real secrets into its environment.

Every required check is deterministic and offline. Setup and the first MCP
server start need network access; grading does not start an MCP server.
`bash check.sh` gives your score any time. CI recomputes the checks and
commits `results/*.json` back, so a hand-edited `results/*.json` grade never survives.
Bonus checks never affect the grade.

**Lecture note — Claude Code (reference only; this lab runs Codex).**
From Claude Code v2.1.277, the
`CLAUDE.md` symlink is optional: with no `CLAUDE.md` in your working directory
or above it, Claude reads `AGENTS.md` directly. Both files present →
`CLAUDE.md` wins; `AGENTS.md` alone → it is used. The toggle is under
`/config` → **Project instructions**.

## Prerequisites — install these before the lab

**The same list for both tracks.** Track A: on your local machine. Track B:
**on the VM** — your laptop needs an SSH client, a browser, and VS Code with
**Remote-SSH**. Reuse your Week 10 installations: Git, Python 3.11 or newer,
uv (including `uvx`), Node 20+ (including `npx`, installed in Week 8 for Vite),
Codex CLI, and VS Code. Week 8 ran its app through `docker compose`; Week 11
does not use it at all — the app runs directly under uv, and nothing in this
lab starts a container.

If any tool is missing, install it before the lab, not during it:

```console
$ git --version && python3 --version    # git; Python >= 3.11
$ curl -LsSf https://astral.sh/uv/install.sh | sh   # uv + uvx
$ node --version                        # >= 20 (you installed it in Week 8)
$ npm install -g @openai/codex          # Codex CLI
```

`pyproject.toml` and `uv.lock` live at the **repo root**, beside `TASKS.md`,
not inside `app/`. Run every shell command below from that root. Python
packages belong to this uv project; do not use `pip install` or create a
`requirements.txt`. `uvx` and `npx` below launch standalone MCP tools: `uvx`
runs the ones published on PyPI, `npx` the ones published on npm.

## Step 0 — Pick a track, set up, sign in (20 min)

Pick **one** track. Every step after this one is the same on both.

| | Track A — local machine | Track B — your VM over SSH |
|---|---|---|
| where | the lab machine or your own Ubuntu/Mac | your own Ubuntu VM |
| edit with | VS Code on that machine | VS Code **Remote-SSH** from your laptop |
| see the app (optional) | `http://localhost:56734` | the same URL through an SSH tunnel |
| install first | prerequisites on this machine | prerequisites **on the VM** |

### Track A — local machine

Inside your clone:

```console
$ bash init.sh
$ codex --version
$ codex
```

Success looks like: `init.sh` ends with `OK deterministic fixture: users
(Alice, Bob), boards, cards, votes` and `OK workspace ready. Open TASKS.md
and begin Step 0.`, and `codex --version` prints a version number. It is
safe to run `bash init.sh` again — the fixture is regenerated identically.
Sign in with your ChatGPT account if this is your first run.

### Track B — your VM

For optional browser viewing, connect with the app port forwarded and keep
this SSH session open:

```console
$ ssh -L 56734:localhost:56734 you@vm-host
```

Or, in your VS Code Remote-SSH connection: **Ports** view → **Forward a Port** → `56734` does the same thing without a second terminal.
Both routes send your laptop's `localhost:56734` to the VM's loopback; nobody
needs an open public app port. Remote-SSH does not forward this port automatically.

On the VM, inside your clone:

```console
$ bash init.sh
$ codex --version
$ codex login --device-auth
$ codex login status
$ codex
```

Device sign-in gives you a link and a code. Open the link in your laptop's
browser.

To edit comfortably: install **Remote - SSH** in your laptop's VS Code,
choose **Remote-SSH: Connect to Host…**, then open your clone on the VM.
Check the bottom-left corner says `SSH: <your host>`. Its terminal now runs
on the VM. Run every command there, including `codex` and `bash check.sh`.

### Both tracks

Create `student.json` at the repo root:

```json
{
  "name": "Your Name",
  "student_id": "680XXXXXX"
}
```

Use your real name and student ID, not these placeholders. Run
`bash check.sh`: check 1 (`student_json`) must be PASS before you continue.
In Codex, run `/skills` to see the built-in skills. Use the model and effort
selected for class; `/status` shows the current session. Any model passes —
every check reads your files offline and never calls the model.

`init.sh` creates `data/app.db` deterministically with `users`, `boards`,
`cards`, and `votes`. Alice and Bob are the only seeded users. Their fake lab
passwords are `alice-lab` and `bob-lab`; stored values are hashes. The DB is
generated, so do not commit it — `.gitignore` already excludes `data/*.db`;
leave that line alone. Keep `pyproject.toml` and `uv.lock` committed.

The starter tests use FastAPI `TestClient`; they do not need a running server:

```console
$ uv run --offline --frozen pytest -q
```

Expect **3 passed** (a dependency deprecation warning is normal). If this
fails on a fresh clone, run `bash init.sh` again before debugging anything.

### OPTIONAL — See the app you are about to attack

Nothing in this lab is graded through a browser. Step 4's exploit test runs
in-process with FastAPI's `TestClient`, and every required check is offline.
This step lets you look at the app before attacking it: `/docs` lists its
routes, including the vulnerable `/login`.

Start the server in a second terminal (on the VM for Track B):

```console
$ uv run --offline --frozen uvicorn app.main:app --host 127.0.0.1 --port 56734
```

Use either tool to test the running app; they answer different questions:

| curl | Browser |
|---|---|
| “What does this endpoint return?” | “What endpoints are there at all?” |
| Run on the machine hosting the server; no forwarding needed. | Open on your laptop; Track B needs either forwarded-port route from Step 0. |
| Fast, scriptable; shows the raw JSON an attacker sees. Use it to poke at an endpoint once you suspect it. | FastAPI's generated documentation lists every route and its parameters, and lets you send a request from the page. Use it to see the app's surface, including the vulnerable `/login`, before attacking it. |

**curl — on the server's machine:**

```console
$ curl -s http://127.0.0.1:56734/ | head -5
$ curl -s -X POST http://127.0.0.1:56734/login \
    -H 'content-type: application/json' \
    -d '{"name": "Alice", "password": "wrong"}'
```

**Browser — on your laptop (with Track B's port forwarded):**

```text
http://localhost:56734/docs
```

Stop the server with `Ctrl+C` when done.

## Step 1 — Write your security skill (30 min)

Create `.agents/skills/security-scan/SKILL.md` yourself. Skills in this lab
are **project-scoped**: commit that directory with your work. Do not put it
in a home-directory skills folder. You can ask the built-in `$skill-creator`
for a first draft, then read and correct what it writes.

Start with YAML frontmatter between `---` lines. `name` **must equal the
folder name**, `security-scan`. `description` must be non-empty and contain
**"Use when"** (same spelling and case), followed by real tasks that should
trigger your skill. Do **not** use `allowed-tools`: that is a Claude-only
key for this lab. The cross-vendor Agent Skills spec defines it as an optional
experimental field, but Codex does not honour it: tool access comes from
permissions and approvals, so this lab rejects the key.

Your Markdown body must tell Codex to inspect these ten items. CWE is a
public numbering of common software weakness types.

| item | inspect | report ID |
|---|---|---|
| 1 | SQL injection in the string-built login query | `SQLI` |
| 2 | Hardcoded secret, even when its value is obviously fake | `SECRET` |
| 3 | `/debug` leaking environment variables | `DEBUG` |
| 4 | Reflected cross-site scripting: unescaped user input in HTML (XSS) | `XSS` |
| 5 | User-supplied regular expressions (ReDoS) | `REDOS` |
| 6 | Error responses exposing stack traces | `TRACE` |
| 7 | Missing input validation | `INPUT` |
| 8 | Missing enum validation | `ENUM` |
| 9 | Unauthenticated deletion | `AUTH` |
| 10 | Plaintext password storage — **CWE-256** | not planted |

There are **nine planted vulnerabilities**, not ten. Passwords stay hashed
on purpose. Your skill should distinguish evidence from suspicion; do not
invent a plaintext-password finding to fill the checklist.

Check 2 reads the body and requires all nine planted report IDs above. Use a
short checklist in this shape; the table remains the source of truth for each ID.

```markdown
## Checklist
SQLI - inspect the string-built login query
SECRET - inspect hardcoded secrets
...
AUTH - inspect unauthenticated deletion
```

Give the skill a report format: a Markdown table with **ID / Severity /
File:line / Evidence / Suggested fix**. Tell it to run the scanner, examine
the source, explain false positives, and avoid claiming the app is secure
because a small scanner is quiet. Restart Codex if the new skill is not
listed by `/skills`. Still missing after a restart: check the folder is
exactly `.agents/skills/security-scan/` with `SKILL.md` inside, keep the
frontmatter `name` equal to the folder name, and restart once more.

The lecture's Priority values are teaching defaults. The grader does not grade
severity; use a defensible judgement.

### Lecture reference — skill loading and file limits

Codex initially sees each skill's `name`, `description`, and path. The
initial list uses at most **2%** of the context window; if the window is
unknown, the limit is **8,000 characters**. With many skills, descriptions
shorten first; some entries may be omitted with a warning. Codex reads the
full `SKILL.md` when it selects that skill.

Agent Skills spec (`agentskills.io`): `name` is at most **64 characters**,
using lowercase letters, digits and hyphens, with no leading, trailing or
doubled hyphen; it **must equal the folder name**. `description` is at most
**1024 characters** and states both what the skill does and when to use it.
Keep the body under **500 lines** and move detail to `references/`.
The optional support directories are `scripts/`, `references/`, and `assets/`.
You can type the file yourself or let `$skill-creator` draft it.

## Step 2 — Extend the scanner, record red first (45 min)

Read `scripts/scan.py`. It ships with exactly **two working detectors**:
`SECRET` and `DEBUG`. Add **at least three detectors of your own**, using
Python's stdlib regex over the supplied `app/*.py` files.
One must detect `SQLI`; choose any two other planted issues for the minimum
five. Do this **before** fixing the app.

The scanner runs sandboxed at grading time: use only stdlib `re` and `pathlib`;
do not use subprocesses or the network. A bare `SELECT` regex also matches the
app's other, correctly parameterized queries, so anchor `SQLI` on the f-string
interpolation rather than the SQL keyword. `SQLI`, `XSS`, `TRACE`, `SECRET`, and
`DEBUG` detect presence of a bad pattern. `INPUT`, `ENUM`, and `AUTH` require
proving a missing safeguard, so choose deliberately: they are harder detectors.

Keep its interface: the positional argument is the directory to scan. Read
that directory instead of hardcoding your own `app/` — the grader runs your
scanner against its own copy of the app, under a different directory name, so a
hardcoded path finds nothing there. Only the issue ID, the file name and the
line number are graded; the directory part of the path may be whatever you
scanned. Print one finding per line, followed by one total line:

```text
ISSUE_ID app/main.py:LINE short evidence description
TOTAL: N
```

Replace `ISSUE_ID` with a report ID from Step 1 and `LINE` with the actual
1-based source line containing the evidence. Each known issue counts once;
printing duplicates does not earn extra credit. `TOTAL: N` must match the
number of findings. A clean input should print `TOTAL: 0`, with no findings.
Do not print a fixed answer or import the app to scan it.

The exact command, from the repo root where `pyproject.toml` lives:

```console
$ mkdir -p reports docs
$ uv run --offline --frozen python scripts/scan.py app | tee reports/scan_before.txt
```

Expect at least five distinct findings, including `SQLI`. If you get fewer:
your regexes are missing planted patterns — re-check each of the ten item
types against `app/main.py` line by line (every planted issue maps to exactly
one ID). If the scanner crashes or prints `TOTAL: 0`: test each regex against
the one function it targets before running the whole app. If a clean input
prints findings: your patterns match benign code — tighten them. Save this
run before changing `app/main.py`. The grader runs **your scanner against its
own pristine app**, with its own ground truth and a clean negative control.
Editing a fixture or printing an empty report cannot pass check 3.

### Lecture command reference — skills and plugins

These are reference routes, not additional lab requirements. Inside Codex,
`$skill-installer <name>` installs curated skills into your personal skill
directory. Examples, verbatim from the lecture:

```text
$skill-installer linear
$skill-installer pdf
```

The third-party `skills.sh` CLI (`vercel-labs/skills`, 32k stars) accepts any
repo across tools: one skill, many agents. Run from the project folder;
`-a codex` selects Codex. These examples write `.agents/skills/pdf/` under
project scope `.agents/skills/`; omit `-g`.

```text
npx skills add <repo> --skill <name> -a codex
npx skills add anthropics/skills --skill pdf -a codex
```

Then `/plugins` browses marketplace packages and installs the **bundle**.
`/skills` lists available / loaded skills inside Codex. Anyone can publish;
skills use your permissions. Read `SKILL.md` and `scripts/` before trusting them.

Also in the curated catalog: `figma`, `jupyter-notebook`, `openai-docs`,
`cli-creator`, `netlify-deploy`, `cloudflare-deploy`, `notion-*`.
`gh-fix-ci` and `jupyter-notebook` ship `scripts/`; `pdf` and `linear` do not.
Instructions come first; scripts are for answers that must be deterministic.

A marketplace repository contains `.claude-plugin/marketplace.json`.
`codex plugin marketplace add <owner>/<repo>` consumes that repository.
`/` separates alternatives in command families, while `/plugins` runs inside
Codex.

```text
codex plugin marketplace add <owner>/<repo>      # also owner/repo@ref, a git URL, or a local dir
codex plugin marketplace list                    # includes implicitly discovered defaults
codex plugin marketplace upgrade / remove
codex plugin add / list / remove
/plugins                                         # browse installed and discoverable
```

On `npx skills add`, `--ref` pins a git ref and `--sparse PATH` takes a
sparse checkout of a repo subfolder.

## Step 3 — Use the skill to audit (25 min)

In Codex:

```text
$security-scan audit app/main.py
```

If Codex calls the skill unknown, `/skills` must list `security-scan` — fix
per Step 1 (folder name must equal the skill name), then restart Codex.

Read its evidence against the source. Save the resulting table in
`reports/audit.md` with the columns you specified in Step 1. Keep real source
line references. Mark SQL injection Critical and explain why the login query
can accept the wrong password. List what remains unfixed; the audit is not
permission to rewrite the whole app.

## Step 4 — Test first, then fix SQL injection (50 min)

Write **`tests/test_sqli.py` before touching the login code**. Reuse the
`client` fixture in `tests/conftest.py`; it gives you a FastAPI `TestClient`.
Your test must call `POST /login` with JSON keys `name` and `password`:

```python
def test_login_rejects_sql_injection(client):
    response = client.post(
        "/login",
        json={"name": "admin' OR '1'='1", "password": "wrong-password"},
    )
    assert response.status_code == 401
```

Run it and **watch the assertion fail on the pristine app**:

```console
$ uv run --offline --frozen pytest -q tests/test_sqli.py
$ git add tests/test_sqli.py
$ git commit -m "test: reject SQL injection at login (red)"
```

If the test PASSES on the pristine app, it asserts nothing — correct the
payload until it fails, then commit. This commit is intentionally red: it
records the test before the fix. Now
ask Codex for a surgical fix to SQL injection in `app/main.py`. Bind values
as SQL parameters; preserve correct password verification and ordinary
Alice/Bob login behavior. Do not remove the endpoint, allow all logins, or
replace the exploit with an easier test.

```console
$ uv run --offline --frozen pytest -q tests/test_sqli.py
$ uv run --offline --frozen pytest -q
$ git add app/main.py
$ git commit -m "fix: parameterize the login query"
```

Both test runs must pass. Full suite red after the fix? The fix likely
broke ordinary Alice/Bob logins or removed the endpoint — re-read the
constraints above, repair, and rerun. Check 4 also runs the **grader's own
exploit**; your test file alone cannot prove the fix. Keep these two commits separate
for the `red_first` bonus.

## Step 5 — Re-scan: did the count drop? (15 min)

Keep your before report. Run the same scanner against your fixed app:

```console
$ uv run --offline --frozen python scripts/scan.py app | tee reports/scan_after.txt
```

The count should drop by **one**, and the `SQLI` finding should disappear.
If it does not, inspect your detector and your fix. Do not edit the number
by hand or remove a detector. The re-scan decides. Add a short before/after
note to `reports/audit.md` and commit your scanner, skill, and reports.
Once `reports/scan_after.txt` is committed, do **not** regenerate it after
adding detectors later: check 5 compares these frozen snapshots. A larger
detector set can raise the after-count and falsely read as “you did not fix
the SQLi.”

### Lecture reference — the same pattern at scale

`cloudflare/security-audit-skill` repository snapshot: **2026-09-20**.

Checklist = example; reviews/releases/data cleaning reuse this pattern: agent steps, script verdict, evidence beyond sessions.

## Step 6 — Connect SQLite MCP (25 min)

Create project `.codex/config.toml`. Keep it in this trusted project, not
in `~/.codex/config.toml`. Add this server block:

```toml
[mcp_servers.sqlite]
command = "uvx"
args = ["--with", "mcp<2", "mcp-server-sqlite", "--db-path", "data/app.db"]
cwd = "."
```

`required = true` is optional. If set, Codex fails startup when this server
cannot initialize instead of continuing without it.

`cwd = "."` makes the database path relative to the repo root. Always start
Codex from that root. Restart Codex and inspect `/mcp` (or `/mcp verbose`
for startup errors). Do not ask it to change the database. Complete Step 7
before calling tools: the server block above restricts nothing by itself —
the allow-list in Step 7 is what restricts it.

A one-line `--with "mcp<2"` guard is in the args on purpose. Pinning the
server package is not enough: `uvx` re-resolves its dependencies on a cold
run, and `mcp` 2.x removed the decorator this server uses, so it now dies
at startup with `AttributeError: 'Server' object has no attribute
'list_resources'` (verified 2026-09-21). The guard keeps the dependency in
the 1.x line. Same lesson as Part 7: dependencies drift even when your own
pin is exact.

### Lecture lookup — MCP servers

The lecture's reference counts and names:

| Group / repository | Stars | Servers or job | Launcher |
|---|---:|---|---|
| Official: `modelcontextprotocol/servers` | 90k | Exactly seven: `everything`, `fetch`, `filesystem`, `git`, `memory`, `sequentialthinking`, `time` | See the repository |
| `upstash/context7` | 62k | Current library docs, so the agent stops guessing APIs | See the repository |
| `microsoft/playwright-mcp` | 37k | Drive a real browser | See the repository |
| `github/github-mcp-server` | 33k | Issues, PRs, code search — GitHub's own | See the repository |
| Friday: `mcp-server-sqlite` | — | SQLite; small, local, one job | `uvx` |
| Friday: `mermaid-mcp-app` | — | Mermaid; small, local, one job | `npx` |

The two launcher commands corresponding to Steps 6 and 8 are:

```sh
uvx --with "mcp<2" mcp-server-sqlite --db-path data/app.db
npx -y mermaid-mcp-app@0.4.4
```

The project config starts these servers for Codex; use the SQLite permission
limits in Step 7 before calling tools.

## Step 7 — Limit permissions, then query (30 min)

Extend that **same sqlite block**, rather than adding a duplicate TOML table:

```toml
enabled_tools = ["list_tables", "describe_table", "read_query"]
disabled_tools = ["write_query", "create_table", "append_insight"]
default_tools_approval_mode = "prompt"
```

All six sqlite tool names use underscores (`list_tables`, `describe_table`,
`read_query`, `write_query`, `create_table`, `append_insight`) — check them
against `/mcp` if a name is ever rejected. Keep only read tools enabled
and deny all three write tools **by name**. Restart Codex and inspect `/mcp`: it must list `sqlite` with no startup
errors (the first launch downloads the server from PyPI — one-time network,
cached afterwards). Then ask Codex in chat to run the query, e.g. type:

```text
Call the read_query tool with: SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name;
```

An approval prompt appears — that is the `default_tools_approval_mode = "prompt"`
you configured; approve it. The tool runs the query:

```sql
SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name;
```

Create `reports/mcp.md`. Name the tool `read_query`, quote the SQL, and paste
the **actual returned result** in a fenced `json` block. Preserve the result's
structure, including any text-content wrapper. It should show `boards`,
`cards`, `users`, and `votes`. Add one sentence explaining why this tool is
allowed and the three write tools are denied. A promise to run it later is
not evidence. Commit `.codex/config.toml` and `reports/mcp.md`.

## Step 8 — Add Mermaid and draw the schema (45 min)

Append this second server to the same `.codex/config.toml`:

```toml
[mcp_servers.mermaid]
command = "npx"
args = ["-y", "mermaid-mcp-app@0.4.4"]
```

`mermaid-mcp-app` is published on **npm**, not PyPI — that is why this server
launches with `npx` while the sqlite server uses `uvx`. Check which registry a
server lives on before you write its `command`. You **must** use the reviewed
`mermaid-mcp-app@0.4.4` pin (lecture Part 7: a server's code and tool
descriptions can change silently on republish).

Restart Codex; `/mcp` should show both servers. First launch downloads the
package, so you need network for this step.

If the server will not start, work through this yourself — you are likely doing
this step outside class:

1. `npx -y mermaid-mcp-app@0.4.4` in a terminal. A healthy start prints
   `Mermaid MCP App server running on stdio` and then waits; `Ctrl-C` to exit.
2. `node --version` must be 20 or newer.
3. No network, or a blocked npm registry, makes `npx` hang on first run. Retry
   on a different network; the package is cached after one success.
4. Still stuck on every network: leave the render for later — under a
   `## mermaid` heading in `reports/mcp.md`, record the Mermaid tool call,
   source `docs/er.mmd`, render target `docs/er.png`, and the exact error if
   it never ran (otherwise record the actual tool result). Finish the rest of
   the lab and retry before the deadline; the package caches after one success.
   Never install a similarly named package or claim a render that did not happen.

Ask Codex to inspect the SQLite schema through `read_query`, write
`docs/er.mmd`, and call the **Mermaid MCP** tool with the diagram source as
its `code` argument. The tool checks the source and returns it as structured
JSON — it does not write image files; the picture comes from a viewer, and
Codex CLI hosts none. Useful SQL for the schema:

```sql
SELECT name, sql FROM sqlite_master WHERE type = 'table' ORDER BY name;
```

`docs/er.mmd` must start with `erDiagram` (no Markdown fences in that file)
and name every actual table: `users`, `boards`, `cards`, `votes`. Show fields
and relationships from the query, not guessed ones. In `reports/mcp.md`, note
the Mermaid tool call, its source `docs/er.mmd`, its render target
`docs/er.png`, and paste the **actual tool result** (the echoed structured
JSON). The picture itself is optional for the grade: render `docs/er.png` with
any renderer outside Codex — `mermaid.live` in your browser, or
`npx -y @mermaid-js/mermaid-cli -i docs/er.mmd -o docs/er.png` — and commit it
if you made it. Commit the config, source, image and report. Grading reads your saved config
and evidence offline; it does not contact either MCP server.

## Step 9 — Bonus: draw the scan pipeline (15 min)

Render **scan → audit → fix → re-scan** as a flowchart to a real image file.
Save the source in `docs/scan_flow.mmd` (start with `flowchart`, no Markdown
fences), then produce `docs/scan_flow.png` with any renderer — `mermaid.live`
in your browser is easiest; `npx -y @mermaid-js/mermaid-cli -i
docs/scan_flow.mmd -o docs/scan_flow.png` works too. This bonus check reads
the PNG bytes, so the image must actually exist. Call the Mermaid MCP tool
with the source as well, and record in `reports/mcp.md` the render, both
filenames, and the tool result, then commit them.

Other optional challenges: fix a second vulnerability with its own
regression test in `tests/test_second_fix.py`, and extend your scanner to all
nine planted issues. The two red/green commits from Step 4 already earn the
`red_first` bonus — no extra work needed. The simplest second fix is `/debug`
(remove or forbid the route, or return no environment data). Finish the
required work first. If you fix `/debug`, capture its failing test before the
fix and rerun all tests afterward, just as you did for SQL injection.

The second-fix check recognizes: remove the hardcoded fake secret; close the debug
leak; escape HTML; reject the nested pattern `(a+)+$` with 400/422; hide stack
traces; reject an empty card title or an unsupported status with 400/422; require
authentication on deletion (401/403). Keep normal routes working. For the simplest
bonus path, remove `/debug` and test that it returns 404.

## Grading

Run `bash check.sh` any time. Required (all seven needed):

| check | what it wants |
|---|---|
| 1 | Valid `student.json` with your real name and student ID |
| 2 | Project `security-scan/SKILL.md`: matching `name`, description containing "Use when", no `allowed-tools` |
| 3 | Your offline scanner finds at least five distinct planted issues, including SQLi, in the grader's own pristine app |
| 4 | The grader's SQLi exploit gets 401, and your `tests/test_sqli.py` exists and passes |
| 5 | `reports/scan_before.txt` count is greater than `reports/scan_after.txt` count |
| 6 | SQLite MCP config is restricted to read tools, with named write denials, and `reports/mcp.md` quotes one `read_query` result |
| 7 | Mermaid MCP configured; `docs/er.mmd` starts with `erDiagram` and names every DB table; `reports/mcp.md` records the Mermaid tool call and its result |

Bonus (never affects the grade):

| name | what it wants |
|---|---|
| `red_first` | Git history contains the SQLi test before the SQLi fix |
| `second_fix` | A second vulnerability fixed, with `tests/test_second_fix.py` passing |
| `scanner_all` | Scanner finds all nine planted issues |
| `scan_flow` | `docs/scan_flow.mmd` and a real `docs/scan_flow.png`, with render evidence |

`results/report.json` contains required checks only.
`results/challenge_report.json` contains bonus only. `check.sh` always exits
0 so it can write every result; read the score, not the shell exit status.
CI's separate required-check gate fails the job if required work is missing.
Do not edit the checker, grader fixtures, or workflows to manufacture passes.

## Submit

```console
$ bash check.sh      # read your score first
$ bash submit.sh     # commits + pushes your student copy; CI recomputes the reports
```

Then read the last CI run: repo → **Actions** tab → workflow **Grade
w11_skills_mcp_lab** → latest run. Green means the recomputed reports were
committed — `git pull` brings them down. The score is the
`Score: N / 7 required | ...` line in the run log (and the `score` field of
`results/report.json`). Pull before your next edit.

## Lecture quiz review

*A1.* `AGENTS.md` loads at startup, every session. A skill contributes only its `name` and `description` up front; the `SKILL.md` body is read when the skill is selected

*A2.* `$security-scan` — type `$` or run `/skills` to browse. There is no `/security-scan` command

*A3.* A tool that actually runs: the server executes the query and returns live rows. A skill supplies judgment, not data — instructions alone cannot reach the database

*A4.* `enabled_tools` is an allow list of the tools Codex may call on that server. It does *not* sandbox the process: the server still runs with your permissions

*A5.* Proof the detectors fire — run the same scanner against a known-vulnerable copy. Zero findings means either clean code or a broken scanner, and the two look identical
