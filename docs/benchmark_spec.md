# Benchmark Spec

V1 combines real Binance USD-M Futures public market data with synthetic agent events.
Every task must define inputs, labels, metrics, and output schema.

## Tasks

| Task | Input | Label | Primary Metrics | Output |
| --- | --- | --- | --- | --- |
| Event detection | Event sequence | Unsafe event flag | PR-AUC, F1, precision@k | event_id, score |
| Session classification | Session events | Unsafe session family | macro F1, PR-AUC | session_id, class, score |
| Early warning | Rolling prefix | Future harm within horizon | lead time, recall@horizon | timestamp, warning_score |
| Action selection | Features and model scores | should_block | false blocks per 100k, utility | action, reason_codes |
| Harm estimation | Incident replay pairs | harm delta | MAE, rank correlation | incident_id, harm_score |
| OOD detection | Held-out scenario family | OOD unsafe flag | PR-AUC, AUROC | scenario_id, score |

## Required Metrics

PR-AUC, AUROC, F1, precision@k, recall@k, lead time, false blocks per 100k,
policy utility, latency p50, latency p95, replay speed, run hash stability,
coverage ratio, missing file count, schema validation failures, manifest hash,
content hash, DuckDB row count, parser error count, and scenario leakage count.
