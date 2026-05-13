# GRU-MTPP Model Card

## Architecture

This model implements a **GRU-based Marked Temporal Point Process (MTPP)** trained end-to-end with PyTorch.

### Input representation

Each order event is encoded as:
- A learnable mark embedding (event family / type)
- Log-transformed inter-event time delta (time since previous event in the sequence)
- Numeric feature vector from the feature store (burst rate, price drift, cancel rates)

### Sequence model

A multi-layer GRU processes the event sequence left-to-right. Variable-length sequences are handled with pack/pad so padded positions are never seen by the GRU.

### Hazard head

A linear layer maps each GRU hidden state to a scalar logit. Sigmoid activation yields P(unsafe | history up to event t).

### Training objective

Binary cross-entropy with class-weighted positive oversampling (pos_weight=5). Optimised with AdamW + cosine LR decay and gradient clipping (max_norm=5).
