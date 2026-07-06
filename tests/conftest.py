"""Shared test setup: populate dummy Matrix env vars before client/server import.

server.py performs a fail-fast check on all MATRIX_* vars at import time, and
client.py reads credentials from the environment. Setting these here (via
conftest, imported before any test module) lets both modules import cleanly
without real credentials or a real homeserver.
"""

import os

_DUMMY_ENV = {
    "ENV_FILE": "/nonexistent/matrix.env",  # load_dotenv no-ops on a missing file
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
    "MATRIX_ROOM_VIKUNJA": "!vikunja:test",
}

for _key, _value in _DUMMY_ENV.items():
    os.environ.setdefault(_key, _value)
