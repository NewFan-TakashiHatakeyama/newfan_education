from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from infrastructure.settings import load_settings

Base = declarative_base()
_settings = load_settings()
connect_args = {"check_same_thread": False} if _settings.database_url.startswith("sqlite") else {}
engine = create_engine(_settings.database_url, future=True, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)


def get_db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
