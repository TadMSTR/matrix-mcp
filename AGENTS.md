# matrix-mcp

FastMCP server providing Matrix messaging for forge agents via matrix-nio.

## What it does

Exposes 3 tools for sending messages, reading recent messages, and uploading file artifacts to Matrix rooms — identified by short names, not raw room IDs.

## Tools

- `send_matrix_message(room, message, format)` — Send plain or Markdown text to a named room. Markdown is sanitized through bleach before sending as `m.text` with `formatted_body`.
- `get_matrix_messages(room, limit)` — Fetch recent messages from a room.
- `post_artifact(room, file_path, caption)` — Upload a local file to Matrix. Path must be within `ARTIFACT_ALLOWED_PREFIXES` and must not match `ARTIFACT_DENIED_PATTERNS`.

## Structure

```
server.py                      FastMCP server — 3 tools, HTML sanitization, artifact path validation
client.py                      Async matrix-nio helpers: send_message, get_messages, upload_file
room_map.py                    Room name → Matrix room ID resolution from env vars
ecosystem.forge.config.json    PM2 config for forge
requirements.txt               Pinned exact versions
```

## Configuration

Matrix credentials (loaded via `python-dotenv` from `ENV_FILE` at import time — fails fast if missing):

| Env var                       | Purpose                                    |
|-------------------------------|--------------------------------------------|
| `MATRIX_HOMESERVER_URL`       | Matrix homeserver URL (required)           |
| `MATRIX_BOT_USER_ID`          | Bot MXID (required)                        |
| `MATRIX_ACCESS_TOKEN`         | Bot access token (required)                |

Room mappings:

| Env var                        | Room key        |
|--------------------------------|-----------------|
| `MATRIX_ROOM_SYSADMIN`         | `sysadmin`      |
| `MATRIX_ROOM_RESEARCH`         | `research`      |
| `MATRIX_ROOM_DEV`              | `developer`     |
| `MATRIX_ROOM_SECURITY`         | `security`      |
| `MATRIX_ROOM_WRITER`           | `writer`        |
| `MATRIX_ROOM_ALERTS`           | `alerts`        |
| `MATRIX_ROOM_AGENTS`           | `agents`        |
| `MATRIX_ROOM_ANNOUNCEMENTS`    | `announcements` |

## Architecture decisions

- **Room names only** — `resolve_room()` in `room_map.py` maps short names to Matrix room IDs from env vars. Passing a literal `!room:server` ID is rejected. Add new rooms to `room_map.py` and set the corresponding env var.
- **Bleach HTML sanitization** — `MATRIX_ALLOWED_TAGS` and `MATRIX_ALLOWED_ATTRS` are scoped to the Matrix spec subset that Element renders. Do not add `script`, `iframe`, or event-handler attributes to the allowlist.
- **Artifact path validation** — `validate_artifact_path()` enforces `ARTIFACT_ALLOWED_PREFIXES` (symlinks resolved via `os.path.realpath`) and `ARTIFACT_DENIED_PATTERNS` (`.env`, credentials, `.ssh/`). This is a security control — do not bypass it.

## Testing

No automated tests. Tested manually against the forge Matrix homeserver.

## Git workflow

Branch before editing — do not commit directly to `main`.
