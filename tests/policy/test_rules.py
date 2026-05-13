from __future__ import annotations

from marketimmune.policy.rules import PolicyAction, RuleEngine


def test_rule_engine_allows_clean_features() -> None:
    decision = RuleEngine().decide({})
    assert decision.action is PolicyAction.ALLOW


def test_rule_engine_alerts_single_rule() -> None:
    decision = RuleEngine().decide({"w1000_agentic_burst_rate_per_second": 20})
    assert decision.action is PolicyAction.ALERT


def test_rule_engine_blocks_multiple_rules() -> None:
    decision = RuleEngine().decide(
        {
            "w1000_agentic_burst_rate_per_second": 20,
            "w5000_order_quantity_sum": 4,
        }
    )
    assert decision.action is PolicyAction.BLOCK


def test_rule_decision_contains_audit_fields() -> None:
    decision = RuleEngine().decide({"w1000_agentic_burst_rate_per_second": 20})
    assert decision.matched_rules
    assert decision.feature_snapshot
    assert decision.reason_codes


def test_rule_engine_detects_sell_pressure() -> None:
    decision = RuleEngine().decide({"w5000_order_sell_ratio": 1.0})
    assert "one_sided_sell_pressure" in decision.matched_rules


def test_rule_engine_detects_rapid_interarrival() -> None:
    decision = RuleEngine().decide({"w1000_agentic_min_interarrival_ms": 5})
    assert "rapid_order_interarrival" in decision.matched_rules


def test_rule_engine_detects_price_drift() -> None:
    decision = RuleEngine().decide({"w60000_market_price_drift": 100})
    assert "sharp_buy_price_drift" in decision.matched_rules


def test_rule_engine_detects_cancel_rate_spike() -> None:
    decision = RuleEngine().decide({"w1000_order_cancel_rate": 0.9})
    assert "cancel_rate_spike" in decision.matched_rules


def test_rule_engine_detects_wash_trade_proxy() -> None:
    decision = RuleEngine().decide({"w5000_agentic_self_cross_proxy_count": 3})
    assert "wash_trade_self_cross_proxy" in decision.matched_rules


def test_rule_engine_detects_cross_account_burst() -> None:
    decision = RuleEngine().decide(
        {"w1000_agentic_unique_agents": 2, "w1000_agentic_burst_rate_per_second": 12}
    )
    assert "cross_account_synchronized_burst" in decision.matched_rules


def test_rule_engine_detects_stop_run_or_feedback_sweep() -> None:
    decision = RuleEngine().decide(
        {"w5000_order_price_range": 100, "w5000_order_quantity_max": 0.08}
    )
    assert "stop_run_or_feedback_sweep" in decision.matched_rules
