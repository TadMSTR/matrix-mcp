"""Matrix MCP server — FastMCP + matrix-nio, port 8487."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load credentials before any module that reads env vars
_env_file = os.environ.get("ENV_FILE", os.path.expanduser("~/.claude-secrets/matrix.env"))
load_dotenv(_env_file)

# Fail fast: assert required credentials are present
_REQUIRED_VARS = ["MATRIX_HOMESERVER_URL", "MATRIX_BOT_USER_ID", "MATRIX_ACCESS_TOKEN"]
for _var in _REQUIRED_VARS:
    if not os.environ.get(_var):
        print(f"ERROR: Required environment variable '{_var}' is missing or empty.", file=sys.stderr)
        print(f"  Loaded from: {_env_file}", file=sys.stderr)
        sys.exit(1)

import markdown as md_lib
from fastmcp import FastMCP

from client import get_messages, send_message, upload_file
from room_map import list_rooms, resolve_room

ARTIFACT_ALLOWED_PREFIXES = [
    "/home/ted/repos/",
    "/home/ted/docker/",
    "/opt/appdata/",
    "/home/ted/.claude/comms/",
    "/home/ted/.claude/memory/",
]

ARTIFACT_DENIED_PATTERNS = [
    ".env", ".secret", "matrix.env", "claude-secrets",
    "id_rsa", "id_ed25519", ".ssh/",
]


def validate_artifact_path(file_path: str) -> str:
    resolved = os.path.realpath(os.path.expanduser(file_path))
    for denied in ARTIFACT_DENIED_PATTERNS:
        if denied in resolved:
            raise ValueError(f"post_artifact: path contains denied pattern '{denied}'")
    if not any(resolved.startswith(prefix) for prefix in ARTIFACT_ALLOWED_PREFIXES):
        raise ValueError(
            f"post_artifact: path '{resolved}' is outside allowed directories. "
            f"Allowed: {ARTIFACT_ALLOWED_PREFIXES}"
        )
    return resolved


mcp = FastMCP(
    name="matrix",
    instructions=(
        "Matrix homeserver communications for claudebox agents. "
        "Use room short names (e.g. 'dev', 'task-queue') — no # or ! prefix needed."
    ),
)


@mcp.tool()
async def send_matrix_message(
    room_name: str,
    message: str,
    html: bool = False,
    reply_to_event_id: str | None = None,
) -> dict:
    """Send a message to a named Matrix room.

    room_name: short name (e.g. 'task-queue', 'dev') — no # or ! prefix.
    html: set True to render message as HTML in Element.
    reply_to_event_id: thread reply to a specific event_id from get_matrix_messages.
    """
    room_id = resolve_room(room_name)
    return await send_message(room_id, message, html=html, reply_to_event_id=reply_to_event_id)


@mcp.tool()
async def get_matrix_messages(
    room_name: str,
    limit: int = 10,
    since_hours: int | None = None,
) -> list[dict]:
    """Get recent messages from a named Matrix room.

    Returns list of {sender, body, timestamp, timestamp_utc, event_id}.
    limit: max messages to return (capped at 100).
    since_hours: if set, return only messages from the last N hours.
    """
    if limit > 100:
        raise ValueError("limit must be 100 or less")
    if limit < 1:
        raise ValueError("limit must be at least 1")
    room_id = resolve_room(room_name)
    return await get_messages(room_id, limit=limit, since_hours=since_hours)


@mcp.tool()
async def list_matrix_rooms() -> list[dict]:
    """List all available agent rooms with names and room IDs."""
    return list_rooms()


@mcp.tool()
async def post_artifact(room_name: str, file_path: str, title: str = "") -> dict:
    """Read a file from claudebox and post its contents to a Matrix room.

    Markdown files are converted to HTML for Element rendering.
    Files over 50KB are uploaded as attachments via the Matrix media store.
    file_path must be within allowed directories (repos, docker, appdata, comms, memory).
    """
    resolved = validate_artifact_path(file_path)
    room_id = resolve_room(room_name)
    path = Path(resolved)

    if not path.exists():
        raise ValueError(f"File not found: {resolved}")

    raw = path.read_bytes()
    size = len(raw)

    if size > 50 * 1024:
        return await upload_file(room_id, raw, filename=path.name)

    text = raw.decode("utf-8", errors="replace")
    header = f"**{title}**\n\n" if title else ""

    if path.suffix.lower() in (".md", ".markdown"):
        html_body = md_lib.markdown(text, extensions=["fenced_code", "tables"])
        message = header + html_body
        return await send_message(room_id, message, html=True)
    else:
        message = header + f"```\n{text}\n```"
        return await send_message(room_id, message)
