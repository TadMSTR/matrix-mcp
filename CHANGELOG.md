# Changelog

## [Unreleased]

## [0.3.0] — 2026-11-14

### Added
- `pyproject.toml` (a virtual project: nothing is built or installed) and a committed `uv.lock`
- Minimum versions for the packages a tool call reaches: fastmcp 3.4.10, mcp 1.30.0, starlette 1.3.1, python-multipart 0.0.31, anyio 4.14.2, h11 0.16.0, opentelemetry-api 1.45.2, pyjwt 2.15, aiohttp 3.14.4, multidict 6.9.1, h2 4.4.1, markdown 3.8.1, bleach 6.4.0, pygments 2.20.0, python-dotenv 1.2.2
- CI audits the locked runtime and dev sets separately, checks `uv lock --check`, and runs a gating job against the newest allowed versions; weekly as well as on push

### Changed
- The README install section is now a script that builds `venv/` from a fresh clone of a release tag's `uv.lock` and checks the checkout byte-for-byte against the release
- The README says what an early stop of the install script leaves behind, and how to recover
- fastmcp is bounded below 4 (it was `>=2.0`, unbounded)
- CI installs from the lock with uv; every action is pinned to a commit SHA
- `release.yml`: `contents: write` moved from the workflow to the release job; checkout no longer persists credentials
- `.gitignore` covers `.env.*` and core dumps (`*.core`, `core.[0-9]*`)

### Removed
- `requirements.txt`: `uv.lock` replaces it
- `plane` room and `MATRIX_ROOM_PLANE` (Plane is decommissioned; matrix-notify-overhaul-2026-10 p1). The variable is no longer required at startup.

## [0.2.1] — 2026-07-06

### Added
- Unit tests for `client.py` (mocked matrix-nio) and `server.py` (FastMCP tools, artifact-path validation, startup fail-fast) — total coverage now 99% (`client`/`room_map` 100%, `server` 96%)

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
