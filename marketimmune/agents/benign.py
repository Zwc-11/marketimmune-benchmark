from __future__ import annotations

from datetime import datetime

from marketimmune.agents.base import Agent, step_time
from marketimmune.schemas.events import AgentOrderEvent, Side


class PassiveMarketMaker(Agent):
    family = "passive_market_maker"
    unsafe = False

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
                timestamp=step_time(start, i),
                side=Side.BUY if i % 2 == 0 else Side.SELL,
                price=mid_price * (0.999 if i % 2 == 0 else 1.001),
                quantity=0.01,
            )
            for i in range(count)
        ]


class TwapExecutor(Agent):
    family = "twap_execution"
    unsafe = False

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
                timestamp=step_time(start, i, 1000),
                side=Side.BUY,
                price=mid_price * 0.9995,
                quantity=0.005,
            )
            for i in range(count)
        ]


class InventoryRebalancer(Agent):
    family = "inventory_rebalancer"
    unsafe = False

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
                timestamp=step_time(start, i, 750),
                side=Side.SELL if i % 3 == 0 else Side.BUY,
                price=mid_price,
                quantity=0.004,
            )
            for i in range(count)
        ]
