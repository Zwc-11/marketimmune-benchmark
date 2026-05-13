from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ReplayReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    scenario_id: str
    events_processed: int = Field(ge=0)
    agent_events_processed: int = Field(ge=0)
    fills: int = Field(ge=0)
    replay_duration_seconds: float = Field(ge=0)
    replay_speed_x: float = Field(ge=0)
    p95_event_latency_ms: float = Field(ge=0)
    run_hash: str
    best_bid_below_ask: bool
    no_negative_quantity: bool
    unique_order_ids: bool
    real_depth_snapshots_seen: int = Field(ge=0, default=0)
    shadow_depth_comparable_points: int = Field(ge=0, default=0)
    shadow_vs_real_mid_mae_bps: float = Field(ge=0, default=0)
    shadow_vs_real_spread_mae_bps: float = Field(ge=0, default=0)
