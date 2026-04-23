"""matrix-nio async client wrapper for the Matrix MCP server."""

import asyncio
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from nio import AsyncClient, LoginResponse, RoomSendResponse, RoomMessagesResponse, RoomMessageText

SYNC_TOKEN_PATH = Path("/opt/appdata/matrix/mcp-sync-token")


def _get_config() -> tuple[str, str, str]:
    url = os.environ["MATRIX_HOMESERVER_URL"]
    user_id = os.environ["MATRIX_BOT_USER_ID"]
    token = os.environ["MATRIX_ACCESS_TOKEN"]
    return url, user_id, token


_client: AsyncClient | None = None
_client_lock = asyncio.Lock()


async def get_client() -> AsyncClient:
    global _client
    async with _client_lock:
        if _client is None:
            url, user_id, token = _get_config()
            _client = AsyncClient(url, user_id)
            _client.access_token = token
            _client.user_id = user_id
        return _client


async def send_message(
    room_id: str,
    message: str,
    html: bool = False,
    reply_to_event_id: str | None = None,
) -> dict:
    client = await get_client()
    content: dict = {"msgtype": "m.text", "body": message}
    if html:
        content["format"] = "org.matrix.custom.html"
        content["formatted_body"] = message
    if reply_to_event_id:
        content["m.relates_to"] = {"m.in_reply_to": {"event_id": reply_to_event_id}}

    resp = await client.room_send(room_id=room_id, message_type="m.room.message", content=content)
    if isinstance(resp, RoomSendResponse):
        return {"event_id": resp.event_id, "room_id": room_id}
    raise RuntimeError(f"Failed to send message: {resp}")


async def get_messages(
    room_id: str,
    limit: int = 10,
    since_hours: int | None = None,
) -> list[dict]:
    client = await get_client()
    resp = await client.room_messages(room_id=room_id, start="", limit=limit)
    if not isinstance(resp, RoomMessagesResponse):
        raise RuntimeError(f"Failed to fetch messages: {resp}")

    messages = []
    for event in resp.chunk:
        if not isinstance(event, RoomMessageText):
            continue
        ts_ms = event.server_timestamp
        messages.append({
            "sender": event.sender,
            "body": event.body,
            "timestamp": ts_ms,
            "timestamp_utc": datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).isoformat(),
            "event_id": event.event_id,
        })

    if since_hours is not None:
        cutoff_ms = (datetime.now(tz=timezone.utc) - timedelta(hours=since_hours)).timestamp() * 1000
        messages = [m for m in messages if m["timestamp"] >= cutoff_ms]

    return messages


async def upload_file(room_id: str, data: bytes, filename: str, content_type: str = "text/plain") -> dict:
    client = await get_client()
    resp, _ = await client.upload(
        data_provider=lambda *_: asyncio.get_event_loop().run_in_executor(None, lambda: data),
        content_type=content_type,
        filename=filename,
        filesize=len(data),
    )
    mxc_uri = resp.content_uri
    content = {
        "msgtype": "m.file",
        "body": filename,
        "url": mxc_uri,
        "info": {"size": len(data), "mimetype": content_type},
    }
    send_resp = await client.room_send(room_id=room_id, message_type="m.room.message", content=content)
    if isinstance(send_resp, RoomSendResponse):
        return {"event_id": send_resp.event_id, "mxc_uri": mxc_uri}
    raise RuntimeError(f"Failed to send file message: {send_resp}")
