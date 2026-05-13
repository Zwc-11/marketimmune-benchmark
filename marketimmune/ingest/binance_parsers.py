from __future__ import annotations

import csv
import zipfile
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from marketimmune.ingest.binance_public import KLINE_DATASETS, BinanceDataset
from marketimmune.schemas.events import (
    AggTradeEvent,
    BookDepthEvent,
    BookTickerEvent,
    CanonicalEvent,
    KlineEvent,
    Side,
    TradeEvent,
    utc_ms,
)


def _rows(lines: Iterable[str]) -> Iterable[list[str]]:
    for row in csv.reader(line for line in lines if line.strip()):
        if row and row[0].strip().lower() in {"id", "timestamp", "open_time"}:
            continue
        yield row


def parse_agg_trades(lines: Iterable[str], symbol: str) -> list[AggTradeEvent]:
    events: list[AggTradeEvent] = []
    for sequence, row in enumerate(_rows(lines)):
        trade_time_ms = int(row[5])
        events.append(
            AggTradeEvent(
                symbol=symbol.upper(),
                timestamp=utc_ms(trade_time_ms),
                sequence=sequence,
                aggregate_trade_id=int(row[0]),
                price=float(row[1]),
                quantity=float(row[2]),
                first_trade_id=int(row[3]),
                last_trade_id=int(row[4]),
                is_buyer_maker=row[6].lower() == "true",
            )
        )
    return events


def parse_trades(lines: Iterable[str], symbol: str) -> list[TradeEvent]:
    events: list[TradeEvent] = []
    for sequence, row in enumerate(_rows(lines)):
        trade_time_ms = int(row[4])
        side = Side.SELL if row[5].lower() == "true" else Side.BUY
        events.append(
            TradeEvent(
                symbol=symbol.upper(),
                timestamp=utc_ms(trade_time_ms),
                sequence=sequence,
                trade_id=int(row[0]),
                price=float(row[1]),
                quantity=float(row[2]),
                side=side,
            )
        )
    return events


def parse_book_ticker(lines: Iterable[str], symbol: str) -> list[BookTickerEvent]:
    events: list[BookTickerEvent] = []
    for sequence, row in enumerate(_rows(lines)):
        event_time_ms = int(row[5]) if len(row) > 5 else int(row[0])
        events.append(
            BookTickerEvent(
                symbol=symbol.upper(),
                timestamp=utc_ms(event_time_ms),
                sequence=sequence,
                update_id=int(row[0]),
                bid_price=float(row[1]),
                bid_quantity=float(row[2]),
                ask_price=float(row[3]),
                ask_quantity=float(row[4]),
            )
        )
    return events


def parse_book_depth(lines: Iterable[str], symbol: str) -> list[BookDepthEvent]:
    events: list[BookDepthEvent] = []
    for sequence, row in enumerate(_rows(lines)):
        timestamp = datetime.fromisoformat(row[0]).replace(tzinfo=UTC)
        events.append(
            BookDepthEvent(
                symbol=symbol.upper(),
                timestamp=timestamp,
                sequence=sequence,
                percentage=float(row[1]),
                depth=float(row[2]),
                notional=float(row[3]),
            )
        )
    return events


def parse_klines(lines: Iterable[str], symbol: str, interval: str) -> list[KlineEvent]:
    events: list[KlineEvent] = []
    for sequence, row in enumerate(_rows(lines)):
        open_time = utc_ms(int(row[0]))
        close_time = utc_ms(int(row[6]))
        events.append(
            KlineEvent(
                symbol=symbol.upper(),
                timestamp=datetime.fromtimestamp(int(row[6]) / 1000, tz=UTC),
                sequence=sequence,
                interval=interval,
                open_time=open_time,
                close_time=close_time,
                open_price=float(row[1]),
                high_price=float(row[2]),
                low_price=float(row[3]),
                close_price=float(row[4]),
                volume=float(row[5]),
                trade_count=int(row[8]),
            )
        )
    return events


def parse_zip_file(
    path: Path,
    *,
    dataset: BinanceDataset,
    symbol: str,
    interval: str | None = None,
) -> list[CanonicalEvent]:
    with zipfile.ZipFile(path) as archive:
        csv_names = [name for name in archive.namelist() if name.endswith(".csv")]
        if len(csv_names) != 1:
            raise ValueError(f"expected exactly one CSV in {path}, found {len(csv_names)}")
        with archive.open(csv_names[0]) as handle:
            lines = (line.decode("utf-8") for line in handle)
            if dataset is BinanceDataset.AGG_TRADES:
                return cast(list[CanonicalEvent], parse_agg_trades(lines, symbol))
            if dataset is BinanceDataset.TRADES:
                return cast(list[CanonicalEvent], parse_trades(lines, symbol))
            if dataset is BinanceDataset.BOOK_DEPTH:
                return cast(list[CanonicalEvent], parse_book_depth(lines, symbol))
            if dataset is BinanceDataset.BOOK_TICKER:
                return cast(list[CanonicalEvent], parse_book_ticker(lines, symbol))
            if dataset in KLINE_DATASETS:
                if interval is None:
                    raise ValueError(f"{dataset.value} requires an interval")
                return cast(list[CanonicalEvent], parse_klines(lines, symbol, interval))
    raise ValueError(f"unsupported dataset: {dataset.value}")
