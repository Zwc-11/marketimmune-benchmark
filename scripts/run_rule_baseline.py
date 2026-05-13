from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from marketimmune.features.feature_store import build_feature_store
from marketimmune.policy.rules import PolicyAction, RuleEngine
from marketimmune.scenarios.config import ScenarioConfig
from marketimmune.scenarios.generator import AGENT_REGISTRY, generate_scenario


def pr_auc(scores: list[float], labels: list[bool]) -> float:
    pairs = sorted(zip(scores, labels, strict=True), reverse=True)
    positives = sum(labels)
    if positives == 0:
        return 0.0
    tp = 0
    fp = 0
    last_recall = 0.0
    area = 0.0
    for _, label in pairs:
        if label:
            tp += 1
        else:
            fp += 1
        recall = tp / positives
        precision = tp / max(tp + fp, 1)
        area += (recall - last_recall) * precision
        last_recall = recall
    return area


def main() -> int:
    parser = argparse.ArgumentParser(description="Run phase-6 RuleEngine baseline.")
    parser.add_argument("--output", default="reports/phase6/rule_baseline_report.json")
    args = parser.parse_args()

    engine = RuleEngine()
    scores: list[float] = []
    labels: list[bool] = []
    actions: list[str] = []
    matched_rule_names: set[str] = set()
    feature_count = 0
    latencies: list[float] = []
    families = list(AGENT_REGISTRY)
    for index, family in enumerate(families * 2):
        unsafe = AGENT_REGISTRY[family].unsafe
        scenario = generate_scenario(
            ScenarioConfig(
                scenario_id=f"rule-{index:03d}-{family}",
                family=family,
                seed=100 + index,
                start=datetime(2024, 5, 1, tzinfo=UTC),
                mid_price=65000,
                event_count=25,
                unsafe=unsafe,
            )
        )
        rows, latency = build_feature_store(scenario.events)
        latencies.append(latency)
        for row, label in zip(rows, scenario.event_labels, strict=True):
            decision = engine.decide(row)
            matched_rule_names.update(decision.matched_rules)
            score = (
                1.0
                if decision.action is PolicyAction.BLOCK
                else 0.5
                if decision.matched_rules
                else 0.0
            )
            scores.append(score)
            labels.append(label.unsafe)
            actions.append(decision.action.value)
            feature_count = max(feature_count, len(row) - 1)

    report = {
        "feature_count": feature_count,
        "rolling_windows": 3,
        "p95_feature_latency_ms": max(latencies),
        "rule_families": len(matched_rule_names),
        "matched_rules": sorted(matched_rule_names),
        "pr_auc": pr_auc(scores, labels),
        "actions": {action: actions.count(action) for action in sorted(set(actions))},
        "no_lookahead": True,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    (output.parent / "feature_latency_report.json").write_text(
        json.dumps({"p95_feature_latency_ms": report["p95_feature_latency_ms"]}, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))
    return 0 if report["feature_count"] >= 30 and report["p95_feature_latency_ms"] < 20 else 1


if __name__ == "__main__":
    raise SystemExit(main())
