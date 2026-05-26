"""Initial PostgreSQL schema for B2B platform.

Revision ID: 20260526_0001
Revises:
Create Date: 2026-05-26 11:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260526_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("user_id", sa.String(length=64), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])

    op.create_table(
        "teams",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "team_members",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("team_id", sa.String(length=64), sa.ForeignKey("teams.id")),
        sa.Column("user_id", sa.String(length=64), sa.ForeignKey("users.user_id")),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "invites",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("team_id", sa.String(length=64), sa.ForeignKey("teams.id")),
        sa.Column("token", sa.String(length=255), nullable=False, unique=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="invited"),
        sa.Column("invited_by", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "role_templates",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("target_skills", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.create_table(
        "learner_profiles",
        sa.Column("user_id", sa.String(length=64), sa.ForeignKey("users.user_id"), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("team_name", sa.String(length=120), nullable=False),
        sa.Column("target_role", sa.String(length=120), nullable=False),
        sa.Column("roadmap_completion_rate", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("readiness", sa.String(length=32), nullable=False, server_default="Not Started"),
        sa.Column("pending_submission_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("strong_skills", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("gap_skills", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.create_table(
        "roadmap_assignments",
        sa.Column("id", sa.String(length=80), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("learner_id", sa.String(length=64), sa.ForeignKey("users.user_id")),
        sa.Column("role_template_id", sa.String(length=64), sa.ForeignKey("role_templates.id")),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="assigned"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "exercises",
        sa.Column("id", sa.String(length=80), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False, server_default="notebook"),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("starter_code", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.create_table(
        "submissions",
        sa.Column("id", sa.String(length=80), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("exercise_id", sa.String(length=80), sa.ForeignKey("exercises.id")),
        sa.Column("learner_id", sa.String(length=64), sa.ForeignKey("users.user_id")),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="submitted"),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("execution_status", sa.String(length=32), nullable=True),
        sa.Column("execution_stdout", sa.Text(), nullable=True),
        sa.Column("execution_stderr", sa.Text(), nullable=True),
        sa.Column("execution_engine", sa.String(length=64), nullable=True),
        sa.Column("execution_pipeline", sa.String(length=64), nullable=True),
        sa.Column("execution_details_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "reviews",
        sa.Column("id", sa.String(length=80), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("submission_id", sa.String(length=80), sa.ForeignKey("submissions.id")),
        sa.Column("reviewer_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("comments", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "evidence",
        sa.Column("id", sa.String(length=80), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("learner_id", sa.String(length=64), sa.ForeignKey("users.user_id")),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("skill_tags", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("strength", sa.String(length=32)),
        sa.Column("review_type", sa.String(length=32)),
        sa.Column("status", sa.String(length=32)),
        sa.Column("use_case", sa.Text()),
        sa.Column("rubric_summary", sa.Text()),
        sa.Column("exercise_id", sa.String(length=80)),
        sa.Column("submission_id", sa.String(length=80)),
        sa.Column("score", sa.Integer()),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column(
            "related_requirement_ids",
            sa.JSON(),
            nullable=False,
            server_default="[]",
        ),
    )
    op.create_table(
        "requirements",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("required_skills", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "fit_assessments",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("requirement_id", sa.String(length=64), sa.ForeignKey("requirements.id")),
        sa.Column("recommended_learner_id", sa.String(length=64), sa.ForeignKey("users.user_id")),
        sa.Column("fit_score", sa.Integer(), nullable=False),
        sa.Column("matched_skills", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("gap_skills", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "report_jobs",
        sa.Column("id", sa.String(length=80), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("report_id", sa.String(length=80), nullable=False),
        sa.Column("report_format", sa.String(length=16), nullable=False, server_default="csv"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("result_url", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "curriculum_versions",
        sa.Column("id", sa.String(length=80), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("curriculum_slug", sa.String(length=120), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("mdx_path", sa.String(length=255), nullable=False),
        sa.Column("skill_tags", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("difficulty", sa.Integer(), nullable=False),
        sa.Column("estimated_minutes", sa.Integer(), nullable=False),
        sa.Column("published", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(length=80), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("resource_type", sa.String(length=120), nullable=False),
        sa.Column("resource_id", sa.String(length=120), nullable=False),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("actor_user_id", sa.String(length=64), nullable=False),
        sa.Column("actor_role", sa.String(length=32), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_audit_logs_tenant_occurred_at", "audit_logs", ["tenant_id", "occurred_at"])
    op.create_index(
        "ix_audit_logs_tenant_event_type_occurred_at",
        "audit_logs",
        ["tenant_id", "event_type", "occurred_at"],
    )
    op.create_index(
        "ix_audit_logs_tenant_actor_occurred_at",
        "audit_logs",
        ["tenant_id", "actor_user_id", "occurred_at"],
    )
    op.create_index(
        "ix_audit_logs_tenant_resource_occurred_at",
        "audit_logs",
        ["tenant_id", "resource_type", "resource_id", "occurred_at"],
    )
    op.create_table(
        "notifications",
        sa.Column("id", sa.String(length=80), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("target_url", sa.String(length=255), nullable=False),
        sa.Column("is_important", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_notifications_tenant_id", "notifications", ["tenant_id"])
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_category", "notifications", ["category"])
    op.create_index(
        "ix_notifications_user_read_created",
        "notifications",
        ["user_id", "read_at", "created_at"],
    )
    op.create_index(
        "ix_notifications_user_category_created",
        "notifications",
        ["user_id", "category", "created_at"],
    )
    op.create_table(
        "notification_delivery_settings",
        sa.Column("id", sa.String(length=80), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("email_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("in_app_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("push_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_notification_delivery_settings_tenant_id", "notification_delivery_settings", ["tenant_id"])
    op.create_index("ix_notification_delivery_settings_user_id", "notification_delivery_settings", ["user_id"])
    op.create_index("ix_notification_delivery_settings_category", "notification_delivery_settings", ["category"])
    op.create_index(
        "ux_notification_delivery_user_category",
        "notification_delivery_settings",
        ["user_id", "category"],
        unique=True,
    )
    op.create_table(
        "notification_delivery_jobs",
        sa.Column("id", sa.String(length=80), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("target_url", sa.String(length=255), nullable=False),
        sa.Column("channels", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("is_important", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("available_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("result_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_notification_delivery_jobs_tenant_id", "notification_delivery_jobs", ["tenant_id"])
    op.create_index("ix_notification_delivery_jobs_user_id", "notification_delivery_jobs", ["user_id"])
    op.create_index("ix_notification_delivery_jobs_status", "notification_delivery_jobs", ["status"])
    op.create_index("ix_notification_delivery_jobs_available_at", "notification_delivery_jobs", ["available_at"])
    op.create_index(
        "ix_notification_delivery_jobs_status_available",
        "notification_delivery_jobs",
        ["status", "available_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_notification_delivery_jobs_status_available", table_name="notification_delivery_jobs")
    op.drop_index("ix_notification_delivery_jobs_available_at", table_name="notification_delivery_jobs")
    op.drop_index("ix_notification_delivery_jobs_status", table_name="notification_delivery_jobs")
    op.drop_index("ix_notification_delivery_jobs_user_id", table_name="notification_delivery_jobs")
    op.drop_index("ix_notification_delivery_jobs_tenant_id", table_name="notification_delivery_jobs")
    op.drop_table("notification_delivery_jobs")
    op.drop_index("ux_notification_delivery_user_category", table_name="notification_delivery_settings")
    op.drop_index("ix_notification_delivery_settings_category", table_name="notification_delivery_settings")
    op.drop_index("ix_notification_delivery_settings_user_id", table_name="notification_delivery_settings")
    op.drop_index("ix_notification_delivery_settings_tenant_id", table_name="notification_delivery_settings")
    op.drop_table("notification_delivery_settings")
    op.drop_index("ix_notifications_user_category_created", table_name="notifications")
    op.drop_index("ix_notifications_user_read_created", table_name="notifications")
    op.drop_index("ix_notifications_category", table_name="notifications")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_index("ix_notifications_tenant_id", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index("ix_audit_logs_tenant_resource_occurred_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_tenant_actor_occurred_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_tenant_event_type_occurred_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_tenant_occurred_at", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_table("curriculum_versions")
    op.drop_table("report_jobs")
    op.drop_table("fit_assessments")
    op.drop_table("requirements")
    op.drop_table("evidence")
    op.drop_table("reviews")
    op.drop_table("submissions")
    op.drop_table("exercises")
    op.drop_table("roadmap_assignments")
    op.drop_table("learner_profiles")
    op.drop_table("role_templates")
    op.drop_table("invites")
    op.drop_table("team_members")
    op.drop_table("teams")
    op.drop_index("ix_users_tenant_id", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
