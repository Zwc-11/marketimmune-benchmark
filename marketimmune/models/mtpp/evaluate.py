from __future__ import annotations

from aegisbench.metrics.classification import auroc, f1_at_threshold, pr_auc
from marketimmune.models.mtpp.dataset import SequenceExample


def flatten_labels(sequences: list[SequenceExample]) -> list[bool]:
    labels: list[bool] = []
    for sequence in sequences:
        labels.extend(sequence.labels)
    return labels


def lead_time_ms(
    sequences: list[SequenceExample],
    scores: list[float],
    threshold: float = 0.5,
) -> float:
    offset = 0
    leads: list[float] = []
    for sequence in sequences:
        sequence_scores = scores[offset : offset + len(sequence.labels)]
        offset += len(sequence.labels)
        if not any(sequence.labels):
            continue
        impact = sequence.times_ms[-1]
        warning_times = [
            time
            for time, score in zip(sequence.times_ms, sequence_scores, strict=True)
            if score >= threshold
        ]
        if warning_times:
            leads.append(max(impact - min(warning_times), 0.0))
    return sum(leads) / max(len(leads), 1)


def evaluate_scores(sequences: list[SequenceExample], scores: list[float]) -> dict[str, float]:
    labels = flatten_labels(sequences)
    return {
        "pr_auc": pr_auc(scores, labels),
        "auroc": auroc(scores, labels),
        "f1": f1_at_threshold(scores, labels),
        "lead_time_ms": lead_time_ms(sequences, scores),
    }
