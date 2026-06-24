from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


Role = Literal["learner", "recruiter", "admin", "content_editor", "mentor"]
CourseSort = Literal["popular", "newest", "rating"]
NotificationCategory = Literal["learning", "career", "dm", "admin"]
MessageChannel = Literal["dm", "applications", "teams"]
UserState = Literal["active", "invited", "suspended"]
PublicProfileVisibility = Literal["public", "limited", "private"]


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
class PublicProfileSetting:
    user_id: str
    visibility: PublicProfileVisibility
    show_goal: bool
    show_skill_evidence: bool
    show_portfolio: bool
    allow_recruiter_contact: bool
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


CourseLevel = Literal["beginner", "intermediate", "advanced"]
CourseLessonKind = Literal["reading", "code"]


@dataclass(slots=True)
class CourseLesson:
    """One learnable unit inside a course.

    A lesson is either a `reading` (MDX explainer only) or a `code` lesson that
    binds to an existing :class:`~domain.models` exercise the learner solves in
    the browser. The teaching content lives in an MDX file (`content_ref`).
    """

    lesson_slug: str
    title: str
    kind: CourseLessonKind
    estimated_minutes: int
    skill_tags: list[str] = field(default_factory=list)
    content_ref: str | None = None
    exercise_id: str | None = None
    is_preview: bool = False


@dataclass(slots=True)
class CourseSection:
    title: str
    lessons: list[CourseLesson]


@dataclass(slots=True)
class Course:
    """A catalog course: marketing metadata plus an ordered set of lessons.

    Courses group existing curriculum (MDX) and exercises into a browsable,
    enrollable unit. Phase 1 is browse-only; enrollment/progress arrive later.
    """

    slug: str
    title: str
    subtitle: str
    category: str
    level: CourseLevel
    instructor: str
    summary: str
    description: str
    sections: list[CourseSection]
    tags: list[str] = field(default_factory=list)
    outcomes: list[str] = field(default_factory=list)
    target_audience: list[str] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)
    rating: float = 0.0
    rating_count: int = 0
    enrolled_count: int = 0
    is_bestseller: bool = False
    is_top_rated: bool = False
    published: bool = True
    updated_at: str = field(default_factory=now_iso)
    id: str = field(default_factory=lambda: f"course-{uuid4().hex[:8]}")

    @property
    def lessons(self) -> list[CourseLesson]:
        return [lesson for section in self.sections for lesson in section.lessons]

    @property
    def total_lessons(self) -> int:
        return len(self.lessons)

    @property
    def total_exercises(self) -> int:
        return sum(1 for lesson in self.lessons if lesson.kind == "code")

    @property
    def estimated_minutes(self) -> int:
        return sum(lesson.estimated_minutes for lesson in self.lessons)


@dataclass(slots=True)
class ProgressEvent:
    user_id: str
    roadmap_id: str
    roadmap_item_id: str
    event_type: Literal["lesson_started", "lesson_completed"]
    idempotency_key: str
    id: str = field(default_factory=lambda: f"event-{uuid4().hex[:8]}")
    occurred_at: str = field(default_factory=now_iso)


OpportunityType = Literal["employment", "freelance"]
OpportunityApplicationState = Literal[
    "none",
    "applied",
    "screening",
    "interview",
    "offer",
    "proposed",
    "proposal_review",
    "negotiation",
    "contracted",
]


@dataclass(slots=True)
class Opportunity:
    type: OpportunityType
    title: str
    provider: str
    contract_type: str
    compensation: str
    skill_match_score: int
    caution: str
    summary: str
    required_skills: list[str]
    payment_terms: str
    is_recommended: bool = False
    is_saved: bool = False
    id: str = field(default_factory=lambda: f"opp-{uuid4().hex[:8]}")


@dataclass(slots=True)
class OpportunityApplicationSnapshot:
    user_id: str
    opportunity_id: str
    state: OpportunityApplicationState
    updated_at: str = field(default_factory=now_iso)


@dataclass(slots=True)
class Company:
    name: str
    industry: str
    status: Literal["active", "stopped"]
    open_opportunity_count: int
    contact_email: str
    contact_person_name: str
    contact_person_phone: str
    id: str = field(default_factory=lambda: f"company-{uuid4().hex[:8]}")
    updated_at: str = field(default_factory=now_iso)


@dataclass(slots=True)
class ModerationCase:
    target_type: Literal["message", "portfolio", "profile"]
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
class PortfolioArtifact:
    user_id: str
    title: str
    summary: str
    skill_tags: list[str]
    related_skills: list[str]
    evidence_links: list[str]
    visibility: Literal["private", "limited", "public"]
    evaluation: str
    evaluation_history: list[dict[str, str]]
    id: str = field(default_factory=lambda: f"artifact-{uuid4().hex[:8]}")
    submitted_at: str = field(default_factory=now_iso)


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
class Message:
    thread_id: str
    sender_user_id: str
    body: str
    attachments: list[str]
    id: str = field(default_factory=lambda: f"message-{uuid4().hex[:8]}")
    created_at: str = field(default_factory=now_iso)


@dataclass(slots=True)
class MessageThread:
    owner_user_id: str
    counterpart_name: str
    channel: MessageChannel
    related_opportunity_label: str | None
    can_send: bool
    restriction_reason: str | None
    context_summary: str
    unread_count: int = 0
    id: str = field(default_factory=lambda: f"thread-{uuid4().hex[:8]}")
    updated_at: str = field(default_factory=now_iso)


@dataclass(slots=True)
class MessageTemplate:
    key: str
    label: str
    body: str
    target_roles: list[Role]
    channels: list[MessageChannel]
    id: str = field(default_factory=lambda: f"template-{uuid4().hex[:8]}")


@dataclass(slots=True)
class MessageTemplateAuditLog:
    template_id: str
    action: Literal["create", "update", "delete"]
    actor_user_id: str
    actor_role: Role
    template_key: str
    template_label: str
    id: str = field(default_factory=lambda: f"audit-{uuid4().hex[:8]}")
    occurred_at: str = field(default_factory=now_iso)


@dataclass(slots=True)
class NotificationDeliverySetting:
    user_id: str
    category: NotificationCategory
    email_enabled: bool
    in_app_enabled: bool
    push_enabled: bool
    updated_at: str = field(default_factory=now_iso)
