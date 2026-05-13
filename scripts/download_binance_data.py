from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from marketimmune.ingest.binance_downloader import download_file
from marketimmune.ingest.binance_public import BinanceDataset, daily_object


def main() -> int:
    parser = argparse.ArgumentParser(description="Download one Binance USD-M Futures public file.")
    parser.add_argument("--dataset", choices=[item.value for item in BinanceDataset], required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--root", default="data/raw/binance")
    parser.add_argument("--interval", default=None)
    args = parser.parse_args()

    obj = daily_object(
        BinanceDataset(args.dataset),
        args.symbol,
        date.fromisoformat(args.date),
        args.interval,
    )
    destination = Path(args.root) / obj.path
    result = download_file(obj.url, destination)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
