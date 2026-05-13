from __future__ import annotations

from typing import Any

from marketimmune.models.mtpp.dataset import SequenceExample
from marketimmune.models.mtpp.gru_mtpp import GRUMTPPModel


def train_order_mtpp(sequences: list[SequenceExample], **kwargs: Any) -> GRUMTPPModel:
    return GRUMTPPModel.fit(sequences, **kwargs)
