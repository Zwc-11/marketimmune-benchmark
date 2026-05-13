from __future__ import annotations


class MarkTokenizer:
    def __init__(self) -> None:
        self.vocab: dict[str, int] = {"<pad>": 0}

    def fit(self, marks: list[str]) -> MarkTokenizer:
        for mark in sorted(set(marks)):
            self.vocab.setdefault(mark, len(self.vocab))
        return self

    def encode(self, marks: list[str]) -> list[int]:
        return [self.vocab[mark] for mark in marks]
