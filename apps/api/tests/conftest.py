"""テストは開発用DBを汚さない。

`main` を import した時点で `build_container()` が走り、`DATABASE_URL` の
SQLite に接続する。テストが 132タスクの案件を何件も作るため、既定のままだと
`apps/api/newfan_education.db` に大量の行が残る。import 前に一時ファイルへ
差し替える。
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

_TEST_DB = Path(tempfile.gettempdir()) / "newfan_education_test.db"
if _TEST_DB.exists():
    _TEST_DB.unlink()
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_TEST_DB.as_posix()}")
