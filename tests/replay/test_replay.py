from __future__ import annotations

from datetime import UTC, datetime

import pytest

from marketimmune.replay.clock import ReplayClock
from marketimmune.replay.matching_engine import MatchingEngine
from marketimmune.replay.order_book import TopNOrderBook, TopOfBook
from marketimmune.replay.replay_runner import ReplayRunner, p95
from marketimmune.replay.shadow_book import ShadowBook
from marketimmune.scenarios.config import ScenarioConfig
from marketimmune.scenarios.generator import generate_scenario
from marketimmune.schemas.events import AggTradeEvent, BookTickerEvent, KlineEvent

NOW = datetime(2024, 5, 1, tzinfo=UTC)


def kline(sequence: int) -> KlineEvent:
    return KlineEvent(
        symbol="BTCUSDT",
        timestamp=NOW.replace(minute=sequence),
        sequence=sequence,
        interval="1m",
        open_time=NOW.replace(minute=sequence),
        close_time=NOW.replace(minute=sequence),
        open_price=65000,
        high_price=65100,
        low_price=64900,
        close_price=65000 + sequence,
        volume=1,
        trade_count=1,
    )


def test_replay_clock_rejects_backwards_time() -> None:
    clock = ReplayClock()
    clock.advance(NOW.replace(minute=1))
    with pytest.raises(ValueError):
        clock.advance(NOW)


def test_order_book_bid_below_ask() -> None:
    book = TopNOrderBook()
    top = book.apply_market_event(kline(0))
    assert top is not None
    assert book.invariant_bid_below_ask()


def test_order_book_applies_book_ticker_event() -> None:
    book = TopNOrderBook()
    top = book.apply_market_event(
        BookTickerEvent(
            symbol="BTCUSDT",
            timestamp=NOW,
            sequence=0,
            update_id=1,
            bid_price=64999.0,
            bid_quantity=2.0,
            ask_price=65001.0,
            ask_quantity=3.0,
        )
    )
    assert top == TopOfBook(64999.0, 2.0, 65001.0, 3.0)


def test_matching_fill_cannot_exceed_remaining_quantity() -> None:
    scenario = generate_scenario(
        ScenarioConfig(
            scenario_id="s",
            family="momentum_ignition",
            seed=1,
            start=NOW,
            mid_price=65000,
            event_count=1,
            unsafe=True,
        )
    )
    fill = MatchingEngine().match(scenario.events[0], TopOfBook(64999, 1, 65000, 0.01))
    assert fill is not None
    assert fill.filled_quantity <= scenario.events[0].remaining_quantity


def test_shadow_book_rejects_duplicate_order_id() -> None:
    scenario = generate_scenario(
        ScenarioConfig(
            scenario_id="s",
            family="passive_market_maker",
            seed=1,
            start=NOW,
            mid_price=65000,
            event_count=1,
            unsafe=False,
        )
    )
    shadow = ShadowBook()
    shadow.apply_agent_order(scenario.events[0])
    with pytest.raises(ValueError):
        shadow.apply_agent_order(scenario.events[0])


def test_replay_same_seed_same_run_hash() -> None:
    scenario = generate_scenario(
        ScenarioConfig(
            scenario_id="s",
            family="spoofing_layering",
            seed=1,
            start=NOW,
            mid_price=65000,
            event_count=3,
            unsafe=True,
        )
    )
    first = ReplayRunner().run(
        scenario_id="s",
        market_events=[kline(0), kline(1)],
        agent_events=scenario.events,
    )
    second = ReplayRunner().run(
        scenario_id="s",
        market_events=[kline(0), kline(1)],
        agent_events=scenario.events,
    )
    assert first.run_hash == second.run_hash


def test_matching_sell_order_fills_at_bid() -> None:
    scenario = generate_scenario(
        ScenarioConfig(
            scenario_id="s",
            family="passive_market_maker",
            seed=1,
            start=NOW,
            mid_price=65000,
            event_count=2,
            unsafe=False,
        )
    )
    sell = scenario.events[1]
    fill = MatchingEngine().match(sell, TopOfBook(65100, 1, 65101, 1))
    assert fill is not None
    assert fill.fill_price == 65100


def test_matching_no_top_has_no_fill() -> None:
    scenario = generate_scenario(
        ScenarioConfig(
            scenario_id="s",
            family="momentum_ignition",
            seed=1,
            start=NOW,
            mid_price=65000,
            event_count=1,
            unsafe=True,
        )
    )
    assert MatchingEngine().match(scenario.events[0], None) is None


def test_p95_empty_and_single() -> None:
    assert p95([]) == 0
    assert p95([3]) == 3


def test_order_book_ignores_non_kline_event() -> None:
    book = TopNOrderBook()
    event = AggTradeEvent(
        symbol="BTCUSDT",
        timestamp=NOW,
        sequence=0,
        aggregate_trade_id=1,
        price=65000,
        quantity=1,
        first_trade_id=1,
        last_trade_id=1,
        is_buyer_maker=True,
    )
    assert book.apply_market_event(event) is None


def test_shadow_book_returns_none_when_no_fill() -> None:
    scenario = generate_scenario(
        ScenarioConfig(
            scenario_id="s",
            family="passive_market_maker",
            seed=1,
            start=NOW,
            mid_price=65000,
            event_count=1,
            unsafe=False,
        )
    )
    assert ShadowBook().apply_agent_order(scenario.events[0]) is None


def test_shadow_book_records_fill() -> None:
    scenario = generate_scenario(
        ScenarioConfig(
            scenario_id="s",
            family="momentum_ignition",
            seed=1,
            start=NOW,
            mid_price=65000,
            event_count=1,
            unsafe=True,
        )
    )
    shadow = ShadowBook()
    shadow.book.top = TopOfBook(64999, 1, 65000, 1)
    fill = shadow.apply_agent_order(scenario.events[0])
    assert fill is not None
    assert len(shadow.fills) == 1


def test_replay_runner_handles_empty_inputs() -> None:
    report = ReplayRunner().run(scenario_id="empty", market_events=[], agent_events=[])
    assert report.events_processed == 0
    assert report.replay_duration_seconds == 0


def test_replay_runner_reports_shadow_vs_real_depth() -> None:
    market = [kline(0), kline(1)]
    real_depth = [
        BookTickerEvent(
            symbol="BTCUSDT",
            timestamp=NOW.replace(minute=0),
            sequence=0,
            update_id=1,
            bid_price=64999.0,
            bid_quantity=2.0,
            ask_price=65001.0,
            ask_quantity=2.0,
        ),
        BookTickerEvent(
            symbol="BTCUSDT",
            timestamp=NOW.replace(minute=1),
            sequence=1,
            update_id=2,
            bid_price=65000.0,
            bid_quantity=2.0,
            ask_price=65002.0,
            ask_quantity=2.0,
        ),
    ]
    report = ReplayRunner().run(
        scenario_id="depth",
        market_events=market,
        agent_events=[],
        real_depth_events=real_depth,
    )
    assert report.real_depth_snapshots_seen == 2
    assert report.shadow_depth_comparable_points == 2
    assert report.shadow_vs_real_mid_mae_bps >= 0
    assert report.shadow_vs_real_spread_mae_bps >= 0
