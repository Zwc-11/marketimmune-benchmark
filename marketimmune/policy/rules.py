from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class PolicyAction(StrEnum):
    ALLOW = "allow"
    ALERT = "alert"
    BLOCK = "block"


class RuleDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    action: PolicyAction
    matched_rules: list[str]
    feature_snapshot: dict[str, float]
    reason_codes: list[str]


class RuleEngine:
    def decide(self, features: dict[str, float]) -> RuleDecision:
        matched: list[str] = []
        if features.get("w1000_agentic_burst_rate_per_second", 0.0) > 15:
            matched.append("burst_rate_high")
        if features.get("w5000_order_quantity_sum", 0.0) > 3:
            matched.append("large_layered_quantity")
        if features.get("w5000_order_sell_ratio", 0.0) > 0.9:
            matched.append("one_sided_sell_pressure")
        if features.get("w1000_agentic_min_interarrival_ms", 1000.0) < 10:
            matched.append("rapid_order_interarrival")
        if features.get("w60000_market_price_drift", 0.0) > 50:
            matched.append("sharp_buy_price_drift")
        if features.get("w1000_order_cancel_rate", 0.0) > 0.45:
            matched.append("cancel_rate_spike")
        if features.get("w5000_agentic_self_cross_proxy_count", 0.0) >= 3:
            matched.append("wash_trade_self_cross_proxy")
        if (
            features.get("w1000_agentic_unique_agents", 0.0) >= 2
            and features.get("w1000_agentic_burst_rate_per_second", 0.0) > 10
        ):
            matched.append("cross_account_synchronized_burst")
        if (
            features.get("w5000_order_price_range", 0.0) > 75
            and features.get("w5000_order_quantity_max", 0.0) > 0.05
        ):
            matched.append("stop_run_or_feedback_sweep")

        if len(matched) >= 2:
            action = PolicyAction.BLOCK
        elif matched:
            action = PolicyAction.ALERT
        else:
            action = PolicyAction.ALLOW
        return RuleDecision(
            action=action,
            matched_rules=matched,
            feature_snapshot=features,
            reason_codes=matched or ["no_rule_matched"],
        )
