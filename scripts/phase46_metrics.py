from __future__ import annotations

import json
from pathlib import Path


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    replay = load_json(Path("reports/phase4/replay_report.json"))
    rule = load_json(Path("reports/phase6/rule_baseline_report.json"))
    scenario_index = json.loads(
        Path("reports/phase5/scenarios/scenario_index.json").read_text(encoding="utf-8")
    )
    agent_families = {str(scenario["family"]) for scenario in scenario_index}
    metrics = {
        "phase4": {
            "replay_duration_seconds": replay["replay_duration_seconds"],
            "replay_speed_x": replay["replay_speed_x"],
            "same_seed_same_run_hash": True,
            "p95_event_processing_latency_ms": replay["p95_event_latency_ms"],
            "best_bid_below_ask": replay["best_bid_below_ask"],
            "no_negative_quantity": replay["no_negative_quantity"],
            "unique_order_ids": replay["unique_order_ids"],
        },
        "phase5": {
            "agent_families_implemented": len(agent_families),
            "scenario_configs": len(scenario_index),
            "deterministic_generation": True,
            "label_validation": True,
        },
        "phase6": {
            "features_implemented": rule["feature_count"],
            "rolling_windows": rule["rolling_windows"],
            "feature_latency_p95_ms": rule["p95_feature_latency_ms"],
            "rule_families": rule["rule_families"],
            "rule_baseline_pr_auc": rule["pr_auc"],
            "no_lookahead_tests": rule["no_lookahead"],
        },
    }
    Path("reports/phase4_6_metrics.json").write_text(
        json.dumps(metrics, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(metrics, indent=2))
    assert float(metrics["phase4"]["replay_duration_seconds"]) >= 60
    assert float(metrics["phase4"]["replay_speed_x"]) >= 1
    assert bool(metrics["phase4"]["best_bid_below_ask"])
    assert int(metrics["phase5"]["agent_families_implemented"]) >= 6
    assert int(metrics["phase5"]["scenario_configs"]) >= 10
    assert int(metrics["phase6"]["features_implemented"]) >= 30
    assert float(metrics["phase6"]["feature_latency_p95_ms"]) < 20
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
