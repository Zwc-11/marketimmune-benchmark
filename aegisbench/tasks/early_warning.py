from __future__ import annotations

from aegisbench.datasets.builder import BenchmarkExample


class EarlyWarningTask:
    name = "early_warning"

    def evaluate(self, examples: list[BenchmarkExample], scores: list[float]) -> dict[str, float]:
        warnings: list[float] = []
        by_session: dict[str, list[tuple[BenchmarkExample, float]]] = {}
        for example, score in zip(examples, scores, strict=True):
            by_session.setdefault(example.scenario_id, []).append((example, score))
        for rows in by_session.values():
            unsafe_rows = [example for example, _ in rows if example.unsafe]
            if not unsafe_rows:
                continue
            impact_time = unsafe_rows[-1].timestamp_ms
            warning_times = [
                example.timestamp_ms
                for example, score in rows
                if example.unsafe and score >= 0.5 and example.timestamp_ms <= impact_time
            ]
            if warning_times:
                warnings.append(max(impact_time - min(warning_times), 0.0))
        return {
            "mean_lead_time_ms": sum(warnings) / max(len(warnings), 1),
            "sessions_warned": float(len(warnings)),
        }
