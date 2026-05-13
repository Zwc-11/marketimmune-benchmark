from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from marketimmune.ingest.binance_ws import collect_messages, stream_url


async def _run(
    symbols: list[str],
    streams: list[str],
    max_messages: int,
    output_path: Path | None,
) -> None:
    writer = output_path.open("w", encoding="utf-8") if output_path else None
    count = 0
    url = stream_url(symbols, streams)
    try:
        async for message in collect_messages(url, max_messages=max_messages):
            count += 1
            record = {
                "stream": message.stream,
                "received_at": message.received_at.isoformat(),
                "payload": message.payload,
            }
            if writer is not None:
                writer.write(json.dumps(record, sort_keys=True))
                writer.write("\n")
            else:
                print(json.dumps(record, sort_keys=True))
    finally:
        if writer is not None:
            writer.close()
    print(
        json.dumps(
            {
                "url": url,
                "symbols": [symbol.upper() for symbol in symbols],
                "streams": streams,
                "messages_collected": count,
                "output_path": str(output_path) if output_path else None,
            },
            sort_keys=True,
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect Binance public WebSocket messages.")
    parser.add_argument("--symbol", action="append", required=True)
    parser.add_argument("--stream", action="append", required=True)
    parser.add_argument("--max-messages", type=int, default=10)
    parser.add_argument("--output-path", default=None)
    args = parser.parse_args()
    output_path = Path(args.output_path) if args.output_path else None
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(_run(args.symbol, args.stream, args.max_messages, output_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
