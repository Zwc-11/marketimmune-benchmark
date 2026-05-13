# Threat Model

MarketImmune V1 detects unsafe autonomous trading-agent behavior inside exchange
microstructure.

## Unsafe Behavior Families

1. Spoofing-style layered orders.
2. Quote stuffing.
3. Momentum ignition attempts.
4. Wash-like self-cross patterns in synthetic scenarios.
5. Cancellation bursts near touch.
6. Liquidity fade after inducing response.
7. Cross-account synchronized bursts in synthetic clusters.
8. Latency-edge exploitation patterns.
9. Stop-run style aggressive sweeps.
10. Inventory-oblivious runaway agents.
11. Feedback-loop agents that amplify volatility.
12. Repeated toxic order placement after alerts.

## Benign Families

1. Passive market maker.
2. TWAP execution agent.
3. VWAP execution agent.
4. Inventory rebalancer.
5. Random small-liquidity taker.

## Non-Goals

- Cross-CEX surveillance.
- On-chain analytics.
- Live trading or order execution.
- Private account identity inference.
- Price-prediction alpha.
- Unsupported claims about real manipulator identity.
