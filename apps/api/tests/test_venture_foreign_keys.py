from sqlalchemy import create_engine, event, select, func
from sqlalchemy.orm import Session

from infrastructure.db import Base
from infrastructure.postgres_b2b import PostgresB2BRepository
from infrastructure.postgres_venture import PostgresVentureRepository
from infrastructure.sql_models import VentureTaskModel, VentureGateModel


def test_create_venture_with_foreign_keys_enforced():
    engine = create_engine("sqlite://")

    @event.listens_for(engine, "connect")
    def enforce_foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with Session(engine, autoflush=False) as session:
        PostgresB2BRepository(session).seed_if_empty()
        venture = PostgresVentureRepository(session).create_venture(
            "company-demo", "admin-user", {"name": "Foreign key regression"})
        assert session.scalar(select(func.count()).select_from(VentureTaskModel).where(
            VentureTaskModel.venture_id == venture["id"])) == 132
        assert session.scalar(select(func.count()).select_from(VentureGateModel).where(
            VentureGateModel.venture_id == venture["id"])) == 6
    engine.dispose()
