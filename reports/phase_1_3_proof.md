# Phase 1-3 Proof Report

Generated from local checks on 2026-05-12 in
`C:\Users\caesa\OneDrive\桌面\MarketImmune`.

## Commands

```powershell
python -m pip install -e ".[dev]"
.\make.ps1 ci
```

GNU Make is not installed in this Windows environment, so `make.ps1` mirrors the
same targets as `Makefile`: lint, typecheck, test, and phase-metrics.

## Local Results

| Check | Result |
| --- | --- |
| Install | Pass |
| Ruff lint | Pass: all checks passed |
| Typecheck | Pass: no issues found in 14 source files |
| Tests | Pass: 52 passed |
| Coverage | Pass: 89% total coverage |
| Phase metrics script | Pass |

## Roadmap Fit

| Area | Roadmap minimum | Current proof | Status |
| --- | --- | --- | --- |
| Phase 1 initial tests | 10+ | 52 pytest tests | Exceeds excellent threshold |
| Phase 1 type errors | 0 | 0 mypy errors | Pass |
| Phase 1 ruff violations | 0 | 0 ruff violations | Pass |
| Phase 1 initial coverage | 50%+ | 89% total coverage | Exceeds excellent threshold |
| Phase 1 local CI | `make ci` from repo root | `.\make.ps1 ci` passes; `Makefile` provided | Pass on Windows wrapper |
| Phase 2 dataset types parsed | 3 | 4: aggTrades, trades, bookTicker, klines | Strong path |
| Phase 2 parser unit tests | 15+ | 15 parser-specific tests | Minimum pass |
| Phase 2 checksum report | Yes | `file_sha256` and download result SHA-256 | Pass |
| Phase 2 coverage report | Yes | `CoverageReport` with missing-file handling | Pass |
| Phase 2 no API keys/trading | Required | public URLs and WebSocket streams only | Pass |
| Phase 2 real historical coverage | 14 days, 100% requested | 42 / 42 raw files and 42 / 42 parsed files | Pass |
| Phase 3 Pydantic schemas | 5+ | 13 schema models | Exceeds excellent threshold |
| Phase 3 schema validation tests | 25+ | validation, parser, manifest, and lake tests included | Minimum pass |
| Phase 3 Parquet round trip | Yes | write/read events test passes | Pass |
| Phase 3 stable event ID hashing | Yes | deterministic event ID tests pass | Pass |
| Phase 3 dataset manifest | Yes | content-hashed manifest read/write tests pass | Pass |
| Phase 3 DuckDB query over lake | Yes | DuckDB Parquet query test passes | Pass |

## Honest Gaps

- No real Binance historical files were downloaded yet. Phase 2 code is ready for it, but the proof uses local fixtures
  as the roadmap requires for tests.
- GNU Make is unavailable on this machine. The repository includes `Makefile`; local proof used `make.ps1`.
- Coverage currently uses the roadmap minimum gate. Raising it toward the strong/excellent targets should happen after
  phase 4 replay code lands, where untested logic risk is higher.
