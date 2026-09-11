from __future__ import annotations

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from infrastructure.db import Base


class UserModel(Base):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(32), index=True)
    state: Mapped[str] = mapped_column(String(32), default="active")
    session_version: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class ApplicationRecordModel(Base):
    """Durable snapshots for consent, learning records and generated reports."""
    __tablename__ = "application_records"
    namespace: Mapped[str] = mapped_column(String(64), primary_key=True)
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TeamModel(Base):
    __tablename__ = "teams"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TeamMemberModel(Base):
    __tablename__ = "team_members"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), index=True)
    joined_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class InviteModel(Base):
    __tablename__ = "invites"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    email: Mapped[str] = mapped_column(String(255), index=True)
    role: Mapped[str] = mapped_column(String(32))
    team_id: Mapped[str | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    token: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="invited")
    invited_by: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RequirementModel(Base):
    __tablename__ = "requirements"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text())
    required_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FitAssessmentModel(Base):
    __tablename__ = "fit_assessments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    requirement_id: Mapped[str] = mapped_column(ForeignKey("requirements.id"), index=True)
    recommended_learner_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"))
    fit_score: Mapped[int] = mapped_column(Integer)
    matched_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    gap_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RoleTemplateModel(Base):
    __tablename__ = "role_templates"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    code: Mapped[str] = mapped_column(String(80), index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text())
    target_skills: Mapped[list[str]] = mapped_column(JSON, default=list)


class LearnerProfileModel(Base):
    __tablename__ = "learner_profiles"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    team_name: Mapped[str] = mapped_column(String(120))
    target_role: Mapped[str] = mapped_column(String(120))
    roadmap_completion_rate: Mapped[int] = mapped_column(Integer, default=0)
    readiness: Mapped[str] = mapped_column(String(32), default="Not Started")
    pending_submission_count: Mapped[int] = mapped_column(Integer, default=0)
    strong_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    gap_skills: Mapped[list[str]] = mapped_column(JSON, default=list)


class RoadmapAssignmentModel(Base):
    __tablename__ = "roadmap_assignments"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    learner_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), index=True)
    role_template_id: Mapped[str] = mapped_column(ForeignKey("role_templates.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="assigned")
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ExerciseModel(Base):
    __tablename__ = "exercises"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    kind: Mapped[str] = mapped_column(String(32), default="notebook")
    title: Mapped[str] = mapped_column(String(255))
    prompt: Mapped[str] = mapped_column(Text())
    starter_code: Mapped[str] = mapped_column(Text())
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class SubmissionModel(Base):
    __tablename__ = "submissions"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    exercise_id: Mapped[str] = mapped_column(ForeignKey("exercises.id"), index=True)
    learner_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="submitted")
    code: Mapped[str] = mapped_column(Text())
    execution_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    execution_stdout: Mapped[str | None] = mapped_column(Text(), nullable=True)
    execution_stderr: Mapped[str | None] = mapped_column(Text(), nullable=True)
    execution_engine: Mapped[str | None] = mapped_column(String(64), nullable=True)
    execution_pipeline: Mapped[str | None] = mapped_column(String(64), nullable=True)
    execution_details_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ReviewModel(Base):
    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    submission_id: Mapped[str] = mapped_column(ForeignKey("submissions.id"), index=True)
    reviewer_type: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32))
    score: Mapped[int] = mapped_column(Integer)
    comments: Mapped[str] = mapped_column(Text())
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EvidenceModel(Base):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    learner_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str] = mapped_column(Text())
    skill_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    strength: Mapped[str | None] = mapped_column(String(32), nullable=True)
    review_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    use_case: Mapped[str | None] = mapped_column(Text(), nullable=True)
    rubric_summary: Mapped[str | None] = mapped_column(Text(), nullable=True)
    exercise_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    submission_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    submitted_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    related_requirement_ids: Mapped[list[str]] = mapped_column(JSON, default=list)


class ReportJobModel(Base):
    __tablename__ = "report_jobs"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    report_id: Mapped[str] = mapped_column(String(80), index=True)
    report_format: Mapped[str] = mapped_column(String(16), default="csv")
    status: Mapped[str] = mapped_column(String(32), default="queued")
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    result_url: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CurriculumVersionModel(Base):
    __tablename__ = "curriculum_versions"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    curriculum_slug: Mapped[str] = mapped_column(String(120), index=True)
    version: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(255))
    mdx_path: Mapped[str] = mapped_column(String(255))
    skill_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    difficulty: Mapped[int] = mapped_column(Integer)
    estimated_minutes: Mapped[int] = mapped_column(Integer)
    published: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    event_type: Mapped[str] = mapped_column(String(120), index=True)
    resource_type: Mapped[str] = mapped_column(String(120), index=True)
    resource_id: Mapped[str] = mapped_column(String(120), index=True)
    action: Mapped[str] = mapped_column(String(80))
    actor_user_id: Mapped[str] = mapped_column(String(64), index=True)
    actor_role: Mapped[str] = mapped_column(String(32))
    summary: Mapped[str] = mapped_column(Text())
    metadata_json: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    occurred_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_audit_logs_tenant_occurred_at", "tenant_id", "occurred_at"),
        Index("ix_audit_logs_tenant_event_type_occurred_at", "tenant_id", "event_type", "occurred_at"),
        Index("ix_audit_logs_tenant_actor_occurred_at", "tenant_id", "actor_user_id", "occurred_at"),
        Index("ix_audit_logs_tenant_resource_occurred_at", "tenant_id", "resource_type", "resource_id", "occurred_at"),
    )


class NotificationInboxModel(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    category: Mapped[str] = mapped_column(String(32), index=True)
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text())
    target_url: Mapped[str] = mapped_column(String(255))
    is_important: Mapped[bool] = mapped_column(Boolean, default=False)
    read_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_notifications_user_read_created", "user_id", "read_at", "created_at"),
        Index("ix_notifications_user_category_created", "user_id", "category", "created_at"),
    )


class NotificationDeliverySettingModel(Base):
    __tablename__ = "notification_delivery_settings"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    category: Mapped[str] = mapped_column(String(32), index=True)
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    in_app_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ux_notification_delivery_user_category", "user_id", "category", unique=True),
    )


class VentureModel(Base):
    """自社事業のAIプロジェクト。工程マスタを参照して台帳を持つ。"""

    __tablename__ = "ventures"
    governance: Mapped[dict] = mapped_column(JSON, default=dict)

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(Text(), default="")
    offering_type: Mapped[str] = mapped_column(String(32), default="社内事業")
    industry: Mapped[str] = mapped_column(String(120), default="")
    service_countries: Mapped[str] = mapped_column(String(255), default="")
    processing_countries: Mapped[str] = mapped_column(String(255), default="")
    scale: Mapped[str] = mapped_column(String(8), default="S")
    risk_tier: Mapped[str] = mapped_column(String(8), default="未判定")
    risk_tier_rationale: Mapped[str] = mapped_column(Text(), default="")
    status: Mapped[str] = mapped_column(String(16), default="計画中", index=True)
    current_phase_id: Mapped[str] = mapped_column(String(8), default="B0")
    business_owner_user_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    conditions: Mapped[dict] = mapped_column(JSON, default=dict)
    # 原本 00 の「管理基準日」。期限・未来日の点検はすべてこの日付を基準にする。
    # 未設定ならサーバの当日を使う（原本のテンプレート値へはフォールバックしない）。
    as_of_date: Mapped[str] = mapped_column(String(10), default="")
    created_by: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (Index("ix_ventures_tenant_status", "tenant_id", "status"),)


class VentureTaskModel(Base):
    """工程タスクの案件別実行台帳（原本 17_ロードマップ・案件実行管理）。"""

    __tablename__ = "venture_tasks"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    venture_id: Mapped[str] = mapped_column(ForeignKey("ventures.id"), index=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    task_id: Mapped[str] = mapped_column(String(16), index=True)
    phase_id: Mapped[str] = mapped_column(String(8), index=True)
    gate_id: Mapped[str] = mapped_column(String(8), index=True)
    applicability: Mapped[str] = mapped_column(String(16), default="未判定", index=True)
    applicability_reason: Mapped[str] = mapped_column(Text(), default="")
    applicability_decided_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    applicability_decided_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="未着手", index=True)
    assignee_user_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    role_id: Mapped[str] = mapped_column(String(8), default="")
    planned_start: Mapped[str] = mapped_column(String(10), default="")
    planned_end: Mapped[str] = mapped_column(String(10), default="")
    actual_start: Mapped[str] = mapped_column(String(10), default="")
    actual_end: Mapped[str] = mapped_column(String(10), default="")
    planned_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    evidence_uri: Mapped[str] = mapped_column(Text(), default="")
    completion_approved_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    completion_approved_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    blocker: Mapped[str] = mapped_column(Text(), default="")
    note: Mapped[str] = mapped_column(Text(), default="")
    # 原本17の直接依存ID。標準依存（02の基本依存ID）から変えるときは
    # 理由・承認者・承認日を残す（原本17!W「依存変更承認不足」）。
    depends_on_override: Mapped[str] = mapped_column(Text(), default="")
    dependency_change_reason: Mapped[str] = mapped_column(Text(), default="")
    dependency_change_approved_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    dependency_change_approved_at: Mapped[str | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    updated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ux_venture_tasks_venture_task", "venture_id", "task_id", unique=True),
        Index("ix_venture_tasks_venture_phase", "venture_id", "phase_id"),
    )


class VentureGateModel(Base):
    """ゲート承認記録（原本 29_ゲート承認記録）。"""

    __tablename__ = "venture_gates"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    venture_id: Mapped[str] = mapped_column(ForeignKey("ventures.id"), index=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    gate_id: Mapped[str] = mapped_column(String(8), index=True)
    decision: Mapped[str] = mapped_column(String(32), default="未審査", index=True)
    scope: Mapped[str] = mapped_column(Text(), default="")
    evidence_package_uri: Mapped[str] = mapped_column(Text(), default="")
    conditions: Mapped[str] = mapped_column(Text(), default="")
    condition_due: Mapped[str] = mapped_column(String(10), default="")
    decided_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    decided_by_name: Mapped[str] = mapped_column(String(120), default="")
    decided_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_action: Mapped[str] = mapped_column(Text(), default="")
    review_trigger: Mapped[str] = mapped_column(Text(), default="")
    updated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (Index("ux_venture_gates_venture_gate", "venture_id", "gate_id", unique=True),)


class VentureMemberModel(Base):
    """案件の要員割当（原本 06_ロール・要員計画 / 35_実名・能力割当）。"""

    __tablename__ = "venture_members"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    venture_id: Mapped[str] = mapped_column(ForeignKey("ventures.id"), index=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    role_id: Mapped[str] = mapped_column(String(8), index=True)
    allocation_note: Mapped[str] = mapped_column(Text(), default="")
    appointed_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ux_venture_members_venture_user_role", "venture_id", "user_id", "role_id", unique=True),
    )


class VentureLedgerEntryModel(Base):
    """汎用台帳の1行（データ・依存・ADR・リスク・SLO・KPI など）。

    台帳ごとに列が違うため、値は `values_json` に列名 -> 値 で保持する。
    列の定義はマスタ（venture_process_master.json）が持つ。
    """

    __tablename__ = "venture_ledger_entries"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    venture_id: Mapped[str] = mapped_column(ForeignKey("ventures.id"), index=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    ledger_key: Mapped[str] = mapped_column(String(32), index=True)
    row_key: Mapped[str] = mapped_column(String(64), index=True)
    is_master_row: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(32), default="未着手", index=True)
    values_json: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ux_venture_ledger_row", "venture_id", "ledger_key", "row_key", unique=True),
    )


class VentureSkillAssessmentModel(Base):
    """案件で必要なスキルに対する担当者の到達度（原本 28_スキル評価・育成）。

    必要Lv はタスクマスタから算出するため保持しない。ここは評価と育成計画を持つ。
    """

    __tablename__ = "venture_skill_assessments"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    venture_id: Mapped[str] = mapped_column(ForeignKey("ventures.id"), index=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    skill_id: Mapped[str] = mapped_column(String(16), index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    assessed_level: Mapped[int] = mapped_column(Integer, default=0)
    supersedes_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    evidence_uri: Mapped[str] = mapped_column(Text(), default="")
    development_plan: Mapped[str] = mapped_column(Text(), default="")
    due_date: Mapped[str] = mapped_column(String(10), default="")
    assessed_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    assessed_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_venture_skill_user", "venture_id", "skill_id", "user_id"),
    )


class NotificationDeliveryJobModel(Base):
    __tablename__ = "notification_delivery_jobs"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    category: Mapped[str] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text())
    target_url: Mapped[str] = mapped_column(String(255))
    channels: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_important: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(32), default="queued", index=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text(), nullable=True)
    available_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    result_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_notification_delivery_jobs_status_available", "status", "available_at"),
    )
