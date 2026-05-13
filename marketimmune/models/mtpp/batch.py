from __future__ import annotations

from dataclasses import dataclass

from marketimmune.models.mtpp.dataset import SequenceExample
from marketimmune.models.mtpp.tokenizer import MarkTokenizer


@dataclass(frozen=True)
class SequenceBatch:
    marks: list[list[int]]
    deltas_ms: list[list[float]]
    labels: list[list[bool]]
    mask: list[list[bool]]


def make_batch(sequences: list[SequenceExample], tokenizer: MarkTokenizer) -> SequenceBatch:
    max_len = max((len(sequence.marks) for sequence in sequences), default=0)
    marks: list[list[int]] = []
    deltas: list[list[float]] = []
    labels: list[list[bool]] = []
    mask: list[list[bool]] = []
    for sequence in sequences:
        encoded = tokenizer.encode(sequence.marks)
        sequence_deltas = [
            0.0,
            *[
                sequence.times_ms[index] - sequence.times_ms[index - 1]
                for index in range(1, len(sequence.times_ms))
            ],
        ]
        padding = max_len - len(encoded)
        marks.append(encoded + [0] * padding)
        deltas.append(sequence_deltas + [0.0] * padding)
        labels.append(sequence.labels + [False] * padding)
        mask.append([True] * len(encoded) + [False] * padding)
    return SequenceBatch(marks=marks, deltas_ms=deltas, labels=labels, mask=mask)
