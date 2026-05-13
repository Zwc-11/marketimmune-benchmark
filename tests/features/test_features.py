from __future__ import annotations

from datetime import UTC, datetime

from marketimmune.features.agentic_features import agentic_features
from marketimmune.features.feature_store import build_feature_store, feature_snapshot
from marketimmune.features.market_features import market_features
from marketimmune.features.windows import windows_for_events
from marketimmune.scenarios.config import ScenarioConfig
from marketimmune.scenarios.generator import generate_scenario

NOW = datetime(2024, 5, 1, tzinfo=UTC)


def scenario_events() -> list:
    return generate_scenario(
        ScenarioConfig(
            scenario_id="features",
            family="quote_stuffing",
            seed=5,
            start=NOW,
            mid_price=65000,
            event_count=10,
            unsafe=True,
        )
    ).events


def test_feature_snapshot_has_30_plus_features_after_windows() -> None:
    rows, _ = build_feature_store(scenario_events())
    assert len(rows[-1]) - 1 >= 30


def test_feature_latency_under_minimum_threshold() -> None:
    _, p95_latency = build_feature_store(scenario_events())
    assert p95_latency < 20


def test_windows_do_not_look_ahead() -> None:
    events = scenario_events()
    snapshots = windows_for_events(events, [])
    assert len(snapshots) == len(events)


def test_feature_snapshot_counts_current_prefix_only() -> None:
    events = scenario_events()
    features = feature_snapshot(events[:3])
    assert features["order_order_count"] == 3


def test_empty_market_features() -> None:
    assert market_features([])["notional_sum"] == 0


def test_empty_agentic_features() -> None:
    assert agentic_features([])["unique_agents"] == 0


def test_agentic_self_cross_proxy_counts_same_price_opposite_sides() -> None:
    events = generate_scenario(
        ScenarioConfig(
            scenario_id="wash",
            family="synthetic_wash_like",
            seed=5,
            start=NOW,
            mid_price=65000,
            event_count=4,
            unsafe=True,
        )
    ).events
    features = agentic_features(events)
    assert features["self_cross_proxy_count"] > 0
    assert features["opposite_side_same_price_pairs"] > 0


def test_agentic_features_count_synchronized_accounts() -> None:
    events = generate_scenario(
        ScenarioConfig(
            scenario_id="burst",
            family="coordinated_burst",
            seed=5,
            start=NOW,
            mid_price=65000,
            event_count=6,
            unsafe=True,
        )
    ).events
    assert agentic_features(events)["unique_agents"] == 3


def test_window_evicts_old_events() -> None:
    events = scenario_events()
    snapshots = windows_for_events(events, [__import__("datetime").timedelta(milliseconds=1)])
    assert len(snapshots[-1]["1"]) <= 1
