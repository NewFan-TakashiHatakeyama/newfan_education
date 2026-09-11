"""Small typed repositories backed by the same request-scoped database session."""
from dataclasses import asdict
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from domain.models import Roadmap, RoadmapItem, CurriculumVersion
from infrastructure.sql_models import ApplicationRecordModel, UserModel
from infrastructure.postgres_b2b import PostgresB2BRepository


class PersistentRecords:
    def __init__(self, db, namespace, record_type, initial_values=()):
        self.db, self.namespace, self.record_type = db, namespace, record_type
        # Seed only once, retaining both edits and the identity of curriculum versions.
        if not self.db.scalar(select(ApplicationRecordModel.id).where(ApplicationRecordModel.namespace == namespace).limit(1)):
            import hashlib
            from sqlalchemy.dialects.sqlite import insert as sqlite_insert
            from sqlalchemy.dialects.postgresql import insert as postgres_insert
            insert = postgres_insert if self.db.get_bind().dialect.name == "postgresql" else sqlite_insert
            for value in initial_values:
                if isinstance(value, CurriculumVersion):
                    value.id = "cv-" + hashlib.sha256((value.curriculum_slug + "@" + value.version).encode()).hexdigest()[:24]
                self.db.execute(insert(ApplicationRecordModel).values(namespace=namespace, id=value.id,
                    payload=asdict(value)).on_conflict_do_nothing(index_elements=["namespace", "id"]))
            self.db.commit()

    def _decode(self, row):
        if row is None: return None
        data = dict(row.payload)
        if self.record_type is Roadmap:
            data["items"] = [RoadmapItem(**item) for item in data["items"]]
        return self.record_type(**data)

    def list_all(self):
        rows = self.db.scalars(select(ApplicationRecordModel).where(
            ApplicationRecordModel.namespace == self.namespace).order_by(ApplicationRecordModel.created_at.desc(), ApplicationRecordModel.id)).all()
        return [self._decode(r) for r in rows]

    def get(self, identity):
        return self._decode(self.db.get(ApplicationRecordModel, (self.namespace, identity)))

    def save(self, value):
        identity = value.id
        row = self.db.get(ApplicationRecordModel, (self.namespace, identity))
        if row is None:
            self.db.add(ApplicationRecordModel(namespace=self.namespace, id=identity, payload=asdict(value)))
        else:
            row.payload = asdict(value)
        self.db.commit()
        return value

    def list_by_user(self, user_id):
        return [v for v in self.list_all() if v.user_id == user_id]

    def list_published(self):
        return [v for v in self.list_all() if v.published]

    def get_many(self, identities):
        return [v for v in self.list_all() if v.id in identities]


class PersistentProgress(PersistentRecords):
    def save(self, event):
        # Unique durable idempotency key; duplicate requests cannot add progress twice.
        import hashlib
        key = hashlib.sha256((event.user_id + "\0" + event.idempotency_key).encode()).hexdigest()
        try:
            self.db.add(ApplicationRecordModel(namespace=self.namespace, id=key, payload=asdict(event)))
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            return None
        return event


class PersistentAudit:
    def __init__(self, db):
        self.db = db

    def append(self, value):
        actor = self.db.get(UserModel, value.actor_user_id)
        if actor is None:
            raise ValueError("Audit actor not found")
        PostgresB2BRepository(self.db).append_audit_log(tenant_id=actor.tenant_id,
            **{k: v for k, v in asdict(value).items() if k not in {"id", "occurred_at"}})
        return value

    def list_logs(self, **kwargs):
        raise RuntimeError("Use the tenant-scoped audit API")
