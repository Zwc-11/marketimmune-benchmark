# Phase 4-6 Proof Report

Generated on 2026-05-12 after the expanded phase-2 100% data coverage gate passed on
`2025-12-31` through `2026-05-11`.

## Commands

```powershell
.\make.ps1 ci
.\make.ps1 phase46
```

## Quality Gate

| Check | Result |
| --- | --- |
| Ruff | Pass |
| Mypy | Pass: 0 issues in 38 source files |
| Tests | Pass: 109 tests |
| Code coverage | Pass: 100% line and branch coverage |
| Coverage gate | `fail_under = 100` |

## Phase 4: Deterministic Replay

| Metric | Roadmap Minimum | Actual | Status |
| --- | ---: | ---: | --- |
| Events processed | Full active phase-2 kline window + synthetic agent events | 190,100 | Pass |
| Replay duration | 1 min | 11,404,740 seconds | Pass |
| Replay speed | 1x | 39,818,753x offline | Pass |
| Same seed same run hash | Yes | Yes | Pass |
| Order book invariant tests | Required | Present | Pass |
| Matching engine tests | Required | Present | Pass |
| p95 event latency | < 20 ms | 0.0018 ms | Pass |
| Replay report generated | Yes | `reports/phase4/replay_report.json` | Pass |
| Best bid below ask | Required | true | Pass |
| No negative quantity | Required | true | Pass |
| Unique order IDs | Required | true | Pass |

## Phase 5: Agent Simulator And Labels

| Metric | Roadmap Minimum | Actual | Status |
| --- | ---: | ---: | --- |
| Agent families implemented | 6 | 6 | Pass |
| Scenario configs | 10 | 12 | Pass |
| Deterministic generation | Yes | Yes | Pass |
| Event labels | Required | Present | Pass |
| Session labels | Required | Present | Pass |
| Scenario manifests | Required | Present | Pass |

Implemented families:

- `passive_market_maker`
- `twap_execution`
- `inventory_rebalancer`
- `spoofing_layering`
- `quote_stuffing`
- `momentum_ignition`

## Phase 6: Features And RuleEngine

| Metric | Roadmap Minimum | Actual | Status |
| --- | ---: | ---: | --- |
| Features implemented | 30 | 72 | Pass |
| Rolling windows | 3 | 3 | Pass |
| Feature latency p95 | < 20 ms | 0.3465 ms | Pass |
| Rule families | 5 | 5 | Pass |
| No-lookahead tests | Yes | Yes | Pass |
| Rule baseline report | Yes | `reports/phase6/rule_baseline_report.json` | Pass |
| PR-AUC | Report honestly | 0.9462 on synthetic scenarios | Pass |

## Important Boundary

Phases 4-6 are not the temporal ML model phases. They provide the replay, labels, features, and RuleEngine baseline that
the later ML benchmark/model phases need. The project should not claim that Order-MTPP, OrderS2P2Style, or TGNCoord are
complete until phases 7-10 are implemented and evaluated.
