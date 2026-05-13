from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import UTC
from pathlib import Path
from types import SimpleNamespace

import pytest

from marketimmune.ingest import binance_downloader, binance_ws
from marketimmune.ingest.binance_downloader import file_sha256
from marketimmune.ingest.binance_ws import collect_messages, stream_url


def test_file_sha256_is_stable(tmp_path: Path) -> None:
    path = tmp_path / "x.bin"
    path.write_bytes(b"abc")
    assert file_sha256(path) == file_sha256(path)


def test_download_file_uses_stream(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    class FakeResponse:
        def __enter__(self) -> FakeResponse:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def raise_for_status(self) -> None:
            return None

        def iter_bytes(self) -> Iterator[bytes]:
            yield b"abc"

    def fake_stream(*_args: object, **_kwargs: object) -> FakeResponse:
        return FakeResponse()

    monkeypatch.setattr(binance_downloader.httpx, "stream", fake_stream)
    result = binance_downloader.download_file("https://example.test/x", tmp_path / "x.bin")
    assert result.bytes == 3
    assert result.path.exists()


def test_stream_url_combines_symbols_and_streams() -> None:
    assert stream_url(["BTCUSDT"], ["aggTrade"]).endswith("btcusdt@aggTrade")


@pytest.mark.asyncio
async def test_collect_messages_yields_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeSocket:
        async def __aenter__(self) -> FakeSocket:
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

        def __aiter__(self) -> FakeSocket:
            self.index = 0
            return self

        async def __anext__(self) -> str:
            if self.index > 0:
                raise StopAsyncIteration
            self.index += 1
            return json.dumps({"stream": "btcusdt@aggTrade", "data": {"x": 1}})

    monkeypatch.setattr(binance_ws.websockets, "connect", lambda _url: FakeSocket())
    messages = [message async for message in collect_messages("wss://example.test", max_messages=1)]
    assert messages[0].stream == "btcusdt@aggTrade"
    assert messages[0].received_at.tzinfo is UTC
    assert messages[0].payload == {"x": 1}


@pytest.mark.asyncio
async def test_collect_messages_yields_multiple_payloads(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeSocket:
        async def __aenter__(self) -> FakeSocket:
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

        def __aiter__(self) -> FakeSocket:
            self.index = 0
            return self

        async def __anext__(self) -> str:
            if self.index >= 2:
                raise StopAsyncIteration
            self.index += 1
            return json.dumps({"stream": "s", "data": {"index": self.index}})

    monkeypatch.setattr(binance_ws.websockets, "connect", lambda _url: FakeSocket())
    messages = [message async for message in collect_messages("wss://example.test", max_messages=2)]
    assert [message.payload["index"] for message in messages] == [1, 2]


@pytest.mark.asyncio
async def test_collect_messages_zero_max_exits() -> None:
    messages = [message async for message in collect_messages("wss://example.test", max_messages=0)]
    assert messages == []


@pytest.mark.asyncio
async def test_collect_messages_reconnects_then_yields(monkeypatch: pytest.MonkeyPatch) -> None:
    attempts = {"count": 0}

    class FakeSocket:
        async def __aenter__(self) -> FakeSocket:
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

        def __aiter__(self) -> FakeSocket:
            self.done = False
            return self

        async def __anext__(self) -> str:
            if self.done:
                raise StopAsyncIteration
            self.done = True
            return json.dumps({"stream": "s", "data": {"ok": True}})

    def fake_connect(_url: str) -> FakeSocket:
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise OSError("temporary")
        return FakeSocket()

    async def fake_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr(binance_ws.websockets, "connect", fake_connect)
    monkeypatch.setattr(binance_ws.asyncio, "sleep", fake_sleep)
    messages = [message async for message in collect_messages("wss://example.test", max_messages=1)]
    assert messages[0].payload == {"ok": True}


def test_websocket_message_dataclass() -> None:
    message = binance_ws.WebSocketMessage(
        stream="s",
        received_at=SimpleNamespace(tzinfo=UTC),  # type: ignore[arg-type]
        payload={"x": 1},
    )
    assert message.stream == "s"
