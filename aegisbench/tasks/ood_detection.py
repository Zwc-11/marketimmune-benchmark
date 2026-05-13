from __future__ import annotations

from aegisbench.datasets.builder import BenchmarkExample
from aegisbench.metrics.classification import auroc, pr_auc


class OODDetectionTask:
    name = "ood_detection"

    def evaluate(self, examples: list[BenchmarkExample], scores: list[float]) -> dict[str, float]:
        ood_families = {
            "momentum_ignition",
            "latency_edge",
            "stop_run_sweep",
            "volatility_feedback",
        }
        labels = [example.family in ood_families for example in examples]
        return {"pr_auc": pr_auc(scores, labels), "auroc": auroc(scores, labels)}
