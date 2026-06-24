from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone

from domain.models import (
    AuditLogEvent,
    Company,
    ConsentRecord,
    Course,
    CurriculumVersion,
    Goal,
    Message,
    MessageTemplateAuditLog,
    MessageTemplate,
    MessageThread,
    ModerationCase,
    NotificationDeliverySetting,
    Notification,
    Opportunity,
    OpportunityApplicationSnapshot,
    PortfolioArtifact,
    PublicProfileSetting,
    ProgressEvent,
    Roadmap,
    UserAccount,
    now_iso,
)


def _parse_iso_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


class InMemoryConsentRepository:
    def __init__(self) -> None:
        self._store: dict[str, list[ConsentRecord]] = defaultdict(list)

    def save(self, consent: ConsentRecord) -> ConsentRecord:
        self._store[consent.user_id].insert(0, consent)
        return consent

    def list_by_user(self, user_id: str) -> list[ConsentRecord]:
        return self._store[user_id]


class InMemoryGoalRepository:
    def __init__(self) -> None:
        self._store: dict[str, Goal] = {}
        self._index_by_user: dict[str, list[str]] = defaultdict(list)

    def save(self, goal: Goal) -> Goal:
        self._store[goal.id] = goal
        self._index_by_user[goal.user_id].insert(0, goal.id)
        return goal

    def get(self, goal_id: str) -> Goal | None:
        return self._store.get(goal_id)

    def list_by_user(self, user_id: str) -> list[Goal]:
        return [self._store[id_] for id_ in self._index_by_user[user_id]]


class InMemoryRoadmapRepository:
    def __init__(self) -> None:
        self._store: dict[str, Roadmap] = {}
        self._index_by_user: dict[str, list[str]] = defaultdict(list)

    def save(self, roadmap: Roadmap) -> Roadmap:
        self._store[roadmap.id] = roadmap
        self._index_by_user[roadmap.user_id].insert(0, roadmap.id)
        return roadmap

    def get(self, roadmap_id: str) -> Roadmap | None:
        return self._store.get(roadmap_id)

    def list_by_user(self, user_id: str) -> list[Roadmap]:
        return [self._store[id_] for id_ in self._index_by_user[user_id]]

    def list_all(self) -> list[Roadmap]:
        return list(self._store.values())


class InMemoryCurriculumRepository:
    def __init__(self, initial_values: list[CurriculumVersion] | None = None) -> None:
        self._values: list[CurriculumVersion] = initial_values or []

    def list_published(self) -> list[CurriculumVersion]:
        return [value for value in self._values if value.published]

    def get(self, curriculum_version_id: str) -> CurriculumVersion | None:
        return next((value for value in self._values if value.id == curriculum_version_id), None)

    def save(self, curriculum_version: CurriculumVersion) -> CurriculumVersion:
        self._values.insert(0, curriculum_version)
        return curriculum_version


class InMemoryCourseRepository:
    def __init__(self, initial_values: list[Course] | None = None) -> None:
        self._values: list[Course] = initial_values or []

    def list_published(self) -> list[Course]:
        return [value for value in self._values if value.published]

    def get_by_slug(self, slug: str) -> Course | None:
        return next(
            (value for value in self._values if value.slug == slug and value.published),
            None,
        )


class InMemoryProgressRepository:
    def __init__(self) -> None:
        self._events_by_user: dict[str, list[ProgressEvent]] = defaultdict(list)
        self._processed_idempotency_keys: set[str] = set()

    def save(self, event: ProgressEvent) -> ProgressEvent | None:
        if event.idempotency_key in self._processed_idempotency_keys:
            return None
        self._processed_idempotency_keys.add(event.idempotency_key)
        self._events_by_user[event.user_id].insert(0, event)
        return event

    def list_by_user(self, user_id: str) -> list[ProgressEvent]:
        return self._events_by_user[user_id]


class InMemoryOpportunityApplicationRepository:
    def __init__(self) -> None:
        self._state_by_user: dict[str, dict[str, OpportunityApplicationSnapshot]] = defaultdict(dict)

    def set_state(self, user_id: str, opportunity_id: str, state: str) -> str:
        self._state_by_user[user_id][opportunity_id] = OpportunityApplicationSnapshot(
            user_id=user_id,
            opportunity_id=opportunity_id,
            state=state,  # type: ignore[arg-type]
            updated_at=now_iso(),
        )
        return state

    def get_state(self, user_id: str, opportunity_id: str) -> str:
        value = self._state_by_user[user_id].get(opportunity_id)
        if value is None:
            return "none"
        return value.state

    def list_by_user(self, user_id: str) -> dict[str, str]:
        return {
            key: value.state
            for key, value in self._state_by_user[user_id].items()
        }

    def list_records_by_user(self, user_id: str) -> list[OpportunityApplicationSnapshot]:
        return list(self._state_by_user[user_id].values())


class InMemoryOpportunityRepository:
    def __init__(self, initial_values: list[Opportunity] | None = None) -> None:
        self._values: list[Opportunity] = initial_values or []

    def list_all(self) -> list[Opportunity]:
        return list(self._values)

    def get(self, opportunity_id: str) -> Opportunity | None:
        return next((value for value in self._values if value.id == opportunity_id), None)


class InMemoryCompanyRepository:
    def __init__(self, initial_values: list[Company] | None = None) -> None:
        self._store: dict[str, Company] = {
            value.id: value for value in (initial_values or [])
        }

    def list_all(self) -> list[Company]:
        values = list(self._store.values())
        values.sort(key=lambda value: value.updated_at, reverse=True)
        return values

    def get(self, company_id: str) -> Company | None:
        return self._store.get(company_id)

    def save(self, value: Company) -> Company:
        self._store[value.id] = value
        return value

    def get_many(self, company_ids: list[str]) -> list[Company]:
        requested = set(company_ids)
        return [value for company_id, value in self._store.items() if company_id in requested]


class InMemoryModerationRepository:
    def __init__(self, initial_values: list[ModerationCase] | None = None) -> None:
        self._store: dict[str, ModerationCase] = {
            value.id: value for value in (initial_values or [])
        }

    def list_all(self) -> list[ModerationCase]:
        return list(self._store.values())

    def get(self, case_id: str) -> ModerationCase | None:
        return self._store.get(case_id)

    def save(self, value: ModerationCase) -> ModerationCase:
        self._store[value.id] = value
        return value

    def get_many(self, case_ids: list[str]) -> list[ModerationCase]:
        requested = set(case_ids)
        return [value for case_id, value in self._store.items() if case_id in requested]


class InMemoryPortfolioArtifactRepository:
    def __init__(self, initial_values: list[PortfolioArtifact] | None = None) -> None:
        self._values: list[PortfolioArtifact] = initial_values or []

    def list_by_user(self, user_id: str) -> list[PortfolioArtifact]:
        values = [value for value in self._values if value.user_id == user_id]
        values.sort(key=lambda value: value.submitted_at, reverse=True)
        return values

    def get_by_user(self, user_id: str, artifact_id: str) -> PortfolioArtifact | None:
        return next(
            (
                value
                for value in self._values
                if value.user_id == user_id and value.id == artifact_id
            ),
            None,
        )


class InMemoryNotificationRepository:
    def __init__(self, initial_values: list[Notification] | None = None) -> None:
        self._values: list[Notification] = initial_values or []

    def list_by_user(self, user_id: str) -> list[Notification]:
        values = [value for value in self._values if value.user_id == user_id]
        values.sort(key=lambda value: value.created_at, reverse=True)
        return values

    def mark_read(self, user_id: str, notification_id: str) -> Notification | None:
        for value in self._values:
            if value.user_id == user_id and value.id == notification_id:
                if value.read_at is None:
                    value.read_at = now_iso()
                return value
        return None

    def mark_all_read(self, user_id: str) -> int:
        updated = 0
        for value in self._values:
            if value.user_id == user_id and value.read_at is None:
                value.read_at = now_iso()
                updated += 1
        return updated


class InMemoryNotificationDeliverySettingRepository:
    def __init__(self, initial_values: list[NotificationDeliverySetting] | None = None) -> None:
        self._values: list[NotificationDeliverySetting] = initial_values or []

    def list_by_user(self, user_id: str) -> list[NotificationDeliverySetting]:
        values = [value for value in self._values if value.user_id == user_id]
        values.sort(key=lambda value: value.category)
        return values

    def upsert_by_user(
        self,
        user_id: str,
        category: str,
        email_enabled: bool,
        in_app_enabled: bool,
        push_enabled: bool,
    ) -> NotificationDeliverySetting:
        for index, value in enumerate(self._values):
            if value.user_id == user_id and value.category == category:
                updated = NotificationDeliverySetting(
                    user_id=user_id,
                    category=category,  # type: ignore[arg-type]
                    email_enabled=email_enabled,
                    in_app_enabled=in_app_enabled,
                    push_enabled=push_enabled,
                )
                self._values[index] = updated
                return updated
        created = NotificationDeliverySetting(
            user_id=user_id,
            category=category,  # type: ignore[arg-type]
            email_enabled=email_enabled,
            in_app_enabled=in_app_enabled,
            push_enabled=push_enabled,
        )
        self._values.insert(0, created)
        return created


class InMemoryMessageRepository:
    def __init__(
        self,
        initial_threads: list[MessageThread] | None = None,
        initial_messages: list[Message] | None = None,
    ) -> None:
        self._threads_by_user: dict[str, list[MessageThread]] = defaultdict(list)
        self._messages_by_thread: dict[str, list[Message]] = defaultdict(list)
        for thread in initial_threads or []:
            self._threads_by_user[thread.owner_user_id].append(thread)
        for message in initial_messages or []:
            self._messages_by_thread[message.thread_id].append(message)

    def list_threads_by_user(self, user_id: str) -> list[MessageThread]:
        values = list(self._threads_by_user[user_id])
        values.sort(key=lambda value: value.updated_at, reverse=True)
        return values

    def get_thread_by_user(self, user_id: str, thread_id: str) -> MessageThread | None:
        return next(
            (
                thread
                for thread in self._threads_by_user[user_id]
                if thread.id == thread_id
            ),
            None,
        )

    def list_messages(self, thread_id: str) -> list[Message]:
        values = list(self._messages_by_thread[thread_id])
        values.sort(key=lambda value: value.created_at)
        return values

    def append_message(self, message: Message) -> Message:
        self._messages_by_thread[message.thread_id].append(message)
        return message


class InMemoryMessageTemplateRepository:
    def __init__(self, initial_values: list[MessageTemplate] | None = None) -> None:
        self._values: list[MessageTemplate] = initial_values or []

    def list_templates(self) -> list[MessageTemplate]:
        return list(self._values)

    def get_template(self, template_id: str) -> MessageTemplate | None:
        return next((value for value in self._values if value.id == template_id), None)

    def save_template(self, template: MessageTemplate) -> MessageTemplate:
        self._values.insert(0, template)
        return template

    def update_template(self, template: MessageTemplate) -> MessageTemplate | None:
        for index, value in enumerate(self._values):
            if value.id == template.id:
                self._values[index] = template
                return template
        return None

    def delete_template(self, template_id: str) -> bool:
        for index, value in enumerate(self._values):
            if value.id == template_id:
                del self._values[index]
                return True
        return False


class InMemoryMessageTemplateAuditLogRepository:
    def __init__(self, initial_values: list[MessageTemplateAuditLog] | None = None) -> None:
        self._values: list[MessageTemplateAuditLog] = initial_values or []

    def append_log(self, value: MessageTemplateAuditLog) -> MessageTemplateAuditLog:
        self._values.insert(0, value)
        return value

    def list_logs(self, limit: int = 100) -> list[MessageTemplateAuditLog]:
        return self._values[:limit]


class InMemoryPublicProfileSettingRepository:
    def __init__(self, initial_values: list[PublicProfileSetting] | None = None) -> None:
        self._store: dict[str, PublicProfileSetting] = {
            value.user_id: value for value in (initial_values or [])
        }

    def get_by_user(self, user_id: str) -> PublicProfileSetting | None:
        return self._store.get(user_id)

    def upsert(self, value: PublicProfileSetting) -> PublicProfileSetting:
        updated = PublicProfileSetting(
            user_id=value.user_id,
            visibility=value.visibility,
            show_goal=value.show_goal,
            show_skill_evidence=value.show_skill_evidence,
            show_portfolio=value.show_portfolio,
            allow_recruiter_contact=value.allow_recruiter_contact,
            updated_at=now_iso(),
        )
        self._store[value.user_id] = updated
        return updated


class InMemoryUserRepository:
    def __init__(self, initial_values: list[UserAccount] | None = None) -> None:
        self._store: dict[str, UserAccount] = {
            value.user_id: value for value in (initial_values or [])
        }

    def get(self, user_id: str) -> UserAccount | None:
        return self._store.get(user_id)

    def save(self, user: UserAccount) -> UserAccount:
        self._store[user.user_id] = user
        return user

    def list_users(self) -> list[UserAccount]:
        return list(self._store.values())


class InMemoryAuditLogRepository:
    def __init__(self, initial_values: list[AuditLogEvent] | None = None) -> None:
        self._values: list[AuditLogEvent] = initial_values or []

    def append(self, value: AuditLogEvent) -> AuditLogEvent:
        self._values.insert(0, value)
        return value

    def list_logs(
        self,
        limit: int = 100,
        event_type: str | None = None,
        actor_user_id: str | None = None,
        occurred_from: str | None = None,
        occurred_to: str | None = None,
    ) -> list[AuditLogEvent]:
        values = self._values
        if event_type is not None:
            values = [value for value in values if value.event_type == event_type]
        if actor_user_id is not None:
            values = [value for value in values if value.actor_user_id == actor_user_id]
        if occurred_from is not None:
            from_dt = _parse_iso_datetime(occurred_from)
            values = [
                value
                for value in values
                if _parse_iso_datetime(value.occurred_at) >= from_dt
            ]
        if occurred_to is not None:
            to_dt = _parse_iso_datetime(occurred_to)
            values = [
                value
                for value in values
                if _parse_iso_datetime(value.occurred_at) <= to_dt
            ]
        return values[:limit]
