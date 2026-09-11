"""テストは開発用DBを汚さない。

`main` を import した時点で `build_container()` が走り、`DATABASE_URL` の
SQLite に接続する。テストが 132タスクの案件を何件も作るため、既定のままだと
`apps/api/newfan_education.db` に大量の行が残る。import 前に一時ファイルへ
差し替える。
"""
from __future__ import annotations

import os
import tempfile
import subprocess
import sys
from uuid import uuid4
from pathlib import Path

_TEST_DIRECTORY = tempfile.TemporaryDirectory(prefix="newfan-api-tests-")
_TEST_DB = Path(_TEST_DIRECTORY.name) / "test.db"
# Never inherit a developer's or production DATABASE_URL into a destructive test.
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB.as_posix()}"
_pg_admin = None
_pg_database = None
if os.environ.get("TEST_POSTGRES_ADMIN_URL"):
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import make_url
    url = make_url(os.environ["TEST_POSTGRES_ADMIN_URL"])
    if url.host not in {"localhost", "127.0.0.1"} or url.get_backend_name() != "postgresql":
        raise RuntimeError("PostgreSQL tests require a local, isolated server")
    _pg_admin = create_engine(url, isolation_level="AUTOCOMMIT")
    _pg_database = "newfan_test_" + uuid4().hex
    with _pg_admin.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{_pg_database}"'))
    os.environ["DATABASE_URL"] = url.set(database=_pg_database).render_as_string(hide_password=False)
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"],
                   cwd=Path(__file__).parents[1], check=True)


def pytest_sessionfinish(session, exitstatus):
    from infrastructure.db import ScopedSession, engine
    ScopedSession.remove()
    engine.dispose()
    if _pg_admin is not None:
        from sqlalchemy import text
        with _pg_admin.connect() as conn:
            conn.execute(text(f'DROP DATABASE "{_pg_database}"'))
        _pg_admin.dispose()
    _TEST_DIRECTORY.cleanup()
