from __future__ import annotations

from aegisbench.datasets.builder import BenchmarkExample
from aegisbench.metrics.classification import auroc, f1_at_threshold, pr_auc, precision_at_k


class EventDetectionTask:
    name = "event_detection"

    def evaluate(self, examples: list[BenchmarkExample], scores: list[float]) -> dict[str, float]:
        labels = [example.unsafe for example in examples]
        return {
            "pr_auc": pr_auc(scores, labels),
            "auroc": auroc(scores, labels),
            "f1": f1_at_threshold(scores, labels),
            "precision_at_10": precision_at_k(scores, labels, min(10, len(scores))),
        }
