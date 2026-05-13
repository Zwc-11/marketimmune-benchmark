# S2P2 Neural Hawkes Process Model Card

## Paper

Mei & Eisner (2017) **The Neural Hawkes Process: A Neurally Self-Modulating Multivariate Point Process**. NeurIPS 2017.

## Architecture

The model implements a **Continuous-Time LSTM (CT-LSTM)**:

- **Mark embedding**: learnable lookup for each order event family.
- **7-gate CT-LSTM cell**: standard LSTM gates (i, f, z, o) plus target-cell gates (ī, f̄) and per-dimension decay rates δ (softplus).
- **Continuous-time decay** between events:
  `c(t) = c̄ + (c − c̄) · exp(−δ · (t − t_last) / 1000)`
- **Hidden state**: `h(t) = o ⊙ tanh(c(t))`
- **Intensity function**: `λ*(t) = softplus(v^T h(t) + b)` — always positive.
- **Hazard head**: `p(t_i) = sigmoid(w^T h(t_i⁻) + b)` — P(unsafe | history).

## Training Objective

Joint loss = α · NLL_TPP + β · BCE

```
NLL_TPP = −Σᵢ log λ*(tᵢ⁻) + Σᵢ ∫_{t_{i−1}}^{tᵢ} λ*(t) dt
```

The integral is approximated by Monte Carlo sampling (n_mc uniform draws per inter-event interval). BCE uses positive-class oversampling (pos_weight=5). Optimised with AdamW + cosine LR decay and gradient clipping (max_norm=5).
