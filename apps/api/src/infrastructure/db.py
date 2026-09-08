from __future__ import annotations

from contextvars import ContextVar
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, scoped_session, sessionmaker

from infrastructure.settings import load_settings

Base = declarative_base()
_settings = load_settings()
connect_args = {"check_same_thread": False} if _settings.database_url.startswith("sqlite") else {}
engine = create_engine(_settings.database_url, future=True, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)

# リクエストごとにSessionを分ける。
#
# Session はスレッド安全ではないが、FastAPI は `def` のエンドポイントを
# スレッドプールで並行実行する。単一のSessionを共有すると、同時アクセスで
# トランザクションが混線し、1件のDB例外でそのSessionが壊れたまま以後の
# 全リクエストに引き継がれる。
#
# スコープはスレッドIDではなくリクエスト単位のトークンにする。
# エンドポイントはワーカースレッドで動くが、ミドルウェアが設定した
# ContextVar はスレッドプールへコピーされるので、同じ鍵を共有できる。
_session_scope: ContextVar[str] = ContextVar("db_session_scope", default="default")

ScopedSession = scoped_session(SessionLocal, scopefunc=_session_scope.get)


def begin_session_scope() -> object:
    """リクエスト用のスコープを開く。戻り値は `end_session_scope` に渡す。"""
    return _session_scope.set(f"req-{uuid4().hex}")


def end_session_scope(token: object) -> None:
    """スコープのSessionを閉じて捨てる。壊れたSessionを次のリクエストへ持ち越さない。"""
    try:
        ScopedSession.remove()
    finally:
        _session_scope.reset(token)  # type: ignore[arg-type]


def get_db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
