"""Add risk verification without promoting existing decisions to verified status."""
import sqlalchemy as sa
import hashlib
from alembic import op

revision = "20260911_0004"
down_revision = "20260907_0003"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("ventures", sa.Column("governance", sa.JSON(), nullable=False, server_default="{}"))
    # Preserve the previous normal-screen decisions as unverified source records.
    # Never invent a source URI, signer, risk confirmation or evaluation scope.
    bind = op.get_bind()
    metadata = sa.MetaData()
    old = sa.Table("venture_gates", metadata, autoload_with=bind)
    entries = sa.Table("venture_ledger_entries", metadata, autoload_with=bind)
    for row in bind.execute(sa.select(old)).mappings():
        if row["decision"] == "未審査" and not row["evidence_package_uri"]:
            continue
        identity = "legacy-" + hashlib.sha256(row["id"].encode()).hexdigest()[:24]
        if bind.execute(sa.select(entries.c.id).where(entries.c.id == identity)).first():
            continue
        decided = row["decided_at"]
        values = {"Gate": row["gate_id"], "判断結果": row["decision"], "対象範囲/版": row["scope"],
                  "証拠パッケージURI": row["evidence_package_uri"], "条件・制約": row["conditions"],
                  "条件期限": row["condition_due"], "A実名": row["decided_by_name"],
                  "承認者PersonID": row["decided_by"] or "", "判断日": decided.date().isoformat() if decided else "",
                  "次Gate/Issue": row["next_action"], "再審査トリガー": row["review_trigger"]}
        bind.execute(entries.insert().values(id=identity, venture_id=row["venture_id"], tenant_id=row["tenant_id"],
            ledger_key="gate_run", row_key=identity, is_master_row=False, status="移行・正本未確認", values_json=values,
            updated_by=None, created_at=row["updated_at"], updated_at=row["updated_at"]))


def downgrade():
    op.drop_column("ventures", "governance")
