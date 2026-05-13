from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class BinanceDataset(StrEnum):
    AGG_TRADES = "aggTrades"
    TRADES = "trades"
    BOOK_DEPTH = "bookDepth"
    BOOK_TICKER = "bookTicker"
    KLINES = "klines"
    MARK_PRICE_KLINES = "markPriceKlines"
    INDEX_PRICE_KLINES = "indexPriceKlines"
    PREMIUM_INDEX_KLINES = "premiumIndexKlines"


KLINE_DATASETS = {
    BinanceDataset.KLINES,
    BinanceDataset.MARK_PRICE_KLINES,
    BinanceDataset.INDEX_PRICE_KLINES,
    BinanceDataset.PREMIUM_INDEX_KLINES,
}


@dataclass(frozen=True)
class BinanceObject:
    dataset: BinanceDataset
    symbol: str
    day: date
    interval: str | None = None

    @property
    def filename(self) -> str:
        if self.dataset in KLINE_DATASETS:
            if self.interval is None:
                raise ValueError(f"{self.dataset.value} requires an interval")
            return f"{self.symbol}-{self.interval}-{self.day.isoformat()}.zip"
        return f"{self.symbol}-{self.dataset.value}-{self.day.isoformat()}.zip"

    @property
    def path(self) -> str:
        if self.dataset in KLINE_DATASETS:
            return (
                f"data/futures/um/daily/{self.dataset.value}/"
                f"{self.symbol}/{self.interval}/{self.filename}"
            )
        return f"data/futures/um/daily/{self.dataset.value}/{self.symbol}/{self.filename}"

    @property
    def url(self) -> str:
        return f"https://data.binance.vision/{self.path}"


def daily_object(
    dataset: BinanceDataset,
    symbol: str,
    day: date,
    interval: str | None = None,
) -> BinanceObject:
    normalized_symbol = symbol.upper()
    return BinanceObject(dataset=dataset, symbol=normalized_symbol, day=day, interval=interval)
