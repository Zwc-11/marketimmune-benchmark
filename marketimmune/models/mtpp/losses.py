from __future__ import annotations


def binary_log_loss(scores: list[float], labels: list[bool], eps: float = 1e-9) -> float:
    if len(scores) != len(labels):
        raise ValueError("scores and labels must have same length")
    total = 0.0
    for score, label in zip(scores, labels, strict=True):
        clipped = min(max(score, eps), 1 - eps)
        total -= (1.0 if label else 0.0) * _log(clipped)
        total -= (0.0 if label else 1.0) * _log(1 - clipped)
    return total / max(len(scores), 1)


def _log(value: float) -> float:
    import math

    return math.log(value)
