# MarketImmune Core V1

MarketImmune is a research-grade benchmark and safety framework for identifying harmful or
unsafe autonomous trading-agent behavior in crypto exchange microstructure.

The project combines:

- Real Binance USD-M Futures public market background data.
- Synthetic, labeled agent order-lifecycle events for controlled evaluation.
- Deterministic replay and scenario generation.
- Feature extraction and rule-based safety baselines.
- A benchmark suite and temporal-model baselines for early-warning and harm estimation tasks.

It does not perform live trading, identify private users/accounts, or claim alpha/prediction
edge for deployment.

## What We Accomplished

This repository now contains implemented and validated work through phases 1-9.

- Phase 1-3 foundation: package quality gates, schemas, event IDs, Parquet/lake/manifests, and CI.
- Phase 4 replay engine: deterministic, invariant-checked replay with generated replay reports.
- Phase 5 scenario and labeling system: benign and risky agent families, deterministic synthetic scenarios,
  and label/manifests.
- Phase 6 feature and policy baseline: multi-window feature store and RuleEngine baseline reports.
- Phase 7 AegisBench v0: train/validation/test splits, task metrics, JSON/Markdown reports, and leaderboard CSV.
- Phase 8 Order-MTPP baseline: variable-length temporal model pipeline with benchmarked latency and quality.
- Phase 9 Order-S2P2 baseline: neural Hawkes (CT-LSTM style) implementation with OOD metrics and comparison artifacts.

## Current Evidence And Reports

Project proof and metrics are included in the repository:

- `reports/phase_1_3_proof.md`
- `reports/phase4_6_proof.md`
- `reports/phase7_9_proof.md`
- `reports/phase4_6_metrics.json`
- `reports/phase7_9_metrics.json`
- Phase outputs under `reports/phase4` through `reports/phase9`

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

Additional phase runners:

```powershell
.\make.ps1 phase46
.\make.ps1 phase79
```

## Scope Rules

- No API keys are required.
- No real orders are sent.
- Tests use local fixtures and do not require internet.
- Synthetic agent behavior is labeled as synthetic.
- Benchmark and model metrics must be generated from actual outputs, not entered manually.
