from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

from infrastructure.db import SessionLocal
from infrastructure.postgres_b2b import PostgresB2BRepository
from infrastructure.settings import load_settings


def _now() -> datetime:
    return datetime.now(timezone.utc)


def run_worker() -> None:
    settings = load_settings()
    print("notification-worker: started", flush=True)
    while True:
        session = SessionLocal()
        try:
            repo = PostgresB2BRepository(session)
            jobs = repo.reserve_notification_jobs(limit=settings.queue_batch_size)
            if not jobs:
                time.sleep(settings.queue_poll_interval_sec)
                continue

            for job in jobs:
                try:
                    delivered_channels: list[str] = []
                    channels = job.get("channels", ["in_app"])

                    if "in_app" in channels:
                        repo.create_in_app_notification(
                            tenant_id=job["tenantId"],
                            user_id=job["userId"],
                            category=job["category"],
                            title=job["title"],
                            body=job["body"],
                            target_url=job["targetUrl"],
                            is_important=job["isImportant"],
                        )
                        delivered_channels.append("in_app")

                    # Extendable hooks for future real dispatch providers.
                    if "email" in channels:
                        delivered_channels.append("email")
                    if "push" in channels:
                        delivered_channels.append("push")

                    repo.mark_notification_job_completed(
                        job_id=job["id"],
                        result={
                            "deliveredChannels": delivered_channels,
                            "processedAt": _now().isoformat(),
                        },
                    )
                except Exception as exc:  # noqa: BLE001
                    retry_delay_sec = 2 ** int(job["attemptCount"])
                    next_retry_at = _now() + timedelta(seconds=retry_delay_sec)
                    repo.mark_notification_job_failed(
                        job_id=job["id"],
                        error_message=str(exc),
                        max_retries=settings.queue_max_retries,
                        next_retry_at=next_retry_at,
                    )
        finally:
            session.close()


if __name__ == "__main__":
    run_worker()
