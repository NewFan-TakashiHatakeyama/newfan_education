"""Read-only membership inventory. Requires an explicitly selected database.

Never infer that historical self-registration is legitimate. Existing users
without invitation evidence require review by the tenant's responsible admin.
"""
import json
import os
import sys
from pathlib import Path

if not os.environ.get("DATABASE_URL"):
    raise SystemExit("Set DATABASE_URL explicitly to the database to inspect")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from sqlalchemy import select
from infrastructure.db import SessionLocal
from infrastructure.sql_models import UserModel, AuditLogModel


def main():
    with SessionLocal() as db:
        accepted = {a.resource_id: a for a in db.scalars(select(AuditLogModel).where(
            AuditLogModel.event_type == "auth.invite.accepted")).all()}
        items = []
        for user in db.scalars(select(UserModel).order_by(UserModel.tenant_id, UserModel.user_id)).all():
            evidence = accepted.get(user.user_id)
            items.append({"userId": user.user_id, "email": user.email, "tenantId": user.tenant_id,
                "role": user.role, "state": user.state, "createdAt": str(user.created_at),
                "membershipEvidence": evidence.id if evidence else None,
                "reviewRequired": evidence is None})
        print(json.dumps({"items": items}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
