from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone

from application.ports import (
    AuditLogRepository,
    CompanyRepository,
    ConsentRepository,
    CourseRepository,
    CurriculumRepository,
    GoalRepository,
    NotificationDeliverySettingRepository,
    NotificationRepository,
    ModerationRepository,
    ProgressRepository,
    RoadmapRepository,
    UserRepository,
)
from domain.models import (
    AuditLogEvent,
    Company,
    ConsentRecord,
    CurriculumVersion,
    Goal,
    ModerationCase,
    Notification,
    ProgressEvent,
    Roadmap,
    RoadmapItem,
    UserAccount,
    UserContext,
    now_iso,
)


def _parse_iso_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


class ConsentService:
    def __init__(self, repository: ConsentRepository) -> None:
        self._repository = repository

    def create(self, actor: UserContext, consent_type: str, granted: bool) -> ConsentRecord:
        consent = ConsentRecord(
            user_id=actor.user_id,
            consent_type=consent_type,  # type: ignore[arg-type]
            granted=granted,
        )
        return self._repository.save(consent)

    def list_mine(self, actor: UserContext) -> list[ConsentRecord]:
        return self._repository.list_by_user(actor.user_id)


class GoalService:
    def __init__(self, repository: GoalRepository) -> None:
        self._repository = repository

    def create(
        self,
        actor: UserContext,
        title: str,
        target_role: str,
        available_hours_per_week: int,
    ) -> Goal:
        goal = Goal(
            user_id=actor.user_id,
            title=title,
            target_role=target_role,
            available_hours_per_week=available_hours_per_week,
        )
        return self._repository.save(goal)

    def get(self, goal_id: str) -> Goal | None:
        return self._repository.get(goal_id)

    def list_mine(self, actor: UserContext) -> list[Goal]:
        return self._repository.list_by_user(actor.user_id)


class CurriculumService:
    def __init__(self, repository: CurriculumRepository) -> None:
        self._repository = repository

    def list_published(self) -> list[CurriculumVersion]:
        return self._repository.list_published()

    def get(self, curriculum_version_id: str) -> CurriculumVersion | None:
        return self._repository.get(curriculum_version_id)

    def publish(
        self,
        actor: UserContext,
        curriculum_slug: str,
        version: str,
        title: str,
        mdx_path: str,
        skill_tags: list[str],
        difficulty: int,
        estimated_minutes: int,
    ) -> CurriculumVersion:
        if actor.role not in {"content_editor", "admin"}:
            raise PermissionError("Only content editor can publish curriculum")
        curriculum_version = CurriculumVersion(
            curriculum_slug=curriculum_slug,
            version=version,
            title=title,
            mdx_path=mdx_path,
            skill_tags=skill_tags,
            difficulty=difficulty,
            estimated_minutes=estimated_minutes,
            published=True,
        )
        return self._repository.save(curriculum_version)


class CourseService:
    """Read-only catalog of courses for browsing, searching and detail view.

    Phase 1 only covers discovery: list with search/filter/sort, category
    facets, trending terms and per-course detail (sections + lessons).
    """

    def __init__(self, repository: CourseRepository) -> None:
        self._repository = repository

    def list_courses(
        self,
        *,
        query: str | None = None,
        category: str | None = None,
        level: str | None = None,
        sort: str = "popular",
    ) -> list[Course]:
        courses = self._repository.list_published()

        if query:
            needle = query.strip().lower()
            if needle:
                courses = [course for course in courses if self._matches(course, needle)]

        if category:
            courses = [course for course in courses if course.category == category]

        if level:
            courses = [course for course in courses if course.level == level]

        return self._sort(courses, sort)

    def get_course(self, slug: str) -> Course | None:
        return self._repository.get_by_slug(slug)

    def list_categories(self) -> list[tuple[str, int]]:
        counts: dict[str, int] = {}
        order: list[str] = []
        for course in self._repository.list_published():
            if course.category not in counts:
                counts[course.category] = 0
                order.append(course.category)
            counts[course.category] += 1
        return [(category, counts[category]) for category in order]

    def list_trending(self) -> list[str]:
        seen: list[str] = []
        for course in self._sort(self._repository.list_published(), "popular"):
            for tag in course.tags:
                if tag not in seen:
                    seen.append(tag)
        return seen[:8]

    @staticmethod
    def _matches(course: Course, needle: str) -> bool:
        haystack = " ".join(
            [
                course.title,
                course.subtitle,
                course.summary,
                course.category,
                " ".join(course.tags),
                " ".join(course.outcomes),
            ]
        ).lower()
        return needle in haystack

    @staticmethod
    def _sort(courses: list[Course], sort: str) -> list[Course]:
        if sort == "rating":
            return sorted(courses, key=lambda course: course.rating, reverse=True)
        if sort == "newest":
            return sorted(courses, key=lambda course: course.updated_at, reverse=True)
        # default: popular
        return sorted(courses, key=lambda course: course.enrolled_count, reverse=True)


class RoadmapService:
    def __init__(
        self,
        goal_repository: GoalRepository,
        roadmap_repository: RoadmapRepository,
        curriculum_repository: CurriculumRepository,
    ) -> None:
        self._goal_repository = goal_repository
        self._roadmap_repository = roadmap_repository
        self._curriculum_repository = curriculum_repository

    def generate(self, actor: UserContext, goal_id: str, preferred_difficulty: int) -> Roadmap:
        goal = self._goal_repository.get(goal_id)
        if goal is None:
            raise ValueError("Goal not found")
        if goal.user_id != actor.user_id:
            raise PermissionError("Cannot generate roadmap for other users")

        candidates = sorted(
            self._curriculum_repository.list_published(),
            key=lambda c: abs(c.difficulty - preferred_difficulty),
        )
        top_candidates = candidates[:3]
        items = [
            RoadmapItem(
                title=candidate.title,
                difficulty=candidate.difficulty,
                estimated_minutes=candidate.estimated_minutes,
                curriculum_version_id=candidate.id,
                prerequisite_skill_tags=candidate.skill_tags,
            )
            for candidate in top_candidates
        ]
        roadmap = Roadmap(
            user_id=actor.user_id,
            goal_id=goal_id,
            items=items,
        )
        return self._roadmap_repository.save(roadmap)

    def get(self, actor: UserContext, roadmap_id: str) -> Roadmap:
        roadmap = self._roadmap_repository.get(roadmap_id)
        if roadmap is None:
            raise ValueError("Roadmap not found")
        if roadmap.user_id != actor.user_id:
            raise PermissionError("Cannot access another user's roadmap")
        return roadmap

    def list_mine(self, actor: UserContext) -> list[Roadmap]:
        return self._roadmap_repository.list_by_user(actor.user_id)


class ProgressService:
    def __init__(
        self,
        progress_repository: ProgressRepository,
        roadmap_repository: RoadmapRepository,
    ) -> None:
        self._progress_repository = progress_repository
        self._roadmap_repository = roadmap_repository

    def track(
        self,
        actor: UserContext,
        roadmap_id: str,
        roadmap_item_id: str,
        event_type: str,
        idempotency_key: str,
    ) -> bool:
        roadmap = self._roadmap_repository.get(roadmap_id)
        if roadmap is None:
            raise ValueError("Roadmap not found")
        if roadmap.user_id != actor.user_id:
            raise PermissionError("Cannot update another user's progress")
        event = ProgressEvent(
            user_id=actor.user_id,
            roadmap_id=roadmap_id,
            roadmap_item_id=roadmap_item_id,
            event_type=event_type,  # type: ignore[arg-type]
            idempotency_key=idempotency_key,
        )
        saved = self._progress_repository.save(event)
        return saved is not None

    def dashboard(self, actor: UserContext) -> dict:
        roadmaps = self._roadmap_repository.list_by_user(actor.user_id)
        total_items = sum(len(roadmap.items) for roadmap in roadmaps)
        events = self._progress_repository.list_by_user(actor.user_id)
        completed_items = len([event for event in events if event.event_type == "lesson_completed"])
        completion_rate = (completed_items / total_items) if total_items else 0.0
        return {
            "userId": actor.user_id,
            "completedItems": completed_items,
            "totalItems": total_items,
            "completionRate": completion_rate,
            "recentEvents": [asdict(event) for event in events[:10]],
        }


class SkillGapService:
    def __init__(
        self,
        goal_repository: GoalRepository,
        roadmap_repository: RoadmapRepository,
        progress_repository: ProgressRepository,
    ) -> None:
        self._goal_repository = goal_repository
        self._roadmap_repository = roadmap_repository
        self._progress_repository = progress_repository

    def get_gap(self, actor: UserContext) -> dict:
        goals = self._goal_repository.list_by_user(actor.user_id)
        current_goal = goals[0] if goals else None
        roadmaps = self._roadmap_repository.list_by_user(actor.user_id)
        latest_roadmap = roadmaps[0] if roadmaps else None
        events = self._progress_repository.list_by_user(actor.user_id)

        # Minimal deterministic profile until dedicated skill assessment is introduced.
        base_skills = [
            {
                "id": "ai-dx-foundation",
                "name": "AI/DX基礎",
                "targetLevel": 3,
                "isCareerVisible": True,
                "evidenceLink": "/learn/afr-enterprise-ai-dx-foundation/main",
            },
            {
                "id": "business-issue",
                "name": "業務課題定義",
                "targetLevel": 3,
                "isCareerVisible": True,
                "evidenceLink": "/learn/afr-enterprise-business-issue-definition/main",
            },
            {
                "id": "rag-verification",
                "name": "RAG/ナレッジ活用",
                "targetLevel": 3,
                "isCareerVisible": True,
                "evidenceLink": "/learn/afr-enterprise-rag-verification/main",
            },
            {
                "id": "poc-planning",
                "name": "PoC計画",
                "targetLevel": 3,
                "isCareerVisible": True,
                "evidenceLink": "/learn/afr-enterprise-poc-planning/main",
            },
            {
                "id": "ai-governance",
                "name": "AIガバナンス",
                "targetLevel": 2,
                "isCareerVisible": False,
                "evidenceLink": "/learn/afr-enterprise-ai-governance-foundation/main",
            },
            {
                "id": "project-proposal",
                "name": "AIプロジェクト提案",
                "targetLevel": 3,
                "isCareerVisible": True,
                "evidenceLink": "/learn/afr-enterprise-project-proposal/main",
            },
        ]

        completed_count = len([event for event in events if event.event_type == "lesson_completed"])
        current_by_skill = {
            "ai-dx-foundation": 1 + min(completed_count, 2),
            "business-issue": 1 + min(completed_count // 2, 2),
            "rag-verification": min(completed_count // 2, 2),
            "poc-planning": min(completed_count // 3, 2),
            "ai-governance": min(completed_count // 4, 2),
            "project-proposal": min(completed_count // 3, 2),
        }
        evidence_by_skill = {
            "ai-dx-foundation": max(1, completed_count),
            "business-issue": max(1, completed_count // 2),
            "rag-verification": max(1, completed_count // 2),
            "poc-planning": max(1, completed_count // 3),
            "ai-governance": max(1, completed_count // 4),
            "project-proposal": max(1, completed_count // 3),
        }

        items: list[dict] = []
        for skill in base_skills:
            current = current_by_skill[skill["id"]]
            target = skill["targetLevel"]
            gap_score = max(target - current, 0)
            items.append(
                {
                    **skill,
                    "currentLevel": current,
                    "evidenceCount": evidence_by_skill[skill["id"]],
                    "gapScore": gap_score,
                }
            )

        items.sort(key=lambda item: item["gapScore"], reverse=True)

        total_target = sum(item["targetLevel"] for item in items)
        total_current = sum(min(item["currentLevel"], item["targetLevel"]) for item in items)
        attainment_rate = round((total_current / total_target) * 100) if total_target else 0

        return {
            "userId": actor.user_id,
            "targetRole": current_goal.target_role if current_goal else "Backend Engineer",
            "attainmentRate": attainment_rate,
            "lastUpdatedAt": (latest_roadmap.generated_at if latest_roadmap else "N/A"),
            "items": items,
        }


class CompanyService:
    def __init__(
        self,
        repository: CompanyRepository,
        audit_log_repository: AuditLogRepository | None = None,
    ) -> None:
        self._repository = repository
        self._audit_log_repository = audit_log_repository

    def list_companies(self, actor: UserContext) -> dict:
        if actor.role != "admin":
            raise PermissionError("Only admin can manage companies")
        values = self._repository.list_all()
        return {
            "items": [
                {
                    "id": value.id,
                    "name": value.name,
                    "industry": value.industry,
                    "status": value.status,
                    "contactEmail": value.contact_email,
                    "contactPersonName": value.contact_person_name,
                    "contactPersonPhone": value.contact_person_phone,
                    "updatedAt": value.updated_at,
                }
                for value in values
            ]
        }

    def update_company(
        self,
        actor: UserContext,
        company_id: str,
        status: str | None = None,
        contact_person_name: str | None = None,
        contact_person_phone: str | None = None,
    ) -> dict:
        if actor.role != "admin":
            raise PermissionError("Only admin can manage companies")
        if status is None and contact_person_name is None and contact_person_phone is None:
            raise ValueError("At least one field is required for update")
        if status is not None and status not in {"active", "stopped"}:
            raise ValueError("Invalid company status")
        current = self._repository.get(company_id)
        if current is None:
            raise ValueError("Company not found")
        saved = self._repository.save(
            Company(
                id=current.id,
                name=current.name,
                industry=current.industry,
                status=status if status is not None else current.status,  # type: ignore[arg-type]
                contact_email=current.contact_email,
                contact_person_name=(
                    contact_person_name if contact_person_name is not None else current.contact_person_name
                ),
                contact_person_phone=(
                    contact_person_phone if contact_person_phone is not None else current.contact_person_phone
                ),
                updated_at=now_iso(),
            )
        )
        if self._audit_log_repository is not None:
            self._audit_log_repository.append(
                AuditLogEvent(
                    event_type="admin.company.updated",
                    resource_type="company",
                    resource_id=saved.id,
                    action="update",
                    actor_user_id=actor.user_id,
                    actor_role=actor.role,
                    summary="管理者が企業情報を更新",
                    metadata={
                        "status": saved.status,
                        "contactPersonName": saved.contact_person_name,
                    },
                )
            )
        return {
            "id": saved.id,
            "name": saved.name,
            "industry": saved.industry,
            "status": saved.status,
            "contactEmail": saved.contact_email,
            "contactPersonName": saved.contact_person_name,
            "contactPersonPhone": saved.contact_person_phone,
            "updatedAt": saved.updated_at,
        }

    def bulk_update_status(
        self,
        actor: UserContext,
        company_ids: list[str],
        status: str,
    ) -> dict:
        if actor.role != "admin":
            raise PermissionError("Only admin can manage companies")
        if status not in {"active", "stopped"}:
            raise ValueError("Invalid company status")
        requested_ids = list(dict.fromkeys(company_ids))
        targets = {value.id: value for value in self._repository.get_many(requested_ids)}
        updated_ids: list[str] = []
        skipped_ids: list[str] = []
        for company_id in requested_ids:
            current = targets.get(company_id)
            if current is None:
                skipped_ids.append(company_id)
                continue
            saved = self._repository.save(
                Company(
                    id=current.id,
                    name=current.name,
                    industry=current.industry,
                    status=status,  # type: ignore[arg-type]
                    contact_email=current.contact_email,
                    contact_person_name=current.contact_person_name,
                    contact_person_phone=current.contact_person_phone,
                    updated_at=now_iso(),
                )
            )
            updated_ids.append(saved.id)
            if self._audit_log_repository is not None:
                self._audit_log_repository.append(
                    AuditLogEvent(
                        event_type="admin.company.updated",
                        resource_type="company",
                        resource_id=saved.id,
                        action="bulk_update_status",
                        actor_user_id=actor.user_id,
                        actor_role=actor.role,
                        summary="管理者が企業ステータスを一括更新",
                        metadata={"status": saved.status},
                    )
                )
        return {
            "updatedCompanyIds": updated_ids,
            "skippedCompanyIds": skipped_ids,
            "status": status,
        }


class ModerationService:
    def __init__(
        self,
        repository: ModerationRepository,
        audit_log_repository: AuditLogRepository | None = None,
    ) -> None:
        self._repository = repository
        self._audit_log_repository = audit_log_repository

    def list_cases(
        self,
        actor: UserContext,
        pending_only: bool = False,
        overdue_only: bool = False,
    ) -> dict:
        if actor.role != "admin":
            raise PermissionError("Only admin can manage moderation")
        values = self._repository.list_all()
        if pending_only:
            values = [value for value in values if value.status in {"accepted", "investigating"}]
        if overdue_only:
            values = [value for value in values if self._is_overdue(value)]
        values.sort(key=lambda value: value.updated_at, reverse=True)
        return {
            "items": [self._to_response(value) for value in values],
        }

    def update_case(
        self,
        actor: UserContext,
        case_id: str,
        status: str,
        assigned_admin: str | None = None,
    ) -> dict:
        if actor.role != "admin":
            raise PermissionError("Only admin can manage moderation")
        current = self._repository.get(case_id)
        if current is None:
            raise ValueError("Moderation case not found")
        status = self._resolve_transition(current.status, status)
        updated = ModerationCase(
            id=current.id,
            target_type=current.target_type,
            target_id=current.target_id,
            reason=current.reason,
            status=status,  # type: ignore[arg-type]
            reported_by=current.reported_by,
            assigned_admin=assigned_admin if assigned_admin is not None else current.assigned_admin,
            due_at=current.due_at,
            created_at=current.created_at,
            updated_at=now_iso(),
        )
        saved = self._repository.save(updated)
        if self._audit_log_repository is not None:
            self._audit_log_repository.append(
                AuditLogEvent(
                    event_type="admin.moderation.updated",
                    resource_type="moderation_case",
                    resource_id=saved.id,
                    action="update",
                    actor_user_id=actor.user_id,
                    actor_role=actor.role,
                    summary="管理者がモデレーション対応を更新",
                    metadata={"status": saved.status},
                )
            )
        return self._to_response(saved)

    def bulk_close(
        self,
        actor: UserContext,
        case_ids: list[str],
        assigned_admin: str | None = None,
    ) -> dict:
        if actor.role != "admin":
            raise PermissionError("Only admin can manage moderation")
        requested_ids = list(dict.fromkeys(case_ids))
        targets = {value.id: value for value in self._repository.get_many(requested_ids)}
        closed_case_ids: list[str] = []
        skipped_case_ids: list[str] = []
        for case_id in requested_ids:
            current = targets.get(case_id)
            if current is None:
                skipped_case_ids.append(case_id)
                continue
            if current.status == "closed":
                skipped_case_ids.append(case_id)
                continue
            updated = ModerationCase(
                id=current.id,
                target_type=current.target_type,
                target_id=current.target_id,
                reason=current.reason,
                status="closed",
                reported_by=current.reported_by,
                assigned_admin=assigned_admin if assigned_admin is not None else current.assigned_admin,
                due_at=current.due_at,
                created_at=current.created_at,
                updated_at=now_iso(),
            )
            saved = self._repository.save(updated)
            closed_case_ids.append(saved.id)
            if self._audit_log_repository is not None:
                self._audit_log_repository.append(
                    AuditLogEvent(
                        event_type="admin.moderation.updated",
                        resource_type="moderation_case",
                        resource_id=saved.id,
                        action="bulk_close",
                        actor_user_id=actor.user_id,
                        actor_role=actor.role,
                        summary="管理者がモデレーションを一括クローズ",
                        metadata={"status": saved.status},
                    )
                )
        return {"closedCaseIds": closed_case_ids, "skippedCaseIds": skipped_case_ids}

    def _to_response(self, value: ModerationCase) -> dict:
        return {
            "id": value.id,
            "targetType": value.target_type,
            "targetId": value.target_id,
            "reason": value.reason,
            "status": value.status,
            "reportedBy": value.reported_by,
            "assignedAdmin": value.assigned_admin,
            "dueAt": value.due_at,
            "isOverdue": self._is_overdue(value),
            "createdAt": value.created_at,
            "updatedAt": value.updated_at,
        }

    def _resolve_transition(self, current_status: str, requested_status: str) -> str:
        ordered = ["accepted", "investigating", "acted", "closed"]
        if requested_status not in ordered:
            raise ValueError("Invalid moderation status")
        if current_status not in ordered:
            return requested_status
        if ordered.index(requested_status) < ordered.index(current_status):
            raise ValueError("Cannot move moderation status backward")
        return requested_status

    def _is_overdue(self, value: ModerationCase) -> bool:
        if value.status == "closed":
            return False
        due = datetime.fromisoformat(value.due_at.replace("Z", "+00:00"))
        return due < datetime.now(timezone.utc)


class CurriculumImpactService:
    def __init__(self, roadmap_repository: RoadmapRepository) -> None:
        self._roadmap_repository = roadmap_repository

    def analyze(self, curriculum_version_id: str) -> dict:
        roadmaps = self._roadmap_repository.list_all()
        affected_roadmaps = [
            roadmap
            for roadmap in roadmaps
            if any(item.curriculum_version_id == curriculum_version_id for item in roadmap.items)
        ]
        affected_user_ids = sorted({roadmap.user_id for roadmap in affected_roadmaps})
        affected_roadmap_ids = [roadmap.id for roadmap in affected_roadmaps]

        # Notification targets: affected learners + one admin recipient.
        notification_user_ids = [*affected_user_ids, "admin-user"]
        return {
            "curriculumVersionId": curriculum_version_id,
            "affectedRoadmapCount": len(affected_roadmap_ids),
            "affectedRoadmapIds": affected_roadmap_ids,
            "affectedUserCount": len(affected_user_ids),
            "affectedUserIds": affected_user_ids,
            "notificationTargetCount": len(notification_user_ids),
            "notificationUserIds": notification_user_ids,
        }


class NotificationService:
    def __init__(
        self,
        repository: NotificationRepository,
        delivery_setting_repository: NotificationDeliverySettingRepository,
    ) -> None:
        self._repository = repository
        self._delivery_setting_repository = delivery_setting_repository
        self._categories = ["learning", "career", "dm", "admin"]

    def list_mine(self, actor: UserContext, tab: str = "all", unread_only: bool = False) -> dict:
        values = self._repository.list_by_user(actor.user_id)
        if tab != "all":
            values = [value for value in values if value.category == tab]
        if unread_only:
            values = [value for value in values if value.read_at is None]
        unread_count = len([value for value in self._repository.list_by_user(actor.user_id) if value.read_at is None])
        return {
            "userId": actor.user_id,
            "unreadCount": unread_count,
            "items": [
                {
                    "id": value.id,
                    "category": value.category,
                    "title": value.title,
                    "body": value.body,
                    "targetUrl": value.target_url,
                    "isImportant": value.is_important,
                    "readAt": value.read_at,
                    "createdAt": value.created_at,
                }
                for value in values
            ],
        }

    def mark_read(self, actor: UserContext, notification_id: str) -> dict:
        updated = self._repository.mark_read(actor.user_id, notification_id)
        if updated is None:
            raise ValueError("Notification not found")
        return {
            "id": updated.id,
            "readAt": updated.read_at,
        }

    def mark_all_read(self, actor: UserContext) -> dict:
        updated_count = self._repository.mark_all_read(actor.user_id)
        return {"updatedCount": updated_count}

    def list_delivery_settings(self, actor: UserContext) -> dict:
        values = self._delivery_setting_repository.list_by_user(actor.user_id)
        by_category = {value.category: value for value in values}
        items: list[dict] = []
        for category in self._categories:
            value = by_category.get(category)
            items.append(
                {
                    "category": category,
                    "emailEnabled": value.email_enabled if value is not None else False,
                    "inAppEnabled": value.in_app_enabled if value is not None else True,
                    "pushEnabled": value.push_enabled if value is not None else False,
                    "updatedAt": value.updated_at if value is not None else None,
                }
            )
        return {"userId": actor.user_id, "items": items}

    def update_delivery_setting(
        self,
        actor: UserContext,
        category: str,
        email_enabled: bool,
        in_app_enabled: bool,
        push_enabled: bool,
    ) -> dict:
        if category not in self._categories:
            raise ValueError("Unsupported notification category")
        value = self._delivery_setting_repository.upsert_by_user(
            user_id=actor.user_id,
            category=category,
            email_enabled=email_enabled,
            in_app_enabled=in_app_enabled,
            push_enabled=push_enabled,
        )
        return {
            "category": value.category,
            "emailEnabled": value.email_enabled,
            "inAppEnabled": value.in_app_enabled,
            "pushEnabled": value.push_enabled,
            "updatedAt": value.updated_at,
        }


class AuthService:
    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    def sign_in(self, user_id: str, role: str) -> dict:
        existing = self._user_repository.get(user_id)
        if existing is not None:
            if existing.role != role:
                existing = UserAccount(
                    user_id=existing.user_id,
                    display_name=existing.display_name,
                    role=role,  # type: ignore[arg-type]
                    state=existing.state,
                    created_at=existing.created_at,
                    updated_at=now_iso(),
                )
                self._user_repository.save(existing)
            return self._to_session(existing)
        created = UserAccount(
            user_id=user_id,
            display_name=user_id,
            role=role,  # type: ignore[arg-type]
            state="active",
        )
        self._user_repository.save(created)
        return self._to_session(created)

    def sign_up(self, user_id: str, display_name: str, role: str) -> dict:
        created = UserAccount(
            user_id=user_id,
            display_name=display_name,
            role=role,  # type: ignore[arg-type]
            state="active",
        )
        self._user_repository.save(created)
        return self._to_session(created)

    def _to_session(self, user: UserAccount) -> dict:
        return {
            "userId": user.user_id,
            "displayName": user.display_name,
            "role": user.role,
            "state": user.state,
        }


class UserManagementService:
    def __init__(
        self,
        user_repository: UserRepository,
        audit_log_repository: AuditLogRepository,
    ) -> None:
        self._user_repository = user_repository
        self._audit_log_repository = audit_log_repository

    def list_users(
        self,
        actor: UserContext,
        role: str | None = None,
        state: str | None = None,
        query: str | None = None,
    ) -> dict:
        if actor.role != "admin":
            raise PermissionError("Only admin can manage users")
        users = self._user_repository.list_users()
        normalized_query = (query or "").strip().lower()
        if role is not None:
            users = [user for user in users if user.role == role]
        if state is not None:
            users = [user for user in users if user.state == state]
        if normalized_query:
            users = [
                user
                for user in users
                if normalized_query in user.user_id.lower()
                or normalized_query in user.display_name.lower()
            ]
        users.sort(key=lambda user: user.updated_at, reverse=True)
        return {"items": [self._to_response(user) for user in users]}

    def update_user(
        self,
        actor: UserContext,
        user_id: str,
        role: str | None = None,
        state: str | None = None,
        display_name: str | None = None,
    ) -> dict:
        if actor.role != "admin":
            raise PermissionError("Only admin can manage users")
        if role is None and state is None and display_name is None:
            raise ValueError("At least one field is required for update")
        current = self._user_repository.get(user_id)
        if current is None:
            raise ValueError("User not found")
        updated = UserAccount(
            user_id=current.user_id,
            display_name=display_name if display_name is not None else current.display_name,
            role=role if role is not None else current.role,  # type: ignore[arg-type]
            state=state if state is not None else current.state,  # type: ignore[arg-type]
            created_at=current.created_at,
            updated_at=now_iso(),
        )
        saved = self._user_repository.save(updated)
        self._audit_log_repository.append(
            AuditLogEvent(
                event_type="admin.user.updated",
                resource_type="user",
                resource_id=saved.user_id,
                action="update",
                actor_user_id=actor.user_id,
                actor_role=actor.role,
                summary="管理者がユーザー設定を更新",
                metadata={
                    "role": saved.role,
                    "state": saved.state,
                },
            )
        )
        return self._to_response(saved)

    def _to_response(self, user: UserAccount) -> dict:
        return {
            "userId": user.user_id,
            "displayName": user.display_name,
            "role": user.role,
            "state": user.state,
            "createdAt": user.created_at,
            "updatedAt": user.updated_at,
        }


class AuditLogService:
    def __init__(self, repository: AuditLogRepository) -> None:
        self._repository = repository

    def list_logs(
        self,
        actor: UserContext,
        limit: int = 100,
        event_type: str | None = None,
        actor_user_id: str | None = None,
        occurred_from: str | None = None,
        occurred_to: str | None = None,
    ) -> dict:
        if actor.role != "admin":
            raise PermissionError("Only admin can view audit logs")
        values = self._repository.list_logs(
            limit=limit,
            event_type=event_type,
            actor_user_id=actor_user_id,
            occurred_from=occurred_from,
            occurred_to=occurred_to,
        )
        return {
            "items": [
                {
                    "id": value.id,
                    "eventType": value.event_type,
                    "resourceType": value.resource_type,
                    "resourceId": value.resource_id,
                    "action": value.action,
                    "actorUserId": value.actor_user_id,
                    "actorRole": value.actor_role,
                    "summary": value.summary,
                    "metadata": value.metadata,
                    "occurredAt": value.occurred_at,
                }
                for value in values
            ]
        }
