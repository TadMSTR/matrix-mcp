# matrix-mcp

FastMCP server providing Matrix homeserver communication tools for forge agent sessions.

```mermaid
flowchart LR
    subgraph session["Claude Code session"]
        T["send_matrix_message\npost_artifact\nget_matrix_messages\nlist_matrix_rooms"]
    end

    MCP["matrix-mcp\n127.0.0.1:8487"]

    subgraph syn["Synapse homeserver"]
        CA["client API"]
        MR["media repo"]
    end

    ROOMS["agent rooms\n#writer · #dev · #security\n#announcements · …"]
    EW["Element Web\noperator"]

    T -->|HTTP| MCP
    MCP -->|text / markdown| CA
    MCP -->|"file > 50 KB"| MR
    CA --> ROOMS
    MR --> ROOMS
    ROOMS --> EW
```

## Tools

| Tool | Description |
|------|-------------|
| `send_matrix_message` | Send a message to a named agent room |
| `get_matrix_messages` | Fetch recent messages from a room |
| `list_matrix_rooms` | List all agent rooms with IDs |
| `post_artifact` | Post a file's contents to a room (markdown rendered as HTML; >50KB uploaded as attachment) |

Room names are short names (`dev`, `task-queue`, `approvals`, etc.) — no `#` or `!` prefix needed.

## Rooms

| Short name | Env var | Purpose |
|------------|---------|---------|
| `sysadmin` | `MATRIX_ROOM_SYSADMIN` | Sysadmin agent activity |
| `research` | `MATRIX_ROOM_RESEARCH` | Research agent activity |
| `developer` | `MATRIX_ROOM_DEV` | Developer agent activity |
| `security` | `MATRIX_ROOM_SECURITY` | Security audit findings |
| `writer` | `MATRIX_ROOM_WRITER` | Writer agent activity |
| `alerts` | `MATRIX_ROOM_ALERTS` | System alerts and notifications |
| `agents` | `MATRIX_ROOM_AGENTS` | Cross-agent coordination |
| `announcements` | `MATRIX_ROOM_ANNOUNCEMENTS` | System-wide announcements |
| `plane` | `MATRIX_ROOM_PLANE` | Plane ticket feed notifications |

## Setup

```bash
cd ~/repos/personal/matrix-mcp
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

Credentials are loaded from `~/.claude-secrets/matrix.env` (or the path in `ENV_FILE`). Required vars:

```
MATRIX_HOMESERVER_URL=https://matrix.example.com
MATRIX_BOT_USER_ID=@bot:example.com
MATRIX_ACCESS_TOKEN=<bot token>
MATRIX_ROOM_SYSADMIN=!...:example.com
MATRIX_ROOM_RESEARCH=!...:example.com
MATRIX_ROOM_DEV=!...:example.com
MATRIX_ROOM_SECURITY=!...:example.com
MATRIX_ROOM_WRITER=!...:example.com
MATRIX_ROOM_ALERTS=!...:example.com
MATRIX_ROOM_AGENTS=!...:example.com
MATRIX_ROOM_ANNOUNCEMENTS=!...:example.com
MATRIX_ROOM_PLANE=!...:example.com
```

All room vars are validated at startup — the server exits immediately if any are missing or empty.

## Running

### PM2 (production)

```bash
pm2 start ~/repos/personal/matrix-mcp/ecosystem.config.json
pm2 save
```

### Manual

```bash
cd ~/repos/personal/matrix-mcp
ENV_FILE=~/.claude-secrets/matrix.env venv/bin/fastmcp run server.py --transport http --host 127.0.0.1 --port 8487
```

## Claude Project Integration

Add to `~/.claude.json` global MCP servers:

```json
{
  "mcpServers": {
    "matrix": {
      "type": "http",
      "url": "http://127.0.0.1:8487/mcp"
    }
  }
}
```

## Security

- Binds to `127.0.0.1` only — not reachable from LAN
- `post_artifact` validates paths against an allowlist before any filesystem access
- `get_matrix_messages` limit is capped at 100
- Unknown room names raise an error — never treated as literal room IDs
- Credentials asserted at startup; server exits with error if any are missing
