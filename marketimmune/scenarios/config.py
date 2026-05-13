from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ScenarioConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    scenario_id: str = Field(min_length=1)
    family: str = Field(min_length=1)
    seed: int
    start: datetime
    mid_price: float = Field(gt=0)
    event_count: int = Field(gt=0)
    unsafe: bool
