from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from random import Random

from marketimmune.schemas.events import AgentOrderEvent, OrderAction, Side


class Agent(ABC):
    family: str
    unsafe: bool

    def __init__(self, agent_id: str, seed: int) -> None:
        self.agent_id = agent_id
        self.random = Random(seed)

    def order(
        self,
        *,
        scenario_id: str,
        sequence: int,
        timestamp: datetime,
        side: Side,
        price: float,
        quantity: float,
        agent_id: str | None = None,
    ) -> AgentOrderEvent:
        owner = agent_id or self.agent_id
        return AgentOrderEvent(
            symbol="BTCUSDT",
            timestamp=timestamp,
            sequence=sequence,
            scenario_id=scenario_id,
            agent_id=owner,
            order_id=f"{scenario_id}-{owner}-{sequence}",
            action=OrderAction.NEW,
            side=side,
            price=price,
            quantity=quantity,
            remaining_quantity=quantity,
        )

    @abstractmethod
    def generate(
        self,
        *,
        scenario_id: str,
        start: datetime,
        mid_price: float,
        count: int,
    ) -> list[AgentOrderEvent]:
        raise NotImplementedError


def step_time(start: datetime, sequence: int, step_ms: int = 100) -> datetime:
    return start + timedelta(milliseconds=sequence * step_ms)
