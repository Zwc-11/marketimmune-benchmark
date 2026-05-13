# MarketImmune Core V1

MarketImmune Core V1 is an open-source benchmark and safety layer for detecting unsafe
autonomous trading-agent behavior in crypto exchange microstructure.

V1 uses real Binance USD-M Futures public market data as market background and synthetic
agent order-lifecycle events for controlled labels. It does not perform live trading,
identify real private accounts, or claim price-prediction alpha.

## Current Status

This repository currently implements roadmap phases 1-3:

- Phase 1: professional Python package foundation, local CI commands, linting, type checks, and tests.
- Phase 2: Binance public-data URL builders, downloader primitives, local parsers, WebSocket collector skeleton,
  checksums, and coverage reports.
- Phase 3: canonical Pydantic schemas, deterministic event IDs, Parquet round trips, DuckDB-compatible lake files,
  and content-hashed dataset manifests.

## Quickstart

```powershell
python -m pip install -e ".[dev]"
.\make.ps1 ci
```

On systems with GNU Make:

```bash
make install
make ci
```

## Scope Rules

- No API keys are required.
- No real orders are sent.
- Tests use local fixtures and do not require internet.
- Synthetic agent behavior is labeled as synthetic.
- Benchmark and model metrics must be generated from actual outputs, not entered manually.
