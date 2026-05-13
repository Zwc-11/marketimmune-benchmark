from __future__ import annotations

from datetime import UTC, datetime

from marketimmune.schemas.events import AgentOrderEvent
from marketimmune.schemas.labels import EventLabel, RiskFamily, SessionLabel


def risk_family(value: str) -> RiskFamily:
    try:
        return RiskFamily(value)
    except ValueError:
        return RiskFamily.BENIGN


def labels_for_events(
    *,
    scenario_id: str,
    session_id: str,
    family: str,
    unsafe: bool,
    events: list[AgentOrderEvent],
) -> tuple[list[EventLabel], SessionLabel]:
    created_at = datetime.now(tz=UTC)
    mapped_family = risk_family(family) if unsafe else RiskFamily.BENIGN
    event_unsafe = [
        _event_is_unsafe(index=index, total=len(events), family=family, scenario_unsafe=unsafe)
        for index, _event in enumerate(events)
    ]
    event_labels = [
        EventLabel(
            scenario_id=scenario_id,
            created_at=created_at,
            event_id=event.event_id or "",
            family=(mapped_family if is_unsafe else RiskFamily.BENIGN),
            unsafe=is_unsafe,
        )
        for event, is_unsafe in zip(events, event_unsafe, strict=True)
    ]
    session_is_unsafe = any(event_unsafe)
    session_label = SessionLabel(
        scenario_id=scenario_id,
        created_at=created_at,
        session_id=session_id,
        family=(mapped_family if session_is_unsafe else RiskFamily.BENIGN),
        unsafe=session_is_unsafe,
    )
    return event_labels, session_label


def _event_is_unsafe(*, index: int, total: int, family: str, scenario_unsafe: bool) -> bool:
    if not scenario_unsafe:
        return False
    if total <= 1:
        return True
    if family in {"quote_stuffing", "coordinated_burst", "latency_edge"}:
        return index >= int(0.25 * total)
    if family in {"spoofing_layering", "synthetic_wash_like"}:
        return index >= int(0.5 * total)
    if family in {"momentum_ignition", "stop_run_sweep", "runaway_inventory"}:
        return index >= int(0.6 * total)
    if family == "volatility_feedback":
        return index >= int(0.4 * total)
    return index >= int(0.5 * total)
