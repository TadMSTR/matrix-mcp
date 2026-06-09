# Changelog

## [Unreleased]

### Added
- `plane` room added to room map (`MATRIX_ROOM_PLANE`) for Plane ticket feed notifications

### Security
- Startup validation (`_REQUIRED_VARS`) now includes all 9 `MATRIX_ROOM_*` env vars — missing room var produces clear error at startup instead of `KeyError` on first call

## [0.1.1] — 2026-04-23

### Security

- **HTML sanitization** — Markdown-rendered `formatted_body` now passed through bleach with
  a strict Matrix spec allowlist (`MATRIX_ALLOWED_TAGS`, `MATRIX_ALLOWED_ATTRS`). Prevents
  injection of `<script>`, `<iframe>`, and event handler attributes via agent-controlled message content.
- **Title escaping in `post_artifact`** — File caption rendered as HTML title is now HTML-escaped
  before inclusion in the formatted message body.
- **`post_artifact` path allowlist tightened** — Removed `/opt/appdata` and `~/docker` from
  `ARTIFACT_ALLOWED_PREFIXES`; only `~/repos/`, `~/.claude/comms/`, and `~/.claude/memory/` are permitted.

## [0.1.0] — 2026-04-23

### Added

- Initial release of `matrix-mcp` — FastMCP server for Matrix homeserver messaging
- `send_matrix_message(room, message, format)` — Send plain or Markdown text to a named room
- `get_matrix_messages(room, limit)` — Fetch recent messages from a named room
- `post_artifact(room, file_path, caption)` — Upload a local file to Matrix with path validation
- Room name resolution via `room_map.py` — short names (`sysadmin`, `developer`, `alerts`, etc.)
  mapped to Matrix room IDs from env vars; literal room IDs rejected
- `ARTIFACT_ALLOWED_PREFIXES` and `ARTIFACT_DENIED_PATTERNS` enforce path safety for file uploads
- Credentials loaded from `ENV_FILE` (default `~/.claude-secrets/matrix.env`); fails fast if any required var is missing
- PM2 ecosystem config for forge deployment
