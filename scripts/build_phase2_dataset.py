from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import UTC, date, datetime
from pathlib import Path

from marketimmune.ingest.binance_downloader import DownloadResult, download_file, file_sha256
from marketimmune.ingest.binance_parsers import parse_zip_file
from marketimmune.ingest.binance_public import KLINE_DATASETS, BinanceDataset, daily_object
from marketimmune.ingest.coverage import (
    CoverageReport,
    CoverageRequest,
    build_coverage_report,
    iter_days,
)
from marketimmune.lake.manifest import build_manifest, write_manifest
from marketimmune.lake.parquet_io import write_events
from marketimmune.schemas.manifests import DatasetSplit


def dataset_from_arg(value: str) -> BinanceDataset:
    return BinanceDataset(value)


def parsed_path(root: Path, dataset: BinanceDataset, symbol: str, interval: str, day: date) -> Path:
    if dataset not in KLINE_DATASETS:
        return (
            root
            / "binance_usdm"
            / dataset.value
            / symbol.upper()
            / f"{symbol.upper()}-{dataset.value}-{day.isoformat()}.parquet"
        )
    return (
        root
        / "binance_usdm"
        / dataset.value
        / symbol.upper()
        / interval
        / f"{symbol.upper()}-{dataset.value}-{interval}-{day.isoformat()}.parquet"
    )


def build_dataset(
    *,
    symbol: str,
    datasets: list[BinanceDataset],
    start: date,
    end: date,
    interval: str,
    raw_root: Path,
    lake_root: Path,
    report_root: Path,
) -> dict[str, object]:
    report_root.mkdir(parents=True, exist_ok=True)
    downloads: list[DownloadResult] = []
    parsed_files: list[Path] = []
    rows_by_path: dict[Path, int] = {}
    raw_coverage: list[CoverageReport] = []
    parsed_coverage: list[dict[str, object]] = []

    for dataset in datasets:
        for day in iter_days(start, end):
            obj = daily_object(dataset, symbol, day, interval)
            raw_path = raw_root / obj.path
            if not raw_path.exists():
                downloads.append(download_file(obj.url, raw_path))
            else:
                downloads.append(
                    DownloadResult(
                        url=obj.url,
                        path=raw_path,
                        sha256=file_sha256(raw_path),
                        bytes=raw_path.stat().st_size,
                    )
                )

            events = parse_zip_file(raw_path, dataset=dataset, symbol=symbol, interval=interval)
            out_path = parsed_path(lake_root, dataset, symbol, interval, day)
            write_events(out_path, events)
            parsed_files.append(out_path)
            rows_by_path[out_path] = len(events)

        raw_coverage.append(
            build_coverage_report(
                CoverageRequest(
                    root=raw_root,
                    symbol=symbol,
                    dataset=dataset,
                    start=start,
                    end=end,
                    interval=interval,
                )
            )
        )
        expected_days = len(iter_days(start, end))
        present_parquet = sum(
            1
            for day in iter_days(start, end)
            if parsed_path(lake_root, dataset, symbol, interval, day).exists()
        )
        parsed_coverage.append(
            {
                "symbol": symbol.upper(),
                "dataset": dataset.value,
                "expected_files": expected_days,
                "present_files": present_parquet,
                "coverage_ratio": present_parquet / expected_days,
                "passes_100_percent": present_parquet == expected_days,
            }
        )

    manifest = build_manifest(
        dataset_id=f"phase2-{symbol.upper()}-{start.isoformat()}-{end.isoformat()}",
        split=DatasetSplit.CANONICAL,
        symbol=symbol,
        started_at=datetime.combine(start, datetime.min.time(), tzinfo=UTC),
        ended_at=datetime.combine(end, datetime.max.time(), tzinfo=UTC),
        files=parsed_files,
        root=lake_root,
        rows_by_path=rows_by_path,
    )
    manifest_path = report_root / "phase2_manifest.json"
    write_manifest(manifest_path, manifest)

    raw_report_path = report_root / "phase2_raw_coverage.json"
    raw_report_path.write_text(
        json.dumps([report.model_dump(mode="json") for report in raw_coverage], indent=2),
        encoding="utf-8",
    )
    parsed_report_path = report_root / "phase2_parsed_coverage.json"
    parsed_report_path.write_text(json.dumps(parsed_coverage, indent=2), encoding="utf-8")

    summary = {
        "symbol": symbol.upper(),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "days": len(iter_days(start, end)),
        "datasets": [dataset.value for dataset in datasets],
        "raw_files": len(downloads),
        "parsed_files": len(parsed_files),
        "total_rows": sum(rows_by_path.values()),
        "raw_coverage_100_percent": all(report.passes_100_percent for report in raw_coverage),
        "parsed_coverage_100_percent": all(
            bool(report["passes_100_percent"]) for report in parsed_coverage
        ),
        "manifest_path": str(manifest_path),
        "manifest_content_hash": manifest.content_hash,
        "downloads": [asdict(download) for download in downloads],
    }
    summary_path = report_root / "phase2_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a phase-2 Binance fixture-free dataset.")
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--interval", default="1m")
    parser.add_argument("--dataset", action="append")
    parser.add_argument("--raw-root", default="data/raw/binance")
    parser.add_argument("--lake-root", default="data/lake")
    parser.add_argument("--report-root", default="reports/phase2")
    args = parser.parse_args()

    datasets = (
        [dataset_from_arg(value) for value in args.dataset]
        if args.dataset
        else [
            BinanceDataset.AGG_TRADES,
            BinanceDataset.TRADES,
            BinanceDataset.BOOK_DEPTH,
            BinanceDataset.KLINES,
            BinanceDataset.MARK_PRICE_KLINES,
            BinanceDataset.INDEX_PRICE_KLINES,
        ]
    )

    summary = build_dataset(
        symbol=args.symbol,
        datasets=datasets,
        start=date.fromisoformat(args.start_date),
        end=date.fromisoformat(args.end_date),
        interval=args.interval,
        raw_root=Path(args.raw_root),
        lake_root=Path(args.lake_root),
        report_root=Path(args.report_root),
    )
    print(json.dumps(summary, indent=2, default=str))
    if not summary["raw_coverage_100_percent"] or not summary["parsed_coverage_100_percent"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
