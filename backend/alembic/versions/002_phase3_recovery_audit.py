"""Phase 3: recovery_cases, actions, audit_events + customer hold flags

Revision ID: 002
Revises: 001
Create Date: 2026-08-21
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Customer hold flags (observable CRM data) ─────────────────────────────
    op.add_column("customers", sa.Column("dispute_hold", sa.Boolean, nullable=False, server_default="false"))
    op.add_column("customers", sa.Column("legal_hold",   sa.Boolean, nullable=False, server_default="false"))
    op.add_column("customers", sa.Column("opt_out",      sa.Boolean, nullable=False, server_default="false"))

    # ── recovery_cases ────────────────────────────────────────────────────────
    op.create_table(
        "recovery_cases",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "customer_id",
            sa.Integer,
            sa.ForeignKey("customers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("risk_score", sa.Numeric(6, 4), nullable=False),
        sa.Column("risk_level", sa.String(10), nullable=False),
        sa.Column("diagnosis", sa.String(50), nullable=True),
        sa.Column("diagnosis_confidence", sa.Numeric(5, 4), nullable=True),
        sa.Column("proposed_action", sa.String(50), nullable=True),
        sa.Column("selected_action", sa.String(50), nullable=True),
        sa.Column("policy_status", sa.String(20), nullable=True),
        sa.Column("outcome_status", sa.String(20), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_recovery_cases_customer_id", "recovery_cases", ["customer_id"])

    # ── actions ───────────────────────────────────────────────────────────────
    op.create_table(
        "actions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "case_id",
            sa.Integer,
            sa.ForeignKey("recovery_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "customer_id",
            sa.Integer,
            sa.ForeignKey("customers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("idempotency_key", sa.String(100), nullable=False, unique=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column("policy_result", sa.JSON, nullable=False),
    )
    op.create_index("ix_actions_case_id", "actions", ["case_id"])
    op.create_index("ix_actions_customer_id", "actions", ["customer_id"])
    op.create_index("ix_actions_timestamp", "actions", ["timestamp"])

    # ── audit_events ──────────────────────────────────────────────────────────
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "case_id",
            sa.Integer,
            sa.ForeignKey("recovery_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("actor", sa.String(100), nullable=False),
        sa.Column("payload", sa.JSON, nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column("idempotency_key", sa.String(100), nullable=True),
    )
    op.create_index("ix_audit_events_case_id", "audit_events", ["case_id"])
    op.create_index("ix_audit_events_timestamp", "audit_events", ["timestamp"])


def downgrade() -> None:
    op.drop_table("audit_events")
    op.drop_table("actions")
    op.drop_table("recovery_cases")
    op.drop_column("customers", "opt_out")
    op.drop_column("customers", "legal_hold")
    op.drop_column("customers", "dispute_hold")
