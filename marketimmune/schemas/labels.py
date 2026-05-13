from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LabelKind(StrEnum):
    EVENT = "event"
    SESSION = "session"
    HARM = "harm"
    SHOULD_BLOCK = "should_block"


class RiskFamily(StrEnum):
    BENIGN = "benign"
    SPOOFING_LAYERING = "spoofing_layering"
    QUOTE_STUFFING = "quote_stuffing"
    MOMENTUM_IGNITION = "momentum_ignition"
    SYNTHETIC_WASH_LIKE = "synthetic_wash_like"
    COORDINATED_BURST = "coordinated_burst"
    LATENCY_EDGE = "latency_edge"
    STOP_RUN_SWEEP = "stop_run_sweep"
    RUNAWAY_INVENTORY = "runaway_inventory"
    VOLATILITY_FEEDBACK = "volatility_feedback"


def label_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(encoded.encode("utf-8")).hexdigest()


class BaseLabel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", use_enum_values=True)

    label_id: str | None = None
    kind: LabelKind
    scenario_id: str = Field(min_length=1)
    created_at: datetime
    source: str = "synthetic"

    @field_validator("created_at")
    @classmethod
    def created_at_must_be_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("created_at must include timezone information")
        return value.astimezone(UTC)

    def model_post_init(self, __context: Any) -> None:
        if self.label_id is None:
            object.__setattr__(self, "label_id", label_hash(self.model_dump(mode="json")))


class EventLabel(BaseLabel):
    kind: LabelKind = LabelKind.EVENT
    event_id: str = Field(min_length=1)
    family: RiskFamily
    unsafe: bool


class SessionLabel(BaseLabel):
    kind: LabelKind = LabelKind.SESSION
    session_id: str = Field(min_length=1)
    family: RiskFamily
    unsafe: bool


class HarmLabel(BaseLabel):
    kind: LabelKind = LabelKind.HARM
    incident_id: str = Field(min_length=1)
    harm_score: float = Field(ge=0)
    metric_name: str = Field(min_length=1)


class ShouldBlockLabel(BaseLabel):
    kind: LabelKind = LabelKind.SHOULD_BLOCK
    event_id: str = Field(min_length=1)
    should_block: bool
    reason: str = Field(min_length=1)
