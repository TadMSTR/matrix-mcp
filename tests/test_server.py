"""Tests for server.py — the FastMCP tool layer and artifact-path validation.

client.py functions and room resolution are patched at the server module level
(the tools look them up as module globals at call time). FastMCP tool objects
are unwrapped to their underlying coroutine via ``.fn`` when needed.
"""

import os
import subprocess
import sys
from unittest.mock import AsyncMock

import pytest

import server

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _tool_fn(tool):
    """Return the raw coroutine function whether or not FastMCP wrapped it."""
    return getattr(tool, "fn", tool)


# --- validate_artifact_path ----------------------------------------------------


# --- startup fail-fast ---------------------------------------------------------


def test_missing_required_var_exits_nonzero():
    """Importing server with a required var absent must exit(1) with a clear error."""
    env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": _REPO_ROOT,
        "ENV_FILE": "/nonexistent/matrix.env",
        "MATRIX_HOMESERVER_URL": "https://matrix.test",
        "MATRIX_BOT_USER_ID": "@bot:test",
        "MATRIX_ACCESS_TOKEN": "test-token",
        "MATRIX_ROOM_SYSADMIN": "!sysadmin:test",
        "MATRIX_ROOM_RESEARCH": "!research:test",
        "MATRIX_ROOM_DEV": "!dev:test",
        "MATRIX_ROOM_SECURITY": "!security:test",
        "MATRIX_ROOM_WRITER": "!writer:test",
        "MATRIX_ROOM_ALERTS": "!alerts:test",
        "MATRIX_ROOM_AGENTS": "!agents:test",
        "MATRIX_ROOM_ANNOUNCEMENTS": "!announcements:test",
        "MATRIX_ROOM_PLANE": "!plane:test",
        "MATRIX_ROOM_HARLOCK": "!harlock:test",
        # MATRIX_ROOM_VIKUNJA intentionally omitted
    }
    proc = subprocess.run(
        [sys.executable, "-c", "import server"],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 1
    assert "MATRIX_ROOM_VIKUNJA" in proc.stderr


def test_validate_artifact_path_allows_repo_path():
    resolved = server.validate_artifact_path("/home/ted/repos/proj/notes.md")
    assert resolved == "/home/ted/repos/proj/notes.md"


def test_validate_artifact_path_rejects_denied_pattern():
    with pytest.raises(ValueError, match="denied pattern"):
        server.validate_artifact_path("/home/ted/repos/proj/prod.env")


def test_validate_artifact_path_rejects_outside_allowed_dirs():
    with pytest.raises(ValueError, match="outside allowed directories"):
        server.validate_artifact_path("/etc/passwd")


# --- send_matrix_message -------------------------------------------------------


async def test_send_matrix_message_resolves_and_forwards(monkeypatch):
    monkeypatch.setattr(server, "resolve_room", lambda name: f"!{name}:test")
    send = AsyncMock(return_value={"event_id": "$e", "room_id": "!dev:test"})
    monkeypatch.setattr(server, "send_message", send)

    result = await _tool_fn(server.send_matrix_message)("dev", "hi", html=True)

    assert result == {"event_id": "$e", "room_id": "!dev:test"}
    send.assert_awaited_once_with("!dev:test", "hi", html=True, reply_to_event_id=None)


# --- get_matrix_messages -------------------------------------------------------


@pytest.mark.parametrize("bad_limit", [0, 101])
async def test_get_matrix_messages_rejects_out_of_range_limit(bad_limit):
    with pytest.raises(ValueError, match="limit must be"):
        await _tool_fn(server.get_matrix_messages)("dev", limit=bad_limit)


async def test_get_matrix_messages_happy_path(monkeypatch):
    monkeypatch.setattr(server, "resolve_room", lambda name: f"!{name}:test")
    getter = AsyncMock(return_value=[{"body": "hi"}])
    monkeypatch.setattr(server, "get_messages", getter)

    result = await _tool_fn(server.get_matrix_messages)("dev", limit=5, since_hours=3)

    assert result == [{"body": "hi"}]
    getter.assert_awaited_once_with("!dev:test", limit=5, since_hours=3)


# --- list_matrix_rooms ---------------------------------------------------------


async def test_list_matrix_rooms_returns_configured_rooms():
    rooms = await _tool_fn(server.list_matrix_rooms)()
    names = {r["name"] for r in rooms}
    assert {"vikunja", "harlock", "plane", "developer"} <= names


# --- post_artifact -------------------------------------------------------------


@pytest.fixture
def allow_tmp(monkeypatch, tmp_path):
    monkeypatch.setattr(server, "ARTIFACT_ALLOWED_PREFIXES", [str(tmp_path)])
    return tmp_path


async def test_post_artifact_markdown_sends_sanitized_html(monkeypatch, allow_tmp):
    md = allow_tmp / "note.md"
    md.write_text("# Title\n\n**bold** and <script>alert(1)</script>")
    send = AsyncMock(return_value={"event_id": "$md"})
    monkeypatch.setattr(server, "send_message", send)
    monkeypatch.setattr(server, "resolve_room", lambda name: f"!{name}:test")

    result = await _tool_fn(server.post_artifact)("dev", str(md), title="My Note")

    assert result == {"event_id": "$md"}
    args, kwargs = send.call_args
    body = args[1]
    assert kwargs["html"] is True
    assert "<strong>My Note</strong>" in body
    assert "<script>" not in body  # sanitized out


async def test_post_artifact_plaintext_sends_code_block(monkeypatch, allow_tmp):
    txt = allow_tmp / "log.txt"
    txt.write_text("line one\nline two")
    send = AsyncMock(return_value={"event_id": "$txt"})
    monkeypatch.setattr(server, "send_message", send)
    monkeypatch.setattr(server, "resolve_room", lambda name: f"!{name}:test")

    await _tool_fn(server.post_artifact)("dev", str(txt))

    body = send.call_args.args[1]
    assert body.startswith("```")
    assert "line one" in body
    # plaintext path does not pass html=True
    assert "html" not in send.call_args.kwargs or send.call_args.kwargs.get("html") is not True


async def test_post_artifact_large_file_uploads(monkeypatch, allow_tmp):
    big = allow_tmp / "big.bin"
    big.write_bytes(b"x" * (50 * 1024 + 1))
    upload = AsyncMock(return_value={"event_id": "$up", "mxc_uri": "mxc://x"})
    monkeypatch.setattr(server, "upload_file", upload)
    monkeypatch.setattr(server, "resolve_room", lambda name: f"!{name}:test")

    result = await _tool_fn(server.post_artifact)("dev", str(big))

    assert result == {"event_id": "$up", "mxc_uri": "mxc://x"}
    upload.assert_awaited_once()
    assert upload.call_args.args[0] == "!dev:test"


async def test_post_artifact_missing_file_raises(monkeypatch, allow_tmp):
    monkeypatch.setattr(server, "resolve_room", lambda name: f"!{name}:test")
    missing = allow_tmp / "nope.txt"

    with pytest.raises(ValueError, match="File not found"):
        await _tool_fn(server.post_artifact)("dev", str(missing))
