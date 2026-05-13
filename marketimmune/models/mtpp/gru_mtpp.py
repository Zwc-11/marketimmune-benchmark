"""GRU-based Marked Temporal Point Process (MTPP) model for unsafe order detection.

Architecture
------------
Each event is represented by:
  - A learnable mark embedding (event-type / family)
  - Log-transformed inter-event delta (time since last event)
  - A small numeric feature vector from the feature store

The GRU hidden state h_t summarises the history up to time t.
A linear hazard head maps h_t -> logit -> sigmoid -> P(unsafe | history).

The model is trained with binary cross-entropy over all non-padded positions.
Padding positions are excluded via the sequence mask.
"""
from __future__ import annotations

import math
from typing import Any, cast

import torch
import torch.nn as nn
import torch.optim as optim

from marketimmune.models.mtpp.dataset import SequenceExample
from marketimmune.models.mtpp.tokenizer import MarkTokenizer

# ---------------------------------------------------------------------------
# Feature helpers
# ---------------------------------------------------------------------------

_FEATURE_KEYS = [
    "w1000_agentic_burst_rate_per_second",
    "w60000_market_price_drift",
    "w1000_order_cancel_rate",
    "w5000_order_cancel_rate",
    "w60000_order_cancel_rate",
]
NUM_EXTRA_FEATURES = len(_FEATURE_KEYS)


def _extract_feature_vec(features: dict[str, float]) -> list[float]:
    return [features.get(k, 0.0) for k in _FEATURE_KEYS]


# ---------------------------------------------------------------------------
# Neural network module
# ---------------------------------------------------------------------------


class GRUMTPPNet(nn.Module):
    """GRU-MTPP hazard network.

    Parameters
    ----------
    vocab_size:
        Number of distinct event marks (including <pad>=0).
    embed_dim:
        Dimensionality of mark embeddings.
    hidden_dim:
        GRU hidden state size.
    num_layers:
        Number of stacked GRU layers.
    dropout:
        Dropout probability (applied between GRU layers when num_layers > 1).
    """

    def __init__(
        self,
        vocab_size: int,
        embed_dim: int = 32,
        hidden_dim: int = 64,
        num_layers: int = 2,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.mark_embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        # +1 for log-delta, +NUM_EXTRA_FEATURES for feature store columns
        input_dim = embed_dim + 1 + NUM_EXTRA_FEATURES
        self.gru = nn.GRU(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.hazard_head = nn.Linear(hidden_dim, 1)

    def forward(
        self,
        marks: torch.Tensor,          # (B, T) int64
        log_deltas: torch.Tensor,     # (B, T, 1) float32
        extra_feats: torch.Tensor,    # (B, T, F) float32
        mask: torch.Tensor,           # (B, T) bool  – True = real token
    ) -> torch.Tensor:                # (B, T) float32 – P(unsafe)
        mark_emb = self.mark_embedding(marks)               # (B, T, E)
        x = torch.cat([mark_emb, log_deltas, extra_feats], dim=-1)  # (B, T, E+1+F)

        # Pack to skip padding in GRU computation
        lengths = mask.sum(dim=1).clamp(min=1).cpu()
        packed = nn.utils.rnn.pack_padded_sequence(
            x, lengths, batch_first=True, enforce_sorted=False
        )
        output_packed, _ = self.gru(packed)
        output, _ = nn.utils.rnn.pad_packed_sequence(
            output_packed, batch_first=True, total_length=marks.size(1)
        )  # (B, T, H)

        logits = self.hazard_head(output).squeeze(-1)   # (B, T)
        return torch.sigmoid(logits)


# ---------------------------------------------------------------------------
# Batch collation
# ---------------------------------------------------------------------------


def _collate(
    sequences: list[SequenceExample],
    tokenizer: MarkTokenizer,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """Return (marks, log_deltas, extra_feats, mask, labels) tensors."""
    max_len = max(len(s.marks) for s in sequences)

    marks_list: list[list[int]] = []
    deltas_list: list[list[float]] = []
    feats_list: list[list[list[float]]] = []
    labels_list: list[list[float]] = []
    mask_list: list[list[bool]] = []

    for seq in sequences:
        T = len(seq.marks)
        pad = max_len - T

        encoded = tokenizer.encode(seq.marks)

        raw_deltas = [0.0] + [
            max(seq.times_ms[i] - seq.times_ms[i - 1], 0.0)
            for i in range(1, T)
        ]
        log_deltas = [math.log1p(d) for d in raw_deltas]

        feats = [_extract_feature_vec(f) for f in seq.features]

        marks_list.append(encoded + [0] * pad)
        deltas_list.append(log_deltas + [0.0] * pad)
        feats_list.append(feats + [[0.0] * NUM_EXTRA_FEATURES] * pad)
        labels_list.append([float(lbl) for lbl in seq.labels] + [0.0] * pad)
        mask_list.append([True] * T + [False] * pad)

    marks_t = torch.tensor(marks_list, dtype=torch.long)
    log_deltas_t = torch.tensor(deltas_list, dtype=torch.float32).unsqueeze(-1)
    feats_t = torch.tensor(feats_list, dtype=torch.float32)
    labels_t = torch.tensor(labels_list, dtype=torch.float32)
    mask_t = torch.tensor(mask_list, dtype=torch.bool)
    return marks_t, log_deltas_t, feats_t, mask_t, labels_t


# ---------------------------------------------------------------------------
# Public model wrapper
# ---------------------------------------------------------------------------


class GRUMTPPModel:
    """Trained GRU-MTPP model ready for inference.

    Use :func:`fit` to train from a list of :class:`SequenceExample` objects.
    """

    def __init__(self, net: GRUMTPPNet, tokenizer: MarkTokenizer) -> None:
        self._net = net
        self._tokenizer = tokenizer

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    @classmethod
    def fit(
        cls,
        sequences: list[SequenceExample],
        *,
        embed_dim: int = 32,
        hidden_dim: int = 64,
        num_layers: int = 2,
        dropout: float = 0.1,
        epochs: int = 30,
        batch_size: int = 32,
        lr: float = 3e-3,
        weight_decay: float = 1e-4,
        pos_weight: float = 5.0,
        seed: int = 42,
        device: str | None = None,
    ) -> GRUMTPPModel:
        """Train the GRU-MTPP model and return a ready-to-use instance."""
        torch.manual_seed(seed)
        dev = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))

        tokenizer = MarkTokenizer()
        all_marks = [mark for seq in sequences for mark in seq.marks]
        tokenizer.fit(all_marks)

        net = GRUMTPPNet(
            vocab_size=len(tokenizer.vocab),
            embed_dim=embed_dim,
            hidden_dim=hidden_dim,
            num_layers=num_layers,
            dropout=dropout,
        ).to(dev)

        pos_w = torch.tensor([pos_weight], device=dev)
        criterion = nn.BCEWithLogitsLoss(pos_weight=pos_w, reduction="none")

        optimizer: optim.Optimizer = optim.AdamW(
            net.parameters(), lr=lr, weight_decay=weight_decay
        )
        scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

        indices = list(range(len(sequences)))
        rng = torch.Generator()
        rng.manual_seed(seed)

        for _ in range(epochs):
            net.train()
            perm = torch.randperm(len(indices), generator=rng).tolist()
            for start in range(0, len(perm), batch_size):
                batch_seqs = [sequences[perm[i]] for i in perm[start : start + batch_size]]
                marks_t, log_deltas_t, feats_t, mask_t, labels_t = _collate(
                    batch_seqs, tokenizer
                )
                marks_t = marks_t.to(dev)
                log_deltas_t = log_deltas_t.to(dev)
                feats_t = feats_t.to(dev)
                mask_t = mask_t.to(dev)
                labels_t = labels_t.to(dev)

                mark_emb = net.mark_embedding(marks_t)
                x = torch.cat([mark_emb, log_deltas_t, feats_t], dim=-1)
                lengths = mask_t.sum(dim=1).clamp(min=1).cpu()
                packed = nn.utils.rnn.pack_padded_sequence(
                    x, lengths, batch_first=True, enforce_sorted=False
                )
                output_packed, _ = net.gru(packed)
                output, _ = nn.utils.rnn.pad_packed_sequence(
                    output_packed, batch_first=True, total_length=marks_t.size(1)
                )
                logits = net.hazard_head(output).squeeze(-1)

                loss_all = criterion(logits, labels_t)
                loss = (loss_all * mask_t.float()).sum() / mask_t.float().sum().clamp(min=1)

                optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(net.parameters(), max_norm=5.0)
                optimizer.step()

            scheduler.step()

        net.eval()
        return cls(net=net, tokenizer=tokenizer)

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def predict_sequence(self, sequence: SequenceExample) -> list[float]:
        marks_t, log_deltas_t, feats_t, mask_t, _ = _collate([sequence], self._tokenizer)
        with torch.no_grad():
            probs = self._net(marks_t, log_deltas_t, feats_t, mask_t)
        return cast(list[float], probs[0, : len(sequence.marks)].tolist())

    def predict(self, sequences: list[SequenceExample]) -> list[float]:
        scores: list[float] = []
        for sequence in sequences:
            scores.extend(self.predict_sequence(sequence))
        return scores

    def state_dict(self) -> dict[str, Any]:
        return {
            "net": self._net.state_dict(),
            "vocab": self._tokenizer.vocab,
        }

    @classmethod
    def load(cls, state: dict[str, Any], **net_kwargs: Any) -> GRUMTPPModel:
        tokenizer = MarkTokenizer()
        tokenizer.vocab = state["vocab"]
        net = GRUMTPPNet(vocab_size=len(tokenizer.vocab), **net_kwargs)
        net.load_state_dict(state["net"])
        net.eval()
        return cls(net=net, tokenizer=tokenizer)
