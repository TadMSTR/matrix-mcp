# Changelog

## [Unreleased]

## [0.2.0] — 2026-07-06

### Added
- `plane` room added to room map (`MATRIX_ROOM_PLANE`) for Plane ticket feed notifications
- `harlock` room added to room map (`MATRIX_ROOM_HARLOCK`) for the Harlock personal agent
- `vikunja` room added to room map (`MATRIX_ROOM_VIKUNJA`) for Vikunja task/webhook notifications
- GitHub Actions CI (`.github/workflows/ci.yml`): full `ruff check` + `ruff format --check`, byte-compile, and pytest with coverage on Python 3.12/3.13
- `tests/test_room_map.py` covering room resolution, unknown-room rejection, and full room coverage
- `ruff.toml` pinning lint/format config (documents the intentional `E402` exception in `server.py`)

### Changed
- Codebase reformatted with `ruff format`; imports cleaned up

### Fixed
- Documentation sync: `harlock` documented in README; `plane`, `harlock`, `vikunja` added to the AGENTS.md room table (previously only code had them)

### Security
- Startup validation (`_REQUIRED_VARS`) now includes all 11 `MATRIX_ROOM_*` env vars — a missing room var produces a clear error at startup instead of a `KeyError` on first call

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
