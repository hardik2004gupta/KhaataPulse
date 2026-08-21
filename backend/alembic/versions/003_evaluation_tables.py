"""Phase 4: evaluation_runs and evaluation_results tables

Revision ID: 003
Revises: 002
Create Date: 2026-08-21
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── evaluation_runs ───────────────────────────────────────────────────────
    op.create_table(
        "evaluation_runs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.String(100), nullable=False, unique=True),
        sa.Column("seed", sa.Integer, nullable=False),
        sa.Column("cohort_size", sa.Integer, nullable=False),
        sa.Column("simulator_version", sa.String(20), nullable=False),
        sa.Column("model_version", sa.String(50), nullable=False),
        sa.Column("policy_version", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("error_message", sa.String(500), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )
    op.create_index("ix_evaluation_runs_run_id", "evaluation_runs", ["run_id"])
    op.create_index("ix_evaluation_runs_seed", "evaluation_runs", ["seed"])

    # ── evaluation_results ────────────────────────────────────────────────────
    op.create_table(
        "evaluation_results",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "run_id",
            sa.String(100),
            sa.ForeignKey("evaluation_runs.run_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("policy_name", sa.String(50), nullable=False),
        sa.Column("recovered_amount", sa.Numeric(14, 4), nullable=False),
        sa.Column("total_at_risk_amount", sa.Numeric(14, 4), nullable=False),
        sa.Column("incremental_recovery", sa.Numeric(14, 4), nullable=True),
        sa.Column("recovery_rate", sa.Numeric(8, 6), nullable=False),
        sa.Column("contacts_sent", sa.Integer, nullable=False),
        sa.Column("contacts_avoided", sa.Integer, nullable=False),
        sa.Column("human_escalations", sa.Integer, nullable=False),
        sa.Column("false_positives", sa.Integer, nullable=False),
        sa.Column("policy_blocks", sa.Integer, nullable=False),
        sa.Column("cases_evaluated", sa.Integer, nullable=False),
        sa.Column("llm_fallback_count", sa.Integer, nullable=False, server_default="0"),
    )
    op.create_index("ix_evaluation_results_run_id", "evaluation_results", ["run_id"])


def downgrade() -> None:
    op.drop_table("evaluation_results")
    op.drop_table("evaluation_runs")
