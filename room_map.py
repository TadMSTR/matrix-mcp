"""Room name → Matrix room ID resolution. Room IDs loaded from env at import time."""

import os

_ROOM_MAP: dict[str, str] = {}


def _load_room_map() -> dict[str, str]:
    return {
        "sysadmin":      os.environ["MATRIX_ROOM_SYSADMIN"],
        "research":      os.environ["MATRIX_ROOM_RESEARCH"],
        "developer":     os.environ["MATRIX_ROOM_DEV"],
        "security":      os.environ["MATRIX_ROOM_SECURITY"],
        "writer":        os.environ["MATRIX_ROOM_WRITER"],
        "alerts":        os.environ["MATRIX_ROOM_ALERTS"],
        "agents":        os.environ["MATRIX_ROOM_AGENTS"],
        "announcements": os.environ["MATRIX_ROOM_ANNOUNCEMENTS"],
    }


def resolve_room(room_name: str) -> str:
    """Return the Matrix room ID for a short room name.

    Raises ValueError for unknown room names — never treats input as a literal ID.
    """
    global _ROOM_MAP
    if not _ROOM_MAP:
        _ROOM_MAP = _load_room_map()
    room_id = _ROOM_MAP.get(room_name)
    if room_id is None:
        known = ", ".join(sorted(_ROOM_MAP.keys()))
        raise ValueError(
            f"Unknown room name '{room_name}'. Known rooms: {known}"
        )
    return room_id


def list_rooms() -> list[dict]:
    """Return all rooms as a list of {name, room_id} dicts."""
    global _ROOM_MAP
    if not _ROOM_MAP:
        _ROOM_MAP = _load_room_map()
    return [{"name": name, "room_id": room_id} for name, room_id in _ROOM_MAP.items()]
