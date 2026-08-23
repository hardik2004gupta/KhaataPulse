"""
Action eligibility per diagnosis cause - CLAUDE.md §13.

The LLM's diagnosis narrows the eligible action space. This mapping determines
which actions are financially rational candidates given the root cause.
The optimizer then ranks eligible actions by Expected Net Revenue.
"""

# cause → ordered list of eligible action types (all valid, not ranked)
CAUSE_ELIGIBILITY: dict[str, list[str]] = {
    "card_expired": [
        "smart_link",       # most effective: customer updates card via link
        "silent_retry",     # low-cost but unlikely to fix expired card
        "grace_period",
        "human_escalation",
    ],
    "billing_migration": [
        "smart_link",       # resolves entity/method mismatch
        "silent_retry",
        "grace_period",
        "human_escalation",
    ],
    "temporary_cash_flow": [
        "grace_period",     # directly addresses timing constraint
        "silent_retry",
        "smart_link",
        "human_escalation",
    ],
    "price_friction": [
        "grace_period",
        "smart_link",
        "human_escalation",
        "suppress",         # may be better than aggressive contact
    ],
    "churn_intent": [
        "grace_period",
        "human_escalation",
        "suppress",         # suppress avoids escalation of churn intent
        "smart_link",
    ],
}


def get_eligible_actions(cause: str) -> list[str]:
    """Return eligible action types for a given diagnosis cause."""
    return CAUSE_ELIGIBILITY.get(cause, ["silent_retry", "smart_link", "grace_period", "human_escalation"])
