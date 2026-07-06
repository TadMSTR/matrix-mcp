"""Tests for client.py — the matrix-nio async wrapper.

Network I/O is mocked: get_client() is patched to hand back a fake AsyncClient
whose methods are AsyncMocks. nio response types are faked with
MagicMock(spec=...) so the wrapper's isinstance() checks still pass.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from nio import RoomMessagesResponse, RoomMessageText, RoomSendResponse

import client


@pytest.fixture(autouse=True)
def _reset_client_singleton():
    # get_client() caches a module-global client behind a module-global lock.
    # Reset both before each test so the lock binds to the current test's loop.
    client._client = None
    client._client_lock = asyncio.Lock()
    yield
    client._client = None


def _mock_client(monkeypatch):
    fake = MagicMock()
    monkeypatch.setattr(client, "get_client", AsyncMock(return_value=fake))
    return fake


def _send_response(event_id="$evt:test"):
    resp = MagicMock(spec=RoomSendResponse)
    resp.event_id = event_id
    return resp


# --- _get_config / get_client --------------------------------------------------


def test_get_config_reads_env():
    url, user_id, token = client._get_config()
    assert url == "https://matrix.test"
    assert user_id == "@bot:test"
    assert token == "test-token"


async def test_get_client_caches_and_sets_token():
    first = await client.get_client()
    assert first.access_token == "test-token"
    assert first.user_id == "@bot:test"
    # Second call returns the same cached instance.
    second = await client.get_client()
    assert first is second


# --- send_message --------------------------------------------------------------


async def test_send_message_plain(monkeypatch):
    fake = _mock_client(monkeypatch)
    fake.room_send = AsyncMock(return_value=_send_response("$s1:test"))

    result = await client.send_message("!room:test", "hello")

    assert result == {"event_id": "$s1:test", "room_id": "!room:test"}
    _, kwargs = fake.room_send.call_args
    assert kwargs["room_id"] == "!room:test"
    assert kwargs["message_type"] == "m.room.message"
    assert kwargs["content"] == {"msgtype": "m.text", "body": "hello"}


async def test_send_message_html_and_reply(monkeypatch):
    fake = _mock_client(monkeypatch)
    fake.room_send = AsyncMock(return_value=_send_response())

    await client.send_message("!room:test", "<b>hi</b>", html=True, reply_to_event_id="$parent")

    content = fake.room_send.call_args.kwargs["content"]
    assert content["format"] == "org.matrix.custom.html"
    assert content["formatted_body"] == "<b>hi</b>"
    assert content["m.relates_to"] == {"m.in_reply_to": {"event_id": "$parent"}}


async def test_send_message_raises_on_error_response(monkeypatch):
    fake = _mock_client(monkeypatch)
    fake.room_send = AsyncMock(return_value=MagicMock())  # not a RoomSendResponse

    with pytest.raises(RuntimeError, match="Failed to send message"):
        await client.send_message("!room:test", "hello")


# --- get_messages --------------------------------------------------------------


def _text_event(ts_ms, sender="@a:test", body="hi", event_id="$e"):
    ev = MagicMock(spec=RoomMessageText)
    ev.server_timestamp = ts_ms
    ev.sender = sender
    ev.body = body
    ev.event_id = event_id
    return ev


async def test_get_messages_maps_and_skips_non_text(monkeypatch):
    fake = _mock_client(monkeypatch)
    resp = MagicMock(spec=RoomMessagesResponse)
    resp.chunk = [_text_event(1_700_000_000_000, body="one"), MagicMock()]  # 2nd skipped
    fake.room_messages = AsyncMock(return_value=resp)

    messages = await client.get_messages("!room:test", limit=10)

    assert len(messages) == 1
    assert messages[0]["body"] == "one"
    assert messages[0]["sender"] == "@a:test"
    assert messages[0]["timestamp"] == 1_700_000_000_000
    assert messages[0]["timestamp_utc"].startswith("2023-11-14")


async def test_get_messages_since_hours_filters_old(monkeypatch):
    fake = _mock_client(monkeypatch)
    now_ms = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
    old_ms = int((datetime.now(tz=timezone.utc) - timedelta(hours=2)).timestamp() * 1000)
    resp = MagicMock(spec=RoomMessagesResponse)
    resp.chunk = [_text_event(now_ms, body="new"), _text_event(old_ms, body="old")]
    fake.room_messages = AsyncMock(return_value=resp)

    messages = await client.get_messages("!room:test", limit=10, since_hours=1)

    bodies = [m["body"] for m in messages]
    assert bodies == ["new"]


async def test_get_messages_raises_on_error_response(monkeypatch):
    fake = _mock_client(monkeypatch)
    fake.room_messages = AsyncMock(return_value=MagicMock())  # not a RoomMessagesResponse

    with pytest.raises(RuntimeError, match="Failed to fetch messages"):
        await client.get_messages("!room:test")


# --- upload_file ---------------------------------------------------------------


async def test_upload_file_success(monkeypatch):
    fake = _mock_client(monkeypatch)
    upload_resp = MagicMock()
    upload_resp.content_uri = "mxc://test/abc"
    fake.upload = AsyncMock(return_value=(upload_resp, None))
    fake.room_send = AsyncMock(return_value=_send_response("$file:test"))

    result = await client.upload_file("!room:test", b"payload", filename="report.txt")

    assert result == {"event_id": "$file:test", "mxc_uri": "mxc://test/abc"}
    content = fake.room_send.call_args.kwargs["content"]
    assert content["msgtype"] == "m.file"
    assert content["url"] == "mxc://test/abc"
    assert content["info"]["size"] == len(b"payload")


async def test_upload_file_raises_when_send_fails(monkeypatch):
    fake = _mock_client(monkeypatch)
    upload_resp = MagicMock()
    upload_resp.content_uri = "mxc://test/abc"
    fake.upload = AsyncMock(return_value=(upload_resp, None))
    fake.room_send = AsyncMock(return_value=MagicMock())  # not a RoomSendResponse

    with pytest.raises(RuntimeError, match="Failed to send file message"):
        await client.upload_file("!room:test", b"payload", filename="report.txt")
