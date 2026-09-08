"""事業PJ台帳: 管理基準日と依存変更の記録

原本00の「管理基準日」と、原本17の依存変更（理由・承認者・承認日）を持たせる。

原本 29/30/31/34/35 と 18/26 の各表は、汎用台帳（venture_ledger_entries）の
行として扱うので新しいテーブルは要らない。列の定義と入力規則は工程マスタ
（venture_process_master.json）が持つ。

Revision ID: 20260907_0003
Revises: 20260906_0002
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260907_0003"
down_revision = "20260906_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 原本00の管理基準日。期限・未来日の点検はすべてこの日付を基準にする。
    op.add_column(
        "ventures",
        sa.Column("as_of_date", sa.String(length=10), nullable=False, server_default=""),
    )
    # 原本17の直接依存ID。標準依存から変えたら理由・承認者・承認日を残す。
    op.add_column(
        "venture_tasks",
        sa.Column("depends_on_override", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column(
        "venture_tasks",
        sa.Column("dependency_change_reason", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column(
        "venture_tasks",
        sa.Column("dependency_change_approved_by", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "venture_tasks",
        sa.Column("dependency_change_approved_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("venture_tasks", "dependency_change_approved_at")
    op.drop_column("venture_tasks", "dependency_change_approved_by")
    op.drop_column("venture_tasks", "dependency_change_reason")
    op.drop_column("venture_tasks", "depends_on_override")
    op.drop_column("ventures", "as_of_date")
