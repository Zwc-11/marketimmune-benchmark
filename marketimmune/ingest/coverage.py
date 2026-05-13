from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from marketimmune.ingest.binance_public import BinanceDataset, daily_object


class CoverageReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    symbol: str
    dataset: str
    expected_files: int
    present_files: int
    missing_files: list[str]
    coverage_ratio: float = Field(ge=0, le=1)
    passes_100_percent: bool = False


@dataclass(frozen=True)
class CoverageRequest:
    root: Path
    symbol: str
    dataset: BinanceDataset
    start: date
    end: date
    interval: str | None = None


def iter_days(start: date, end: date) -> list[date]:
    if end < start:
        raise ValueError("end date must be >= start date")
    days: list[date] = []
    current = start
    while current <= end:
        days.append(current)
        current += timedelta(days=1)
    return days


def build_coverage_report(request: CoverageRequest) -> CoverageReport:
    missing: list[str] = []
    present = 0
    for day in iter_days(request.start, request.end):
        obj = daily_object(request.dataset, request.symbol, day, request.interval)
        candidate = request.root / obj.path
        if candidate.exists():
            present += 1
        else:
            missing.append(str(candidate))
    expected = present + len(missing)
    ratio = present / expected if expected else 1.0
    return CoverageReport(
        symbol=request.symbol.upper(),
        dataset=request.dataset.value,
        expected_files=expected,
        present_files=present,
        missing_files=missing,
        coverage_ratio=ratio,
        passes_100_percent=ratio == 1.0,
    )
