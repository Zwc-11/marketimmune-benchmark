from __future__ import annotations

from datetime import UTC, datetime

import pytest

from marketimmune.agents.base import Agent
from marketimmune.agents.benign import InventoryRebalancer, TwapExecutor
from marketimmune.scenarios.config import ScenarioConfig
from marketimmune.scenarios.generator import AGENT_REGISTRY, generate_scenario
from marketimmune.scenarios.labels import labels_for_events, risk_family
from marketimmune.schemas.labels import RiskFamily

NOW = datetime(2024, 5, 1, tzinfo=UTC)


def config(family: str, unsafe: bool) -> ScenarioConfig:
    return ScenarioConfig(
        scenario_id=f"s-{family}",
        family=family,
        seed=7,
        start=NOW,
        mid_price=65000,
        event_count=5,
        unsafe=unsafe,
    )


def test_agent_families_minimum_count() -> None:
    assert len(AGENT_REGISTRY) >= 12


def test_generation_is_deterministic() -> None:
    first = generate_scenario(config("quote_stuffing", True))
    second = generate_scenario(config("quote_stuffing", True))
    assert first.manifest()["event_hash"] == second.manifest()["event_hash"]


def test_benign_agents_do_not_create_unsafe_labels() -> None:
    scenario = generate_scenario(config("passive_market_maker", False))
    assert not any(label.unsafe for label in scenario.event_labels)
    assert scenario.session_label.unsafe is False


def test_unsafe_agents_create_event_and_session_labels() -> None:
    scenario = generate_scenario(config("spoofing_layering", True))
    assert any(label.unsafe for label in scenario.event_labels)
    assert any(not label.unsafe for label in scenario.event_labels)
    assert scenario.session_label.unsafe is True


def test_new_threat_model_families_are_registered() -> None:
    required = {
        "synthetic_wash_like",
        "coordinated_burst",
        "latency_edge",
        "stop_run_sweep",
        "runaway_inventory",
        "volatility_feedback",
    }
    assert required.issubset(set(AGENT_REGISTRY))


@pytest.mark.parametrize("family", sorted(AGENT_REGISTRY))
def test_registered_agents_generate_events(family: str) -> None:
    scenario = generate_scenario(config(family, AGENT_REGISTRY[family].unsafe))
    assert len(scenario.events) == 5


def test_unknown_unsafe_family_uses_default_window() -> None:
    scenario = generate_scenario(config("quote_stuffing", True))
    labels, session = labels_for_events(
        scenario_id="unknown",
        session_id="unknown-session",
        family="future_family",
        unsafe=True,
        events=scenario.events,
    )
    assert any(label.unsafe for label in labels)
    assert any(not label.unsafe for label in labels)
    assert session.unsafe is True


def test_manifest_includes_seed_and_hashes() -> None:
    manifest = generate_scenario(config("momentum_ignition", True)).manifest()
    assert manifest["seed"] == 7
    assert "event_hash" in manifest
    assert "label_hash" in manifest


def test_scenario_write_outputs_files(tmp_path) -> None:  # type: ignore[no-untyped-def]
    scenario = generate_scenario(config("momentum_ignition", True))
    scenario.write(tmp_path)
    assert (tmp_path / "s-momentum_ignition_events.json").exists()
    assert (tmp_path / "s-momentum_ignition_labels.json").exists()
    assert (tmp_path / "s-momentum_ignition_manifest.json").exists()


def test_unknown_risk_family_maps_to_benign() -> None:
    assert risk_family("unknown") is RiskFamily.BENIGN


def test_twap_executor_generates_orders() -> None:
    orders = TwapExecutor("twap", 1).generate(
        scenario_id="s",
        start=NOW,
        mid_price=65000,
        count=2,
    )
    assert len(orders) == 2


def test_inventory_rebalancer_generates_orders() -> None:
    orders = InventoryRebalancer("inv", 1).generate(
        scenario_id="s",
        start=NOW,
        mid_price=65000,
        count=2,
    )
    assert len(orders) == 2


def test_base_agent_generate_raises() -> None:
    class ConcreteAgent(Agent):
        family = "test"
        unsafe = False

        def generate(self, **_kwargs):  # type: ignore[no-untyped-def]
            return super().generate(**_kwargs)

    with pytest.raises(NotImplementedError):
        ConcreteAgent("a", 1).generate(
            scenario_id="s",
            start=NOW,
            mid_price=65000,
            count=1,
        )
