"""Verify 0004 -> head migration and backup restoration on disposable databases.

TEST_POSTGRES_ADMIN_URL must address a local test server. PG_BIN optionally points
to the directory containing pg_dump and pg_restore.
"""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

url = make_url(os.environ['TEST_POSTGRES_ADMIN_URL'])
if url.host not in {'127.0.0.1', 'localhost'} or url.get_backend_name() != 'postgresql':
    raise RuntimeError('Use an isolated local PostgreSQL server')
admin = create_engine(url, isolation_level='AUTOCOMMIT')
names = ['newfan_migration_' + uuid4().hex, 'newfan_restore_' + uuid4().hex]
root = Path(__file__).resolve().parents[1]
env = {**os.environ, 'PGHOST': url.host, 'PGPORT': str(url.port or 5432),
       'PGUSER': url.username or 'postgres', 'PGPASSWORD': url.password or ''}

def migrate(name, revision):
    subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', revision], cwd=root,
                   env={**env, 'DATABASE_URL': url.set(database=name).render_as_string(hide_password=False)}, check=True)

def binary(name):
    return str(Path(os.environ['PG_BIN']) / name) if os.environ.get('PG_BIN') else name

created = []
try:
    with admin.connect() as conn:
        for name in names:
            conn.execute(text(f'CREATE DATABASE "{name}"'))
            created.append(name)
    migrate(names[0], '20260911_0004')
    source = create_engine(url.set(database=names[0]))
    with source.begin() as conn:
        conn.execute(text("""INSERT INTO users (user_id,email,display_name,role,state,tenant_id,password_hash)
            VALUES ('migration-user','migration@example.test','移行前の担当者','admin','active','migration-tenant','test-only')"""))
    source.dispose()
    with tempfile.TemporaryDirectory(prefix='newfan-backup-') as folder:
        backup = str(Path(folder) / 'before.dump')
        subprocess.run([binary('pg_dump'), '-Fc', '-f', backup, '-d', names[0]], env=env, check=True)
        migrate(names[0], 'head')
        source = create_engine(url.set(database=names[0]))
        with source.connect() as conn:
            assert conn.execute(text("SELECT display_name,session_version FROM users WHERE user_id='migration-user'")).one() == ('移行前の担当者', 1)
            assert conn.execute(text('SELECT version_num FROM alembic_version')).scalar_one() == '20260911_0005'
        source.dispose()
        subprocess.run([binary('pg_restore'), '--no-owner', '--exit-on-error', '-d', names[1], backup], env=env, check=True)
        restored = create_engine(url.set(database=names[1]))
        with restored.connect() as conn:
            assert conn.execute(text("SELECT display_name FROM users WHERE user_id='migration-user'")).scalar_one() == '移行前の担当者'
            assert conn.execute(text('SELECT version_num FROM alembic_version')).scalar_one() == '20260911_0004'
        restored.dispose()
        migrate(names[1], 'head')
    print('PASS: upgrade from 0004, history retention, pg_dump/pg_restore, re-upgrade')
finally:
    with admin.connect() as conn:
        for name in created:
            conn.execute(text(f'DROP DATABASE "{name}"'))
    admin.dispose()
