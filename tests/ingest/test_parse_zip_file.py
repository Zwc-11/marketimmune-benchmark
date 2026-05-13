from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from marketimmune.ingest.binance_parsers import parse_zip_file
from marketimmune.ingest.binance_public import BinanceDataset


def write_zip(path: Path, name: str, body: str) -> Path:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(name, body)
    return path


def test_parse_zip_file_agg_trades(tmp_path: Path) -> None:
    path = write_zip(
        tmp_path / "a.zip",
        "a.csv",
        "id,price,qty,first,last,time,maker\n1,1,1,1,1,1,true\n",
    )
    assert len(parse_zip_file(path, dataset=BinanceDataset.AGG_TRADES, symbol="BTCUSDT")) == 1


def test_parse_zip_file_trades(tmp_path: Path) -> None:
    path = write_zip(tmp_path / "t.zip", "t.csv", "1,1,1,0,1,true\n")
    assert len(parse_zip_file(path, dataset=BinanceDataset.TRADES, symbol="BTCUSDT")) == 1


def test_parse_zip_file_book_ticker(tmp_path: Path) -> None:
    path = write_zip(tmp_path / "b.zip", "b.csv", "1,1,1,2,1,1\n")
    assert len(parse_zip_file(path, dataset=BinanceDataset.BOOK_TICKER, symbol="BTCUSDT")) == 1


def test_parse_zip_file_book_depth(tmp_path: Path) -> None:
    path = write_zip(
        tmp_path / "d.zip",
        "d.csv",
        "timestamp,percentage,depth,notional\n2026-05-11 00:00:08,-5.00,8754.63,702612935.17\n",
    )
    events = parse_zip_file(path, dataset=BinanceDataset.BOOK_DEPTH, symbol="BTCUSDT")
    assert len(events) == 1
    assert events[0].event_type == "book_depth"


def test_parse_zip_file_klines_requires_interval(tmp_path: Path) -> None:
    path = write_zip(tmp_path / "k.zip", "k.csv", "1,1,2,1,1,1,2,1,1,1,1,0\n")
    with pytest.raises(ValueError, match="requires an interval"):
        parse_zip_file(path, dataset=BinanceDataset.KLINES, symbol="BTCUSDT")


def test_parse_zip_file_klines(tmp_path: Path) -> None:
    path = write_zip(tmp_path / "k.zip", "k.csv", "1,1,2,1,1,1,2,1,1,1,1,0\n")
    assert (
        len(parse_zip_file(path, dataset=BinanceDataset.KLINES, symbol="BTCUSDT", interval="1m"))
        == 1
    )


def test_parse_zip_file_mark_price_klines(tmp_path: Path) -> None:
    path = write_zip(tmp_path / "m.zip", "m.csv", "1,1,2,1,1,1,2,1,1,1,1,0\n")
    events = parse_zip_file(
        path,
        dataset=BinanceDataset.MARK_PRICE_KLINES,
        symbol="BTCUSDT",
        interval="1m",
    )
    assert len(events) == 1


def test_parse_zip_file_multiple_csv_rejected(tmp_path: Path) -> None:
    path = tmp_path / "bad.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("a.csv", "x")
        archive.writestr("b.csv", "x")
    with pytest.raises(ValueError, match="expected exactly one CSV"):
        parse_zip_file(path, dataset=BinanceDataset.TRADES, symbol="BTCUSDT")


def test_parse_zip_file_unsupported_dataset(tmp_path: Path) -> None:
    path = write_zip(tmp_path / "u.zip", "u.csv", "1,1,1,0,1,true\n")

    class UnsupportedDataset:
        value = "unsupported"

    dataset = UnsupportedDataset()
    with pytest.raises(ValueError, match="unsupported dataset"):
        parse_zip_file(path, dataset=dataset, symbol="BTCUSDT")  # type: ignore[arg-type]
