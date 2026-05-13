from __future__ import annotations

from datetime import date

import pytest

from marketimmune.ingest.binance_public import BinanceDataset, daily_object


def test_agg_trade_url_points_to_usdm_public_data() -> None:
    obj = daily_object(BinanceDataset.AGG_TRADES, "btcusdt", date(2024, 5, 1))
    assert obj.url.endswith(
        "/data/futures/um/daily/aggTrades/BTCUSDT/BTCUSDT-aggTrades-2024-05-01.zip"
    )


def test_trades_filename() -> None:
    obj = daily_object(BinanceDataset.TRADES, "ETHUSDT", date(2024, 5, 1))
    assert obj.filename == "ETHUSDT-trades-2024-05-01.zip"


def test_book_depth_filename() -> None:
    obj = daily_object(BinanceDataset.BOOK_DEPTH, "BTCUSDT", date(2026, 5, 11))
    assert obj.filename == "BTCUSDT-bookDepth-2026-05-11.zip"


def test_kline_url_includes_interval() -> None:
    obj = daily_object(BinanceDataset.KLINES, "SOLUSDT", date(2024, 5, 1), "1m")
    assert "/klines/SOLUSDT/1m/" in obj.url


def test_kline_without_interval_fails() -> None:
    obj = daily_object(BinanceDataset.KLINES, "SOLUSDT", date(2024, 5, 1))
    with pytest.raises(ValueError, match="klines require"):
        _ = obj.filename
