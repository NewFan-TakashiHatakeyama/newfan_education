"""事業PJ台帳（Venture Ledger）のテーブルを追加する。

工程マスタ（7工程・6ゲート・132タスク・106スキル）は JSON マスタが正本で、
ここでは案件ごとの台帳だけを保持する。

Revision ID: 20260906_0002
Revises: 20260526_0001
Create Date: 2026-09-06
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260906_0002"
down_revision = "20260526_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ventures",
        sa.Column("id", sa.String(length=80), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("offering_type", sa.String(length=32), nullable=False, server_default="社内事業"),
        sa.Column("industry", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("service_countries", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("processing_countries", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("scale", sa.String(length=8), nullable=False, server_default="S"),
        sa.Column("risk_tier", sa.String(length=8), nullable=False, server_default="T1"),
        sa.Column("risk_tier_rationale", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="計画中"),
        sa.Column("current_phase_id", sa.String(length=8), nullable=False, server_default="B0"),
        sa.Column("business_owner_user_id", sa.String(length=64), nullable=True),
        sa.Column("conditions", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_by", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ventures_tenant_id", "ventures", ["tenant_id"])
    op.create_index("ix_ventures_status", "ventures", ["status"])
    op.create_index("ix_ventures_tenant_status", "ventures", ["tenant_id", "status"])

    op.create_table(
        "venture_tasks",
        sa.Column("id", sa.String(length=80), primary_key=True),
        sa.Column("venture_id", sa.String(length=80), sa.ForeignKey("ventures.id"), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("task_id", sa.String(length=16), nullable=False),
        sa.Column("phase_id", sa.String(length=8), nullable=False),
        sa.Column("gate_id", sa.String(length=8), nullable=False, server_default=""),
        sa.Column("applicability", sa.String(length=16), nullable=False, server_default="未判定"),
        sa.Column("applicability_reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("applicability_decided_by", sa.String(length=64), nullable=True),
        sa.Column("applicability_decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="未着手"),
        sa.Column("assignee_user_id", sa.String(length=64), nullable=True),
        sa.Column("role_id", sa.String(length=8), nullable=False, server_default=""),
        sa.Column("planned_start", sa.String(length=10), nullable=False, server_default=""),
        sa.Column("planned_end", sa.String(length=10), nullable=False, server_default=""),
        sa.Column("actual_start", sa.String(length=10), nullable=False, server_default=""),
        sa.Column("actual_end", sa.String(length=10), nullable=False, server_default=""),
        sa.Column("planned_hours", sa.Integer(), nullable=True),
        sa.Column("actual_hours", sa.Integer(), nullable=True),
        sa.Column("evidence_uri", sa.Text(), nullable=False, server_default=""),
        sa.Column("completion_approved_by", sa.String(length=64), nullable=True),
        sa.Column("completion_approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("blocker", sa.Text(), nullable=False, server_default=""),
        sa.Column("note", sa.Text(), nullable=False, server_default=""),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_venture_tasks_venture_id", "venture_tasks", ["venture_id"])
    op.create_index("ix_venture_tasks_tenant_id", "venture_tasks", ["tenant_id"])
    op.create_index("ix_venture_tasks_task_id", "venture_tasks", ["task_id"])
    op.create_index("ix_venture_tasks_phase_id", "venture_tasks", ["phase_id"])
    op.create_index("ix_venture_tasks_gate_id", "venture_tasks", ["gate_id"])
    op.create_index("ix_venture_tasks_applicability", "venture_tasks", ["applicability"])
    op.create_index("ix_venture_tasks_status", "venture_tasks", ["status"])
    op.create_index("ix_venture_tasks_assignee_user_id", "venture_tasks", ["assignee_user_id"])
    op.create_index("ix_venture_tasks_venture_phase", "venture_tasks", ["venture_id", "phase_id"])
    op.create_index("ux_venture_tasks_venture_task", "venture_tasks", ["venture_id", "task_id"], unique=True)

    op.create_table(
        "venture_gates",
        sa.Column("id", sa.String(length=80), primary_key=True),
        sa.Column("venture_id", sa.String(length=80), sa.ForeignKey("ventures.id"), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("gate_id", sa.String(length=8), nullable=False),
        sa.Column("decision", sa.String(length=32), nullable=False, server_default="未審査"),
        sa.Column("scope", sa.Text(), nullable=False, server_default=""),
        sa.Column("evidence_package_uri", sa.Text(), nullable=False, server_default=""),
        sa.Column("conditions", sa.Text(), nullable=False, server_default=""),
        sa.Column("condition_due", sa.String(length=10), nullable=False, server_default=""),
        sa.Column("decided_by", sa.String(length=64), nullable=True),
        sa.Column("decided_by_name", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_action", sa.Text(), nullable=False, server_default=""),
        sa.Column("review_trigger", sa.Text(), nullable=False, server_default=""),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_venture_gates_venture_id", "venture_gates", ["venture_id"])
    op.create_index("ix_venture_gates_tenant_id", "venture_gates", ["tenant_id"])
    op.create_index("ix_venture_gates_gate_id", "venture_gates", ["gate_id"])
    op.create_index("ix_venture_gates_decision", "venture_gates", ["decision"])
    op.create_index("ux_venture_gates_venture_gate", "venture_gates", ["venture_id", "gate_id"], unique=True)

    op.create_table(
        "venture_members",
        sa.Column("id", sa.String(length=80), primary_key=True),
        sa.Column("venture_id", sa.String(length=80), sa.ForeignKey("ventures.id"), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("role_id", sa.String(length=8), nullable=False),
        sa.Column("allocation_note", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_venture_members_venture_id", "venture_members", ["venture_id"])
    op.create_index("ix_venture_members_tenant_id", "venture_members", ["tenant_id"])
    op.create_index("ix_venture_members_user_id", "venture_members", ["user_id"])
    op.create_index("ix_venture_members_role_id", "venture_members", ["role_id"])
    op.create_index(
        "ux_venture_members_venture_user_role", "venture_members", ["venture_id", "user_id", "role_id"], unique=True
    )

    op.create_table(
        "venture_ledger_entries",
        sa.Column("id", sa.String(length=80), primary_key=True),
        sa.Column("venture_id", sa.String(length=80), sa.ForeignKey("ventures.id"), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("ledger_key", sa.String(length=32), nullable=False),
        sa.Column("row_key", sa.String(length=64), nullable=False),
        sa.Column("is_master_row", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="未着手"),
        sa.Column("values_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("updated_by", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_venture_ledger_entries_venture_id", "venture_ledger_entries", ["venture_id"])
    op.create_index("ix_venture_ledger_entries_tenant_id", "venture_ledger_entries", ["tenant_id"])
    op.create_index("ix_venture_ledger_entries_ledger_key", "venture_ledger_entries", ["ledger_key"])
    op.create_index("ix_venture_ledger_entries_row_key", "venture_ledger_entries", ["row_key"])
    op.create_index("ix_venture_ledger_entries_status", "venture_ledger_entries", ["status"])
    op.create_index(
        "ux_venture_ledger_row", "venture_ledger_entries", ["venture_id", "ledger_key", "row_key"], unique=True
    )

    op.create_table(
        "venture_skill_assessments",
        sa.Column("id", sa.String(length=80), primary_key=True),
        sa.Column("venture_id", sa.String(length=80), sa.ForeignKey("ventures.id"), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("skill_id", sa.String(length=16), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("assessed_level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("evidence_uri", sa.Text(), nullable=False, server_default=""),
        sa.Column("development_plan", sa.Text(), nullable=False, server_default=""),
        sa.Column("due_date", sa.String(length=10), nullable=False, server_default=""),
        sa.Column("assessed_by", sa.String(length=64), nullable=True),
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_venture_skill_assessments_venture_id", "venture_skill_assessments", ["venture_id"])
    op.create_index("ix_venture_skill_assessments_tenant_id", "venture_skill_assessments", ["tenant_id"])
    op.create_index("ix_venture_skill_assessments_skill_id", "venture_skill_assessments", ["skill_id"])
    op.create_index("ix_venture_skill_assessments_user_id", "venture_skill_assessments", ["user_id"])
    op.create_index(
        "ux_venture_skill_user", "venture_skill_assessments", ["venture_id", "skill_id", "user_id"], unique=True
    )


def downgrade() -> None:
    op.drop_table("venture_skill_assessments")
    op.drop_table("venture_ledger_entries")
    op.drop_table("venture_members")
    op.drop_table("venture_gates")
    op.drop_table("venture_tasks")
    op.drop_table("ventures")
