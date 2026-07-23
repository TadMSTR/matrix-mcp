"""Tests for room name → Matrix room ID resolution.

Only room_map is exercised here — server.py performs a fail-fast env check and
network client setup at import time, which is out of scope for a unit test.
"""

import importlib

import pytest

# room_map reads these env vars lazily on first resolve; set dummies before import.
_DUMMY_ROOMS = {
    "MATRIX_ROOM_SYSADMIN": "!sysadmin:test",
    "MATRIX_ROOM_RESEARCH": "!research:test",
    "MATRIX_ROOM_DEV": "!dev:test",
    "MATRIX_ROOM_SECURITY": "!security:test",
    "MATRIX_ROOM_WRITER": "!writer:test",
    "MATRIX_ROOM_ALERTS": "!alerts:test",
    "MATRIX_ROOM_APPROVALS": "!approvals:test",
    "MATRIX_ROOM_AGENTS": "!agents:test",
    "MATRIX_ROOM_ANNOUNCEMENTS": "!announcements:test",
    "MATRIX_ROOM_PLANE": "!plane:test",
    "MATRIX_ROOM_HARLOCK": "!harlock:test",
    "MATRIX_ROOM_VIKUNJA": "!vikunja:test",
}

_EXPECTED_ROOMS = set(name.removeprefix("MATRIX_ROOM_").lower() for name in _DUMMY_ROOMS)
_EXPECTED_ROOMS.discard("dev")
_EXPECTED_ROOMS.add("developer")  # MATRIX_ROOM_DEV maps to the short name "developer"


@pytest.fixture(autouse=True)
def _load_env(monkeypatch):
    for key, value in _DUMMY_ROOMS.items():
        monkeypatch.setenv(key, value)
    import room_map

    importlib.reload(room_map)  # drop any cached map from a prior test process
    yield room_map


def test_resolve_known_room(_load_env):
    room_map = _load_env
    assert room_map.resolve_room("vikunja") == "!vikunja:test"
    assert room_map.resolve_room("harlock") == "!harlock:test"
    assert room_map.resolve_room("developer") == "!dev:test"


def test_resolve_unknown_room_raises(_load_env):
    room_map = _load_env
    with pytest.raises(ValueError):
        room_map.resolve_room("does-not-exist")


def test_list_rooms_covers_all(_load_env):
    room_map = _load_env
    names = {r["name"] for r in room_map.list_rooms()}
    assert names == _EXPECTED_ROOMS
