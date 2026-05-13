from __future__ import annotations

from pathlib import Path

import pytest

from marketimmune.ingest.binance_parsers import (
    parse_agg_trades,
    parse_book_ticker,
    parse_klines,
    parse_trades,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def fixture_lines(name: str) -> list[str]:
    return (FIXTURES / name).read_text(encoding="utf-8").splitlines()


def test_parse_agg_trades_count() -> None:
    assert len(parse_agg_trades(fixture_lines("agg_trades.csv"), "BTCUSDT")) == 2


def test_parse_agg_trades_symbol_normalized() -> None:
    event = parse_agg_trades(fixture_lines("agg_trades.csv"), "btcusdt")[0]
    assert event.symbol == "BTCUSDT"


def test_parse_agg_trades_event_id_is_stable() -> None:
    first = parse_agg_trades(fixture_lines("agg_trades.csv"), "BTCUSDT")[0]
    second = parse_agg_trades(fixture_lines("agg_trades.csv"), "BTCUSDT")[0]
    assert first.event_id == second.event_id


def test_parse_agg_trades_preserves_buyer_maker_flag() -> None:
    assert parse_agg_trades(fixture_lines("agg_trades.csv"), "BTCUSDT")[0].is_buyer_maker is True


def test_parse_trades_count() -> None:
    assert len(parse_trades(fixture_lines("trades.csv"), "BTCUSDT")) == 2


def test_parse_trades_side_from_buyer_maker() -> None:
    first, second = parse_trades(fixture_lines("trades.csv"), "BTCUSDT")
    assert first.side == "sell"
    assert second.side == "buy"


def test_parse_trades_timestamp_is_timezone_aware() -> None:
    event = parse_trades(fixture_lines("trades.csv"), "BTCUSDT")[0]
    assert event.timestamp.tzinfo is not None


def test_parse_book_ticker_count() -> None:
    assert len(parse_book_ticker(fixture_lines("book_ticker.csv"), "BTCUSDT")) == 2


def test_parse_book_ticker_bid_below_ask() -> None:
    event = parse_book_ticker(fixture_lines("book_ticker.csv"), "BTCUSDT")[0]
    assert event.bid_price < event.ask_price


def test_parse_book_ticker_update_id() -> None:
    event = parse_book_ticker(fixture_lines("book_ticker.csv"), "BTCUSDT")[1]
    assert event.update_id == 301


def test_parse_klines_count() -> None:
    assert len(parse_klines(fixture_lines("klines.csv"), "BTCUSDT", "1m")) == 2


def test_parse_klines_interval() -> None:
    event = parse_klines(fixture_lines("klines.csv"), "BTCUSDT", "1m")[0]
    assert event.interval == "1m"


def test_parse_klines_trade_count() -> None:
    event = parse_klines(fixture_lines("klines.csv"), "BTCUSDT", "1m")[1]
    assert event.trade_count == 50


def test_parse_invalid_book_cross_fails() -> None:
    with pytest.raises(ValueError, match="bid_price"):
        parse_book_ticker(["1,2,1,1,1,1714521600000"], "BTCUSDT")


def test_parse_invalid_agg_trade_range_fails() -> None:
    with pytest.raises(ValueError, match="last_trade_id"):
        parse_agg_trades(["1,65000,1,9,8,1714521600000,true"], "BTCUSDT")
