"""Initial schema — Phase 1: customers, subscriptions, payments, events, sim_runs, sim_outcomes

Revision ID: 001
Revises:
Create Date: 2026-08-21
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── customers ─────────────────────────────────────────────────────────────
    # subscription_id FK is added after subscriptions table is created (circular).
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("segment", sa.String(50), nullable=False),
        sa.Column("ltv", sa.Numeric(12, 2), nullable=False),
        sa.Column("subscription_id", sa.Integer, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )
    op.create_index("ix_customers_subscription_id", "customers", ["subscription_id"])

    # ── subscriptions ──────────────────────────────────────────────────────────
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "customer_id",
            sa.Integer,
            sa.ForeignKey("customers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("plan", sa.String(100), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("renewal_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )
    op.create_index("ix_subscriptions_customer_id", "subscriptions", ["customer_id"])

    # Add FK from customers.subscription_id → subscriptions.id (resolves circular)
    op.create_foreign_key(
        "fk_customer_subscription_id",
        "customers",
        "subscriptions",
        ["subscription_id"],
        ["id"],
    )

    # ── payments ──────────────────────────────────────────────────────────────
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "customer_id",
            sa.Integer,
            sa.ForeignKey("customers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "subscription_id",
            sa.Integer,
            sa.ForeignKey("subscriptions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("failure_code", sa.String(100), nullable=True),
        sa.Column("payment_method", sa.String(50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )
    op.create_index("ix_payments_customer_id", "payments", ["customer_id"])
    op.create_index("ix_payments_subscription_id", "payments", ["subscription_id"])

    # ── events (observable only) ───────────────────────────────────────────────
    op.create_table(
        "events",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "customer_id",
            sa.Integer,
            sa.ForeignKey("customers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON, nullable=False),
    )
    op.create_index("ix_events_customer_id", "events", ["customer_id"])
    op.create_index("ix_events_timestamp", "events", ["timestamp"])

    # ── sim_runs (simulator metadata) ──────────────────────────────────────────
    op.create_table(
        "sim_runs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("seed", sa.Integer, nullable=False),
        sa.Column("cohort_size", sa.Integer, nullable=False),
        sa.Column("simulator_version", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── sim_outcomes (HIDDEN — simulator-internal) ─────────────────────────────
    op.create_table(
        "sim_outcomes",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "simulation_run_id",
            sa.Integer,
            sa.ForeignKey("sim_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "customer_id",
            sa.Integer,
            sa.ForeignKey("customers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("p_payment", sa.Numeric(6, 4), nullable=False),
        sa.Column("p_churn", sa.Numeric(6, 4), nullable=False),
        sa.UniqueConstraint(
            "simulation_run_id", "customer_id", "action_type",
            name="uq_sim_outcome",
        ),
    )
    op.create_index("ix_sim_outcomes_run_id", "sim_outcomes", ["simulation_run_id"])
    op.create_index("ix_sim_outcomes_customer_id", "sim_outcomes", ["customer_id"])


def downgrade() -> None:
    op.drop_table("sim_outcomes")
    op.drop_table("sim_runs")
    op.drop_table("events")
    op.drop_table("payments")
    op.drop_foreign_key("fk_customer_subscription_id", "customers")
    op.drop_table("subscriptions")
    op.drop_table("customers")
