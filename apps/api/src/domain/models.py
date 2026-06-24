from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


Role = Literal["learner", "recruiter", "admin", "content_editor", "mentor"]
NotificationCategory = Literal["learning", "career", "dm", "admin"]
UserState = Literal["active", "invited", "suspended"]


@dataclass(slots=True, frozen=True)
class UserContext:
    user_id: str
    role: Role
    tenant_id: str


@dataclass(slots=True)
class UserAccount:
    user_id: str
    display_name: str
    role: Role
    state: UserState = "active"
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)


@dataclass(slots=True)
class AuditLogEvent:
    event_type: str
    resource_type: str
    resource_id: str
    action: str
    actor_user_id: str
    actor_role: Role
    summary: str
    metadata: dict[str, str] = field(default_factory=dict)
    id: str = field(default_factory=lambda: f"audit-global-{uuid4().hex[:8]}")
    occurred_at: str = field(default_factory=now_iso)


@dataclass(slots=True)
class ConsentRecord:
    user_id: str
    consent_type: Literal["career_profile", "talent_search"]
    granted: bool
    id: str = field(default_factory=lambda: f"consent-{uuid4().hex[:8]}")
    granted_at: str = field(default_factory=now_iso)


@dataclass(slots=True)
class Goal:
    user_id: str
    title: str
    target_role: str
    available_hours_per_week: int
    id: str = field(default_factory=lambda: f"goal-{uuid4().hex[:8]}")
    created_at: str = field(default_factory=now_iso)


@dataclass(slots=True)
class RoadmapItem:
    title: str
    difficulty: int
    estimated_minutes: int
    curriculum_version_id: str
    prerequisite_skill_tags: list[str]
    id: str = field(default_factory=lambda: f"item-{uuid4().hex[:8]}")


@dataclass(slots=True)
class Roadmap:
    user_id: str
    goal_id: str
    items: list[RoadmapItem]
    id: str = field(default_factory=lambda: f"roadmap-{uuid4().hex[:8]}")
    generated_at: str = field(default_factory=now_iso)


@dataclass(slots=True)
class CurriculumVersion:
    curriculum_slug: str
    version: str
    title: str
    mdx_path: str
    skill_tags: list[str]
    difficulty: int
    estimated_minutes: int
    published: bool = True
    id: str = field(default_factory=lambda: f"cv-{uuid4().hex[:8]}")


@dataclass(slots=True)
class ProgressEvent:
    user_id: str
    roadmap_id: str
    roadmap_item_id: str
    event_type: Literal["lesson_started", "lesson_completed"]
    idempotency_key: str
    id: str = field(default_factory=lambda: f"event-{uuid4().hex[:8]}")
    occurred_at: str = field(default_factory=now_iso)


@dataclass(slots=True)
class Company:
    name: str
    industry: str
    status: Literal["active", "stopped"]
    contact_email: str
    contact_person_name: str
    contact_person_phone: str
    id: str = field(default_factory=lambda: f"company-{uuid4().hex[:8]}")
    updated_at: str = field(default_factory=now_iso)


@dataclass(slots=True)
class ModerationCase:
    target_type: Literal["evidence", "submission", "profile"]
    target_id: str
    reason: str
    status: Literal["accepted", "investigating", "acted", "closed"]
    reported_by: str
    assigned_admin: str | None = None
    due_at: str = field(default_factory=now_iso)
    id: str = field(default_factory=lambda: f"mod-{uuid4().hex[:8]}")
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)


@dataclass(slots=True)
class Notification:
    user_id: str
    category: NotificationCategory
    title: str
    body: str
    target_url: str
    is_important: bool = False
    read_at: str | None = None
    id: str = field(default_factory=lambda: f"notification-{uuid4().hex[:8]}")
    created_at: str = field(default_factory=now_iso)


@dataclass(slots=True)
class NotificationDeliverySetting:
    user_id: str
    category: NotificationCategory
    email_enabled: bool
    in_app_enabled: bool
    push_enabled: bool
    updated_at: str = field(default_factory=now_iso)
