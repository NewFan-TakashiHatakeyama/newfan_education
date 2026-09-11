import pytest

from infrastructure.postgres_b2b import _seed_password


def test_production_refuses_public_bootstrap_password(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("BOOTSTRAP_ADMIN_PASSWORD", raising=False)
    with pytest.raises(RuntimeError):
        _seed_password("admin", "Admin123!")
    monkeypatch.setenv("BOOTSTRAP_ADMIN_PASSWORD", "x" * 32)
    assert _seed_password("admin", "Admin123!") == "x" * 32
    passwords = [_seed_password("learner", "Learner123!") for _ in range(2)]
    assert passwords[0] != passwords[1]
    assert all(len(password) >= 32 and password != "Learner123!" for password in passwords)
