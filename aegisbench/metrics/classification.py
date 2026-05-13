from __future__ import annotations


def pr_auc(scores: list[float], labels: list[bool]) -> float:
    if len(scores) != len(labels):
        raise ValueError("scores and labels must have same length")
    positives = sum(labels)
    if positives == 0:
        return 0.0
    pairs = sorted(zip(scores, labels, strict=True), reverse=True)
    tp = 0
    fp = 0
    previous_recall = 0.0
    area = 0.0
    for _, label in pairs:
        if label:
            tp += 1
        else:
            fp += 1
        recall = tp / positives
        precision = tp / max(tp + fp, 1)
        area += (recall - previous_recall) * precision
        previous_recall = recall
    return area


def auroc(scores: list[float], labels: list[bool]) -> float:
    if len(scores) != len(labels):
        raise ValueError("scores and labels must have same length")
    positives = sum(labels)
    negatives = len(labels) - positives
    if positives == 0 or negatives == 0:
        return 0.0
    pairs = sorted(zip(scores, labels, strict=True), key=lambda item: item[0])
    rank_sum = 0.0
    index = 0
    while index < len(pairs):
        next_index = index + 1
        while next_index < len(pairs) and pairs[next_index][0] == pairs[index][0]:
            next_index += 1
        average_rank = (index + 1 + next_index) / 2
        rank_sum += sum(label for _, label in pairs[index:next_index]) * average_rank
        index = next_index
    return (rank_sum - positives * (positives + 1) / 2) / (positives * negatives)


def f1_at_threshold(scores: list[float], labels: list[bool], threshold: float = 0.5) -> float:
    if len(scores) != len(labels):
        raise ValueError("scores and labels must have same length")
    predictions = [score >= threshold for score in scores]
    tp = sum(pred and label for pred, label in zip(predictions, labels, strict=True))
    fp = sum(pred and not label for pred, label in zip(predictions, labels, strict=True))
    fn = sum((not pred) and label for pred, label in zip(predictions, labels, strict=True))
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    return 2 * precision * recall / max(precision + recall, 1e-9)


def precision_at_k(scores: list[float], labels: list[bool], k: int) -> float:
    if k <= 0:
        raise ValueError("k must be positive")
    pairs = sorted(zip(scores, labels, strict=True), reverse=True)[:k]
    return sum(label for _, label in pairs) / max(len(pairs), 1)
