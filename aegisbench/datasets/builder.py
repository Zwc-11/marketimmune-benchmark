from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from marketimmune.features.feature_store import build_feature_store
from marketimmune.schemas.events import AgentOrderEvent, parse_event


@dataclass(frozen=True)
class BenchmarkExample:
    scenario_id: str
    event_id: str
    timestamp_ms: float
    family: str
    unsafe: bool
    features: dict[str, float]


def _load_events(path: Path) -> list[AgentOrderEvent]:
    payloads = json.loads(path.read_text(encoding="utf-8"))
    events: list[AgentOrderEvent] = []
    for payload in payloads:
        event = parse_event(payload)
        if not isinstance(event, AgentOrderEvent):
            raise ValueError(f"expected agent order event in {path}")
        events.append(event)
    return events


def _load_manifest(path: Path) -> dict[str, object]:
    return cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))


def build_examples(scenario_root: Path) -> list[BenchmarkExample]:
    examples: list[BenchmarkExample] = []
    for event_file in sorted(scenario_root.glob("*_events.json")):
        scenario_id = event_file.name.removesuffix("_events.json")
        manifest = _load_manifest(scenario_root / f"{scenario_id}_manifest.json")
        events = _load_events(event_file)
        feature_rows, _ = build_feature_store(events)
        for event, features in zip(events, feature_rows, strict=True):
            examples.append(
                BenchmarkExample(
                    scenario_id=scenario_id,
                    event_id=event.event_id or "",
                    timestamp_ms=event.timestamp.timestamp() * 1000,
                    family=str(manifest["family"]),
                    unsafe=bool(manifest["unsafe"]),
                    features=features,
                )
            )
    return examples


def examples_to_rows(examples: list[BenchmarkExample]) -> list[dict[str, object]]:
    return [
        {
            "scenario_id": example.scenario_id,
            "event_id": example.event_id,
            "timestamp_ms": example.timestamp_ms,
            "family": example.family,
            "unsafe": example.unsafe,
            "features": example.features,
        }
        for example in examples
    ]
