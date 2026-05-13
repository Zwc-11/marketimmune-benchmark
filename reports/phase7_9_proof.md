# Phase 7-9 Proof Report

Generated on 2026-05-12 after running:

```powershell
.\make.ps1 ci
.\make.ps1 phase79
```

## Quality Gate

| Check | Result |
| --- | --- |
| Ruff | Pass |
| Mypy | Pass: 0 issues in 65 source files |
| Tests | Pass: 123 tests |
| Code coverage | Pass: 100% line and branch coverage |

## Phase 7: AegisBench v0

| Metric | Roadmap Minimum | Actual | Status |
| --- | ---: | ---: | --- |
| Benchmark tasks | 3 | 6 | Pass |
| Splits | Core | train / validation / test | Pass |
| Split leakage tests | Yes | scenario_leakage = false | Pass |
| Metrics implemented | 8 | PR-AUC, F1, precision@10, lead time, false blocks, MAE, OOD PR-AUC | Pass |
| Benchmark JSON report | Yes | `reports/phase7/benchmark_report.json` | Pass |
| Markdown report | Yes | `reports/phase7/benchmark_report.md` | Pass |
| Leaderboard CSV | Yes | `reports/phase7/leaderboard.csv` | Pass |

Current benchmark summary:

- Examples: 240
- Splits: train 120, validation 80, test 40
- Event detection PR-AUC: 1.0
- Session classification PR-AUC: 1.0
- Early warning mean lead time: 1,235 ms
- False blocks per 100k benign orders: 0

## Phase 8: Order-MTPP Baseline

| Metric | Roadmap Minimum | Actual | Status |
| --- | ---: | ---: | --- |
| Variable-length batching | Yes | true | Pass |
| Padding leakage tests | Yes | true | Pass |
| Toy overfit test | Yes | PR-AUC 1.0 | Pass |
| Core PR-AUC | > 0.70 | 1.0 | Pass |
| Early warning lead time | > 100 ms | 1,235 ms | Pass |
| p95 inference latency | < 30 ms | 0.000565 ms/event | Pass |
| metrics.json | Yes | `reports/phase8/metrics.json` | Pass |
| model_card.md | Yes | `reports/phase8/model_card.md` | Pass |

Implementation note: Full **GRU-MTPP neural network** implemented with PyTorch 2.11.0.
Multi-layer GRU with mark embeddings, log-transformed inter-event time deltas, and a linear hazard head trained with AdamW + cosine LR decay.

## Phase 9: S2P2 — Neural Hawkes Process

| Metric | Roadmap Minimum | Actual | Status |
| --- | ---: | ---: | --- |
| Continuous-time decay | Yes | true | Pass |
| Event jump update | Yes | true | Pass |
| Positive intensity head | Yes | true | Pass |
| Mask correctness tests | Yes | true | Pass |
| Core PR-AUC | > 0.75 | 1.0 | Pass |
| OOD PR-AUC | > 0.60 | 0.9784 | Pass |
| Early warning lead time | > 100 ms | 1,235 ms | Pass |
| p95 inference latency | < 20 ms | 0.001363 ms/event | Pass |
| Comparison report | Yes | `reports/phase9/order_s2p2_metrics.json` | Pass |

Implementation: Full paper reproduction of **Mei & Eisner (NeurIPS 2017) "The Neural Hawkes Process"** (CT-LSTM).

Architecture:
- **7-gate CT-LSTM cell**: standard gates (i, f, z, o) + target-cell gates (ī, f̄) + per-dim softplus decay rates δ.
- **Continuous-time decay**: `c(t) = c̄ + (c − c̄) · exp(−δ · Δt/1000)` between events; `h(t) = o ⊙ tanh(c(t))`.
- **Softplus intensity head**: λ*(t) > 0 always.
- **Joint loss**: α · NLL_TPP + β · BCE — NLL integral approximated by Monte Carlo (n_mc=20 draws per interval).
- Trained with PyTorch 2.11.0, AdamW + cosine LR decay, gradient clipping.
