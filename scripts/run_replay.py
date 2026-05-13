from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

from marketimmune.lake.parquet_io import read_events
from marketimmune.replay.replay_runner import ReplayRunner
from marketimmune.scenarios.config import ScenarioConfig
from marketimmune.scenarios.generator import generate_scenario
from marketimmune.schemas.events import BookTickerEvent, CanonicalEvent


def file_date(path: Path) -> date:
    match = re.search(r"(\d{4}-\d{2}-\d{2})", path.name)
    if match is None:
        raise ValueError(f"could not parse date from {path}")
    return date.fromisoformat(match.group(1))


def phase2_window(summary_path: Path) -> tuple[date, date] | None:
    if not summary_path.exists():
        return None
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    return date.fromisoformat(summary["start"]), date.fromisoformat(summary["end"])


def load_market_events(
    lake_root: Path,
    dataset: str,
    limit: int | None,
    window: tuple[date, date] | None,
) -> list[CanonicalEvent]:
    if dataset == "klines":
        root = lake_root / "binance_usdm" / "klines" / "BTCUSDT" / "1m"
    elif dataset == "bookTicker":
        root = lake_root / "binance_usdm" / "bookTicker" / "BTCUSDT"
    else:
        raise ValueError("dataset must be one of: klines, bookTicker")

    candidates = sorted(root.glob("*.parquet"))
    if window is not None:
        start, end = window
        candidates = [candidate for candidate in candidates if start <= file_date(candidate) <= end]
    if not candidates:
        raise FileNotFoundError("phase-2 klines Parquet files are required before replay")
    events: list[CanonicalEvent] = []
    for candidate in candidates:
        events.extend(read_events(candidate))
    return events[:limit] if limit is not None else events


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic replay smoke report.")
    parser.add_argument("--lake-root", default="data/lake")
    parser.add_argument("--phase2-summary", default="reports/phase2/phase2_summary.json")
    parser.add_argument("--output", default="reports/phase4/replay_report.json")
    parser.add_argument("--market-limit", type=int, default=0, help="0 means replay all klines")
    parser.add_argument(
        "--market-dataset",
        default="klines",
        choices=["klines", "bookTicker"],
        help="Market stream used to drive the shadow book. bookTicker is real LOB top-of-book.",
    )
    parser.add_argument(
        "--depth-compare-dataset",
        default="none",
        choices=["none", "bookTicker"],
        help="Real depth snapshots used for shadow-vs-real comparison.",
    )
    args = parser.parse_args()

    market_limit = None if args.market_limit == 0 else args.market_limit
    market_events = load_market_events(
        Path(args.lake_root),
        args.market_dataset,
        market_limit,
        phase2_window(Path(args.phase2_summary)),
    )
    depth_events: list[BookTickerEvent] | None = None
    if args.depth_compare_dataset == "bookTicker":
        depth_candidates = load_market_events(
            Path(args.lake_root),
            "bookTicker",
            market_limit,
            phase2_window(Path(args.phase2_summary)),
        )
        depth_events = [event for event in depth_candidates if isinstance(event, BookTickerEvent)]
    first = market_events[0]
    config = ScenarioConfig(
        scenario_id="phase4-smoke-spoofing",
        family="spoofing_layering",
        seed=31,
        start=first.timestamp,
        mid_price=getattr(first, "close_price", 65000.0),
        event_count=20,
        unsafe=True,
    )
    scenario = generate_scenario(config)
    report = ReplayRunner().run(
        scenario_id=config.scenario_id,
        market_events=market_events,
        agent_events=scenario.events,
        real_depth_events=depth_events,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    print(report.model_dump_json(indent=2))
    return 0 if report.best_bid_below_ask and report.unique_order_ids else 1


if __name__ == "__main__":
    raise SystemExit(main())
