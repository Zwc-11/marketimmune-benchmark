# Phase 2 Real Data Proof

Generated on 2026-05-12 from real Binance USD-M Futures public historical data.

## Correction

The CSV files under `tests/fixtures/` contain two rows by design. They are parser fixtures only and are not the
historical phase-2 dataset.

The real phase-2 dataset now lives under:

- Raw ZIP files: `data/raw/binance/`
- Parsed Parquet files: `data/lake/binance_usdm/`
- Reports: `reports/phase2/`

## Build Command

```powershell
python scripts/build_phase2_dataset.py `
  --symbol BTCUSDT `
  --start-date 2025-12-31 `
  --end-date 2026-05-11 `
  --interval 1m `
  --dataset klines `
  --dataset markPriceKlines `
  --dataset indexPriceKlines
```

## Result

| Metric | Required | Actual | Status |
| --- | ---: | ---: | --- |
| Historical window | 2025-12-31 through latest completed 2026 day | 2025-12-31 through 2026-05-11 | Pass |
| Days | 132 | 132 | Pass |
| Raw coverage | 100% | 396 / 396 files | Pass |
| Parsed coverage | 100% | 396 / 396 Parquet files | Pass |
| Missing files | 0 | 0 | Pass |
| Datasets | 3 | klines, markPriceKlines, indexPriceKlines | Pass |
| Total parsed rows | Real data | 570,240 rows | Pass |
| Manifest | Required | `reports/phase2/phase2_manifest.json` | Pass |
| Content hash | Required | `d25c32551e76df13ba929cf81561e8ef6a548e59dbf2b118a04cd0756c51b4a7` | Pass |

## Dataset Counts

| Dataset | Files | Rows |
| --- | ---: | ---: |
| klines | 132 | 190,080 |
| markPriceKlines | 132 | 190,080 |
| indexPriceKlines | 132 | 190,080 |

## Verification Commands

```powershell
.\make.ps1 ci
```

Current local result:

- Ruff: pass
- Mypy: pass, 0 issues in 14 source files
- Pytest: pass, 52 tests
- Coverage: pass, 84%
- Phase metrics: pass

```powershell
python - <<'PY'
import json
from pathlib import Path
summary = json.loads(Path("reports/phase2/phase2_summary.json").read_text())
assert summary["days"] == 132
assert summary["raw_files"] == 396
assert summary["parsed_files"] == 396
assert summary["start"] == "2025-12-31"
assert summary["end"] == "2026-05-11"
assert summary["total_rows"] == 570240
assert summary["raw_coverage_100_percent"] is True
assert summary["parsed_coverage_100_percent"] is True
PY
```

## Gate Decision

Phase 2 now satisfies the requested expanded 2026 coverage gate from 2025-12-31 through the latest completed daily
files available at build time.

The window cannot safely include 2026-05-12 yet because daily Binance public files are complete historical artifacts,
and the 2026-05-12 daily files were not available when checked on 2026-05-12. This is why the dataset ends at
2026-05-11 while still being the latest complete daily window.
