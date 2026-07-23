from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str
    jwt_secret: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    web_origin: str
    web_origins: tuple[str, ...]
    auth_cookie_name: str
    queue_poll_interval_sec: float
    queue_batch_size: int
    queue_max_retries: int
    docker_sandbox_enabled: bool
    docker_sandbox_image: str
    docker_sandbox_timeout_sec: int


def _parse_web_origins() -> tuple[str, ...]:
    """Allow Docker (:3000) and local Next (:3001) during development."""
    raw = os.getenv("WEB_ORIGINS") or os.getenv(
        "WEB_ORIGIN",
        "http://localhost:3000,http://localhost:3001",
    )
    origins = tuple(origin.strip() for origin in raw.split(",") if origin.strip())
    return origins or ("http://localhost:3000",)


def load_settings() -> Settings:
    docker_sandbox_enabled_raw = os.getenv("DOCKER_SANDBOX_ENABLED", "true").strip().lower()
    web_origins = _parse_web_origins()
    return Settings(
        database_url=os.getenv(
            "DATABASE_URL",
            "sqlite:///./newfan_education.db",
        ),
        jwt_secret=os.getenv("JWT_SECRET", "change-this-in-production"),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        access_token_expire_minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "120")),
        web_origin=web_origins[0],
        web_origins=web_origins,
        auth_cookie_name=os.getenv("AUTH_COOKIE_NAME", "newfan_access_token"),
        queue_poll_interval_sec=float(os.getenv("QUEUE_POLL_INTERVAL_SEC", "1.5")),
        queue_batch_size=int(os.getenv("QUEUE_BATCH_SIZE", "10")),
        queue_max_retries=int(os.getenv("QUEUE_MAX_RETRIES", "3")),
        docker_sandbox_enabled=docker_sandbox_enabled_raw in {"1", "true", "yes", "on"},
        docker_sandbox_image=os.getenv("DOCKER_SANDBOX_IMAGE", "python:3.12-alpine"),
        docker_sandbox_timeout_sec=int(os.getenv("DOCKER_SANDBOX_TIMEOUT_SEC", "8")),
    )
