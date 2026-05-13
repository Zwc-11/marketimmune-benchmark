"""S2P2: Neural Hawkes Process for order-stream unsafe-event detection.

Full reproduction of the Continuous-Time LSTM (CT-LSTM) architecture introduced by:

    Mei & Eisner (2017) "The Neural Hawkes Process: A Neurally Self-Modulating
    Multivariate Point Process". NeurIPS 2017.

Architecture
------------
At each event t_i the CT-LSTM computes seven gated quantities from the current
event embedding x_i and the previous hidden state h(t_i^-):

    i      = sigmoid(W_i  · [x_i, h^-])   input gate       (for c)
    f      = sigmoid(W_f  · [x_i, h^-])   forget gate      (for c)
    z      = tanh   (W_z  · [x_i, h^-])   cell input
    o      = sigmoid(W_o  · [x_i, h^-])   output gate
    ī      = sigmoid(W_ī  · [x_i, h^-])   input gate       (for c̄)
    f̄      = sigmoid(W_f̄  · [x_i, h^-])   forget gate      (for c̄)
    δ      = softplus(W_δ · [x_i, h^-])   per-dim decay rate (always > 0)

State update:
    c_i    = f ⊙ c_{i-1}  + i  ⊙ z       post-event cell
    c̄_i    = f̄ ⊙ c_{i-1}  + ī  ⊙ z       target / resting cell

Continuous-time decay between events (t ∈ [t_i, t_{i+1})):
    c(t)   = c̄_i + (c_i − c̄_i) · exp(−δ_i · (t − t_i) / 1000)
    h(t)   = o_i ⊙ tanh(c(t))

Intensity function (always positive via softplus):
    λ*(t)  = softplus(v^T h(t) + b)

Hazard / classification head:
    p(t_i) = sigmoid(w^T h(t_i^-) + b')

Training objective
------------------
Joint loss = α · NLL_TPP + β · BCE

NLL_TPP = −Σ_i log λ*(t_i^-) + Σ_i ∫_{t_{i−1}}^{t_i} λ*(t) dt

The integral is approximated via Monte Carlo sampling (n_mc uniform draws per
inter-event interval). BCE uses per-positive oversampling for class imbalance.
"""
from __future__ import annotations

import math
from typing import Any, cast

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

from marketimmune.models.mtpp.dataset import SequenceExample
from marketimmune.models.mtpp.gru_mtpp import NUM_EXTRA_FEATURES, _extract_feature_vec
from marketimmune.models.mtpp.tokenizer import MarkTokenizer

# ---------------------------------------------------------------------------
# CT-LSTM neural network
# ---------------------------------------------------------------------------


class CTLSTMNet(nn.Module):
    """Continuous-Time LSTM as in Mei & Eisner (NeurIPS 2017).

    Parameters
    ----------
    vocab_size:  number of distinct event marks (including <pad>=0)
    embed_dim:   mark embedding dimensionality
    hidden_dim:  CT-LSTM cell / hidden dimensionality
    n_mc:        Monte-Carlo samples per interval for the NLL integral
    dropout:     dropout probability on the input projection
    """

    def __init__(
        self,
        vocab_size: int,
        embed_dim: int = 32,
        hidden_dim: int = 64,
        n_mc: int = 20,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.hidden_dim = hidden_dim
        self.n_mc = n_mc

        self.mark_embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.input_dropout = nn.Dropout(dropout)

        # Input: mark embedding + log-delta + NUM_EXTRA_FEATURES
        input_dim = embed_dim + 1 + NUM_EXTRA_FEATURES
        # 7 CT-LSTM gates packed into one linear: i, f, z, o, i_bar, f_bar, delta
        self.cell_update = nn.Linear(input_dim + hidden_dim, 7 * hidden_dim)

        # Intensity head: h(t) -> scalar, softplus ensures λ*(t) > 0
        self.intensity_head = nn.Linear(hidden_dim, 1)
        # Hazard head: h(t_i^-) -> P(unsafe)
        self.hazard_head = nn.Linear(hidden_dim, 1)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _decay(
        self,
        o: torch.Tensor,
        c: torch.Tensor,
        c_bar: torch.Tensor,
        delta: torch.Tensor,
        elapsed_ms: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Return h(t) and c(t) after decaying over *elapsed_ms* milliseconds."""
        dt = (elapsed_ms / 1000.0).unsqueeze(-1)          # (B,1) seconds
        c_t = c_bar + (c - c_bar) * torch.exp(-delta * dt)
        h_t = o * torch.tanh(c_t)
        return h_t, c_t

    def _update(
        self,
        x: torch.Tensor,
        h: torch.Tensor,
        c: torch.Tensor,
        c_bar: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """One CT-LSTM update step at a single event."""
        combined = torch.cat([x, h], dim=-1)
        raw = self.cell_update(combined)
        i_g, f_g, z_g, o_g, i_bar, f_bar, raw_delta = raw.chunk(7, dim=-1)

        i_g = torch.sigmoid(i_g)
        f_g = torch.sigmoid(f_g)
        z_g = torch.tanh(z_g)
        o_g = torch.sigmoid(o_g)
        i_bar = torch.sigmoid(i_bar)
        f_bar = torch.sigmoid(f_bar)
        delta = F.softplus(raw_delta) + 1e-6   # positive, per-dim

        c_new = f_g * c + i_g * z_g
        c_bar_new = f_bar * c + i_bar * z_g
        return o_g, c_new, c_bar_new, delta

    # ------------------------------------------------------------------
    # Forward
    # ------------------------------------------------------------------

    def forward(
        self,
        marks: torch.Tensor,        # (B, T)  int64
        log_deltas: torch.Tensor,   # (B, T)  float32 – log1p inter-event ms
        extra_feats: torch.Tensor,  # (B, T, F) float32
        elapsed_ms: torch.Tensor,   # (B, T)  float32 – raw inter-event ms
        mask: torch.Tensor,         # (B, T)  bool – True = real token
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Returns
        -------
        hazard_probs : (B, T) – P(unsafe | history up to t_i^-)
        log_lams     : (B, T) – log λ*(t_i^-)  for NLL
        mc_lams      : (B, T, n_mc) – sampled λ* values for integral
        """
        B, T = marks.shape
        H = self.hidden_dim
        dev = marks.device

        # Initial CT-LSTM state (all zeros)
        c = marks.new_zeros(B, H, dtype=torch.float32)
        c_bar = marks.new_zeros(B, H, dtype=torch.float32)
        o = marks.new_zeros(B, H, dtype=torch.float32)
        delta = torch.ones(B, H, device=dev, dtype=torch.float32)

        hazards: list[torch.Tensor] = []
        log_lams: list[torch.Tensor] = []
        mc_lams: list[torch.Tensor] = []

        for step in range(T):
            # ── 1. Decay to current event time (gives h(t_i^-)) ──────────
            h_now, c_now = self._decay(o, c, c_bar, delta, elapsed_ms[:, step])

            # ── 2. Intensity & hazard at t_i^- ───────────────────────────
            lam = F.softplus(self.intensity_head(h_now).squeeze(-1)) + 1e-8
            log_lam = torch.log(lam)
            hazard = torch.sigmoid(self.hazard_head(h_now).squeeze(-1))

            # ── 3. MC integral over [t_{i-1}, t_i] ───────────────────────
            elapsed_s = elapsed_ms[:, step] / 1000.0            # (B,) seconds
            u = torch.rand(self.n_mc, device=dev)               # (n_mc,)
            t_mc = elapsed_s.unsqueeze(-1) * u.unsqueeze(0)     # (B, n_mc)
            # Vectorised decay for all MC samples
            c_mc = (
                c_bar.unsqueeze(1)
                + (c - c_bar).unsqueeze(1)
                * torch.exp(-delta.unsqueeze(1) * t_mc.unsqueeze(-1))
            )                                                     # (B, n_mc, H)
            h_mc = o.unsqueeze(1) * torch.tanh(c_mc)            # (B, n_mc, H)
            lam_mc = F.softplus(self.intensity_head(h_mc).squeeze(-1)) + 1e-8  # (B, n_mc)

            # ── 4. CT-LSTM update at event t_i ───────────────────────────
            mark_emb = self.input_dropout(self.mark_embedding(marks[:, step]))
            x = torch.cat(
                [mark_emb, log_deltas[:, step : step + 1], extra_feats[:, step]], dim=-1
            )
            o_new, c_new_ev, c_bar_new, delta_new = self._update(x, h_now, c_now, c_bar)

            # Only update valid (non-padded) positions
            valid = mask[:, step].float().unsqueeze(-1)
            o = valid * o_new + (1.0 - valid) * o
            c = valid * c_new_ev + (1.0 - valid) * c
            c_bar = valid * c_bar_new + (1.0 - valid) * c_bar
            delta = valid * delta_new + (1.0 - valid) * delta

            hazards.append(hazard)
            log_lams.append(log_lam)
            mc_lams.append(lam_mc)

        return (
            torch.stack(hazards, dim=1),    # (B, T)
            torch.stack(log_lams, dim=1),   # (B, T)
            torch.stack(mc_lams, dim=1),    # (B, T, n_mc)
        )


# ---------------------------------------------------------------------------
# Batch collation
# ---------------------------------------------------------------------------


def _collate_s2p2(
    sequences: list[SequenceExample],
    tokenizer: MarkTokenizer,
) -> tuple[
    torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor
]:
    """Return (marks, log_deltas, extra_feats, elapsed_ms, mask, labels)."""
    max_len = max(len(s.marks) for s in sequences)

    marks_list: list[list[int]] = []
    log_deltas_list: list[list[float]] = []
    feats_list: list[list[list[float]]] = []
    elapsed_list: list[list[float]] = []
    labels_list: list[list[float]] = []
    mask_list: list[list[bool]] = []

    for seq in sequences:
        T = len(seq.marks)
        pad = max_len - T

        encoded = tokenizer.encode(seq.marks)
        raw_deltas = [0.0] + [
            max(seq.times_ms[i] - seq.times_ms[i - 1], 0.0) for i in range(1, T)
        ]
        log_deltas = [math.log1p(d) for d in raw_deltas]
        feats = [_extract_feature_vec(f) for f in seq.features]

        marks_list.append(encoded + [0] * pad)
        log_deltas_list.append(log_deltas + [0.0] * pad)
        feats_list.append(feats + [[0.0] * NUM_EXTRA_FEATURES] * pad)
        elapsed_list.append(raw_deltas + [0.0] * pad)
        labels_list.append([float(lbl) for lbl in seq.labels] + [0.0] * pad)
        mask_list.append([True] * T + [False] * pad)

    return (
        torch.tensor(marks_list, dtype=torch.long),
        torch.tensor(log_deltas_list, dtype=torch.float32),
        torch.tensor(feats_list, dtype=torch.float32),
        torch.tensor(elapsed_list, dtype=torch.float32),
        torch.tensor(mask_list, dtype=torch.bool),
        torch.tensor(labels_list, dtype=torch.float32),
    )


# ---------------------------------------------------------------------------
# Loss
# ---------------------------------------------------------------------------


def _s2p2_loss(
    hazard_probs: torch.Tensor,   # (B, T)
    log_lams: torch.Tensor,       # (B, T)
    mc_lams: torch.Tensor,        # (B, T, n_mc)
    elapsed_ms: torch.Tensor,     # (B, T)
    labels: torch.Tensor,         # (B, T)
    mask: torch.Tensor,           # (B, T) bool
    pos_weight: float,
    nll_weight: float,
) -> torch.Tensor:
    mask_f = mask.float()
    n_valid = mask_f.sum().clamp(min=1.0)

    # ── BCE hazard loss (weighted positive) ───────────────────────────────
    sample_weight = mask_f * (1.0 + (pos_weight - 1.0) * labels)
    bce = F.binary_cross_entropy(
        hazard_probs.clamp(1e-7, 1.0 - 1e-7),
        labels,
        weight=sample_weight,
        reduction="sum",
    ) / n_valid

    # ── NLL of temporal point process ─────────────────────────────────────
    # Event term: -Σ log λ*(t_i)
    nll_event = -(log_lams * mask_f).sum() / n_valid

    # Integral term: Σ (elapsed_s) * E_mc[λ*(t)]
    elapsed_s = elapsed_ms / 1000.0
    integral = (elapsed_s * mc_lams.mean(dim=-1) * mask_f).sum() / n_valid

    return bce + nll_weight * (nll_event + integral)


# ---------------------------------------------------------------------------
# Public model wrapper
# ---------------------------------------------------------------------------


class OrderS2P2Style:
    """Trained Neural Hawkes Process (CT-LSTM) model.

    Implements the full S2P2 architecture (Mei & Eisner, NeurIPS 2017) for
    marked temporal point process modelling of order-stream unsafe events.

    Use :meth:`fit` to train from a list of :class:`SequenceExample` objects.
    """

    def __init__(self, net: CTLSTMNet, tokenizer: MarkTokenizer) -> None:
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
        n_mc: int = 20,
        dropout: float = 0.1,
        epochs: int = 30,
        batch_size: int = 32,
        lr: float = 3e-3,
        weight_decay: float = 1e-4,
        pos_weight: float = 5.0,
        nll_weight: float = 0.5,
        seed: int = 42,
        device: str | None = None,
    ) -> OrderS2P2Style:
        """Train the CT-LSTM and return a ready-to-use model."""
        torch.manual_seed(seed)
        dev = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))

        tokenizer = MarkTokenizer()
        tokenizer.fit([mark for seq in sequences for mark in seq.marks])

        net = CTLSTMNet(
            vocab_size=len(tokenizer.vocab),
            embed_dim=embed_dim,
            hidden_dim=hidden_dim,
            n_mc=n_mc,
            dropout=dropout,
        ).to(dev)

        optimizer: optim.Optimizer = optim.AdamW(
            net.parameters(), lr=lr, weight_decay=weight_decay
        )
        scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

        rng = torch.Generator()
        rng.manual_seed(seed)
        idx = list(range(len(sequences)))

        for _ in range(epochs):
            net.train()
            perm = torch.randperm(len(idx), generator=rng).tolist()
            for start in range(0, len(perm), batch_size):
                batch = [sequences[perm[i]] for i in perm[start : start + batch_size]]
                marks_t, log_d_t, feats_t, elapsed_t, mask_t, labels_t = _collate_s2p2(
                    batch, tokenizer
                )
                marks_t = marks_t.to(dev)
                log_d_t = log_d_t.to(dev)
                feats_t = feats_t.to(dev)
                elapsed_t = elapsed_t.to(dev)
                mask_t = mask_t.to(dev)
                labels_t = labels_t.to(dev)

                hazard_probs, log_lams, mc_lams = net(
                    marks_t, log_d_t, feats_t, elapsed_t, mask_t
                )
                loss = _s2p2_loss(
                    hazard_probs, log_lams, mc_lams,
                    elapsed_t, labels_t, mask_t,
                    pos_weight, nll_weight,
                )

                optimizer.zero_grad()
                loss.backward()  # type: ignore[no-untyped-call]
                nn.utils.clip_grad_norm_(net.parameters(), max_norm=5.0)
                optimizer.step()

            scheduler.step()

        net.eval()
        return cls(net=net, tokenizer=tokenizer)

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def predict_sequence(self, sequence: SequenceExample) -> list[float]:
        marks_t, log_d_t, feats_t, elapsed_t, mask_t, _ = _collate_s2p2(
            [sequence], self._tokenizer
        )
        with torch.no_grad():
            hazard_probs, _, _ = self._net(marks_t, log_d_t, feats_t, elapsed_t, mask_t)
        return cast(list[float], hazard_probs[0, : len(sequence.marks)].tolist())

    def predict(self, sequences: list[SequenceExample]) -> list[float]:
        scores: list[float] = []
        for sequence in sequences:
            scores.extend(self.predict_sequence(sequence))
        return scores

    def state_dict(self) -> dict[str, Any]:
        return {"net": self._net.state_dict(), "vocab": self._tokenizer.vocab}

    @classmethod
    def load(cls, state: dict[str, Any], **net_kwargs: Any) -> OrderS2P2Style:
        tokenizer = MarkTokenizer()
        tokenizer.vocab = state["vocab"]
        net = CTLSTMNet(vocab_size=len(tokenizer.vocab), **net_kwargs)
        net.load_state_dict(state["net"])
        net.eval()
        return cls(net=net, tokenizer=tokenizer)
