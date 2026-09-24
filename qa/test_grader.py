"""Focused regression checks for malformed evidence rejected by the grader."""
import json
from pathlib import Path

import pytest
from grader import check


def test_skill_requires_closing_frontmatter(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = Path('.agents/skills/security-scan/SKILL.md')
    path.parent.mkdir(parents=True)
    path.write_text('---\nname: security-scan\ndescription: Use when auditing\n')
    with pytest.raises((AssertionError, ValueError)):
        check.skill()


def test_skill_accepts_crlf_frontmatter(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = Path('.agents/skills/security-scan/SKILL.md')
    path.parent.mkdir(parents=True)
    path.write_bytes(
        b"---\r\nname: security-scan\r\ndescription: Use when auditing\r\n---\r\n"
        b"SQLI SECRET DEBUG XSS REDOS TRACE INPUT ENUM AUTH\r\n"
    )
    check.skill()


@pytest.mark.parametrize('extra', ['enabled = false\n', ''])
def test_mcp_rejects_disabled_or_error_evidence(tmp_path, monkeypatch, extra):
    monkeypatch.chdir(tmp_path)
    Path('.codex').mkdir()
    Path('reports').mkdir()
    Path('.codex/config.toml').write_text('''[mcp_servers.sqlite]
command = "uvx"
args = ["--with", "mcp<2", "mcp-server-sqlite", "--db-path", "data/app.db"]
cwd = "."
enabled_tools = ["read_query"]
disabled_tools = ["write_query", "create_table", "append_insight"]
default_tools_approval_mode = "prompt"
''' + extra)
    payload = {'rows': [{'name': 'users'}]} if extra else {'error': 'tool never ran'}
    Path('reports/mcp.md').write_text('read_query\n```json\n'+json.dumps(payload)+'\n```\n')
    with pytest.raises((AssertionError, ValueError)):
        check.mcp()


@pytest.mark.parametrize('args_line', [
    'args = ["--with", "mcp<2", "mcp-server-sqlite", "--db-path", "data/app.db"]',
    'args = ["mcp-server-sqlite", "--db-path", "data/app.db"]',
])
def test_mcp_args_shape(tmp_path, monkeypatch, args_line):
    """The --with mcp<2 guard is required. The pre-2026-09-21 shape (no guard)
    must FAIL: without it uvx resolves mcp 2.x and the server dies at startup
    (AttributeError: 'Server' object has no attribute 'list_resources')."""
    monkeypatch.chdir(tmp_path)
    Path('.codex').mkdir()
    Path('reports').mkdir()
    Path('.codex/config.toml').write_text(f'''[mcp_servers.sqlite]
command = "uvx"
{args_line}
cwd = "."
enabled_tools = ["read_query"]
disabled_tools = ["write_query", "create_table", "append_insight"]
default_tools_approval_mode = "prompt"
''')
    Path('reports/mcp.md').write_text('read_query\n```json\n[{"name": "users"}]\n```\n')
    if '<' in args_line:
        check.mcp()  # guard present: passes
    else:
        with pytest.raises(AssertionError):
            check.mcp()  # no guard: would crash at startup


def test_mcp_names_malformed_json_evidence(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path('.codex').mkdir()
    Path('reports').mkdir()
    Path('.codex/config.toml').write_text('''[mcp_servers.sqlite]
command = "uvx"
args = ["--with", "mcp<2", "mcp-server-sqlite", "--db-path", "data/app.db"]
cwd = "."
enabled_tools = ["read_query"]
disabled_tools = ["write_query", "create_table", "append_insight"]
default_tools_approval_mode = "prompt"
''')
    Path('reports/mcp.md').write_text("read_query\n```json\n{'rows': []}\n```\n")
    with pytest.raises(AssertionError, match='not valid JSON'):
        check.mcp()
