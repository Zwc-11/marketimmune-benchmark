from __future__ import annotations

from datetime import date

import pytest

from marketimmune.ingest.binance_public import BinanceDataset, daily_object
from marketimmune.ingest.coverage import CoverageRequest, build_coverage_report, iter_days


def test_iter_days_is_inclusive() -> None:
    days = iter_days(date(2024, 5, 1), date(2024, 5, 3))
    assert len(days) == 3


def test_coverage_reports_missing_files(tmp_path) -> None:  # type: ignore[no-untyped-def]
    report = build_coverage_report(
        CoverageRequest(
            tmp_path,
            "BTCUSDT",
            BinanceDataset.AGG_TRADES,
            date(2024, 5, 1),
            date(2024, 5, 2),
        )
    )
    assert report.present_files == 0
    assert report.expected_files == 2
    assert len(report.missing_files) == 2


def test_coverage_reports_present_files(tmp_path) -> None:  # type: ignore[no-untyped-def]
    obj = daily_object(BinanceDataset.AGG_TRADES, "BTCUSDT", date(2024, 5, 1))
    path = tmp_path / obj.path
    path.parent.mkdir(parents=True)
    path.write_bytes(b"fixture")
    report = build_coverage_report(
        CoverageRequest(
            tmp_path,
            "BTCUSDT",
            BinanceDataset.AGG_TRADES,
            date(2024, 5, 1),
            date(2024, 5, 2),
        )
    )
    assert report.present_files == 1
    assert report.coverage_ratio == 0.5


def test_iter_days_rejects_reversed_range() -> None:
    with pytest.raises(ValueError):
        iter_days(date(2024, 5, 2), date(2024, 5, 1))
