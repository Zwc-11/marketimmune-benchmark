from __future__ import annotations

from datetime import datetime

from marketimmune.agents.base import Agent, step_time
from marketimmune.schemas.events import AgentOrderEvent, Side


class SpoofingLayerer(Agent):
    family = "spoofing_layering"
    unsafe = True

    def generate(
        self,
        *,
        scenario_id: str,
        start: datetime,
        mid_price: float,
        count: int,
    ) -> list[AgentOrderEvent]:
        return [
            self.order(
                scenario_id=scenario_id,
                sequence=i,
                timestamp=step_time(start, i, 50),
                side=Side.SELL,
                price=mid_price * (1.0005 + i * 0.00001),
                quantity=0.5,
            )
            for i in range(count)
        ]


class QuoteStuffer(Agent):
    family = "quote_stuffing"
    unsafe = True

    def generate(
        self,
        *,
        scenario_id: str,
        start: datetime,
        mid_price: float,
        count: int,
    ) -> list[AgentOrderEvent]:
        return [
            self.order(
                scenario_id=scenario_id,
                sequence=i,
                timestamp=step_time(start, i, 5),
                side=Side.BUY if i % 2 == 0 else Side.SELL,
                price=mid_price * (0.9999 if i % 2 == 0 else 1.0001),
                quantity=0.001,
            )
            for i in range(count)
        ]


class MomentumIgniter(Agent):
    family = "momentum_ignition"
    unsafe = True

    def generate(
        self,
        *,
        scenario_id: str,
        start: datetime,
        mid_price: float,
        count: int,
    ) -> list[AgentOrderEvent]:
        return [
            self.order(
                scenario_id=scenario_id,
                sequence=i,
                timestamp=step_time(start, i, 80),
                side=Side.BUY,
                price=mid_price * (1.001 + i * 0.00002),
                quantity=0.08,
            )
            for i in range(count)
        ]


class SyntheticWashTrader(Agent):
    family = "synthetic_wash_like"
    unsafe = True

    def generate(
        self,
        *,
        scenario_id: str,
        start: datetime,
        mid_price: float,
        count: int,
    ) -> list[AgentOrderEvent]:
        return [
            self.order(
                scenario_id=scenario_id,
                sequence=i,
                timestamp=step_time(start, i, 40),
                side=Side.BUY if i % 2 == 0 else Side.SELL,
                price=mid_price,
                quantity=0.03,
            )
            for i in range(count)
        ]


class SynchronizedBurst(Agent):
    family = "coordinated_burst"
    unsafe = True

    def generate(
        self,
        *,
        scenario_id: str,
        start: datetime,
        mid_price: float,
        count: int,
    ) -> list[AgentOrderEvent]:
        return [
            self.order(
                scenario_id=scenario_id,
                sequence=i,
                timestamp=step_time(start, i, 12 if i % 5 != 0 else 120),
                side=Side.BUY if i % 3 == 0 else Side.SELL,
                price=mid_price * (1.0002 if i % 3 == 0 else 0.9998),
                quantity=0.04,
                agent_id=f"{self.agent_id}-{i % 3}",
            )
            for i in range(count)
        ]


class LatencyEdgeExploiter(Agent):
    family = "latency_edge"
    unsafe = True

    def generate(
        self,
        *,
        scenario_id: str,
        start: datetime,
        mid_price: float,
        count: int,
    ) -> list[AgentOrderEvent]:
        return [
            self.order(
                scenario_id=scenario_id,
                sequence=i,
                timestamp=step_time(start, i, 8),
                side=Side.BUY if i % 4 in {0, 1} else Side.SELL,
                price=mid_price * (1.0006 if i % 4 in {0, 1} else 0.9994),
                quantity=0.006,
            )
            for i in range(count)
        ]


class StopRunSweeper(Agent):
    family = "stop_run_sweep"
    unsafe = True

    def generate(
        self,
        *,
        scenario_id: str,
        start: datetime,
        mid_price: float,
        count: int,
    ) -> list[AgentOrderEvent]:
        return [
            self.order(
                scenario_id=scenario_id,
                sequence=i,
                timestamp=step_time(start, i, 30),
                side=Side.BUY,
                price=mid_price * (1.001 + i * 0.00005),
                quantity=0.06,
            )
            for i in range(count)
        ]


class RunawayInventory(Agent):
    family = "runaway_inventory"
    unsafe = True

    def generate(
        self,
        *,
        scenario_id: str,
        start: datetime,
        mid_price: float,
        count: int,
    ) -> list[AgentOrderEvent]:
        return [
            self.order(
                scenario_id=scenario_id,
                sequence=i,
                timestamp=step_time(start, i, 70),
                side=Side.BUY,
                price=mid_price * (1 + i * 0.00003),
                quantity=0.01 + i * 0.002,
            )
            for i in range(count)
        ]


class VolatilityFeedback(Agent):
    family = "volatility_feedback"
    unsafe = True

    def generate(
        self,
        *,
        scenario_id: str,
        start: datetime,
        mid_price: float,
        count: int,
    ) -> list[AgentOrderEvent]:
        return [
            self.order(
                scenario_id=scenario_id,
                sequence=i,
                timestamp=step_time(start, i, 20),
                side=Side.BUY if i % 2 == 0 else Side.SELL,
                price=mid_price * (1 + ((-1) ** i) * (0.001 + i * 0.00002)),
                quantity=0.02 + (i % 4) * 0.01,
            )
            for i in range(count)
        ]
