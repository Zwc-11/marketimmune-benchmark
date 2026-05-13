from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime

import websockets


@dataclass(frozen=True)
class WebSocketMessage:
    stream: str
    received_at: datetime
    payload: dict[str, object]


def stream_url(symbols: list[str], streams: list[str]) -> str:
    parts = [f"{symbol.lower()}@{stream}" for symbol in symbols for stream in streams]
    return "wss://fstream.binance.com/stream?streams=" + "/".join(parts)


async def collect_messages(
    url: str,
    *,
    max_messages: int | None = None,
    reconnect_delay_seconds: float = 1.0,
) -> AsyncIterator[WebSocketMessage]:
    emitted = 0
    while max_messages is None or emitted < max_messages:  # pragma: no branch
        try:
            async with websockets.connect(url) as socket:
                async for raw_message in socket:  # pragma: no branch
                    decoded = json.loads(raw_message)
                    emitted += 1
                    yield WebSocketMessage(
                        stream=str(decoded.get("stream", "")),
                        received_at=datetime.now(tz=UTC),
                        payload=dict(decoded.get("data", decoded)),
                    )
                    if max_messages is not None and emitted >= max_messages:
                        return
        except (OSError, websockets.WebSocketException):
            await asyncio.sleep(reconnect_delay_seconds)
