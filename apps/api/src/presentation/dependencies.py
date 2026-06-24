from __future__ import annotations

from dataclasses import dataclass

from fastapi import Cookie, Header, HTTPException
from fastapi.security import OAuth2PasswordBearer

from application.services import (
    AuditLogService,
    AuthService,
    CompanyService,
    ConsentService,
    CurriculumImpactService,
    CurriculumService,
    GoalService,
    ModerationService,
    NotificationService,
    ProgressService,
    RoadmapService,
    SkillGapService,
    UserManagementService,
)
from application.b2b_services import B2BService
from domain.models import (
    Company,
    CurriculumVersion,
    ModerationCase,
    NotificationDeliverySetting,
    Notification,
    UserAccount,
    UserContext,
)
from infrastructure.auth import decode_access_token
from infrastructure.db import Base, SessionLocal, engine
from infrastructure.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryCompanyRepository,
    InMemoryConsentRepository,
    InMemoryCurriculumRepository,
    InMemoryGoalRepository,
    InMemoryModerationRepository,
    InMemoryNotificationDeliverySettingRepository,
    InMemoryNotificationRepository,
    InMemoryProgressRepository,
    InMemoryRoadmapRepository,
    InMemoryUserRepository,
)
from infrastructure.postgres_b2b import PostgresB2BRepository
from infrastructure.settings import load_settings


@dataclass(slots=True)
class ServiceContainer:
    auth_service: AuthService
    consent_service: ConsentService
    goal_service: GoalService
    roadmap_service: RoadmapService
    curriculum_service: CurriculumService
    progress_service: ProgressService
    skill_gap_service: SkillGapService
    company_service: CompanyService
    moderation_service: ModerationService
    curriculum_impact_service: CurriculumImpactService
    notification_service: NotificationService
    user_management_service: UserManagementService
    audit_log_service: AuditLogService
    b2b_service: B2BService


def build_container() -> ServiceContainer:
    settings = load_settings()
    Base.metadata.create_all(bind=engine)
    db_session = SessionLocal()
    postgres_b2b_repository = PostgresB2BRepository(db_session)
    postgres_b2b_repository.seed_if_empty()

    consent_repo = InMemoryConsentRepository()
    goal_repo = InMemoryGoalRepository()
    roadmap_repo = InMemoryRoadmapRepository()
    curriculum_repo = InMemoryCurriculumRepository(
        initial_values=[
            CurriculumVersion(
                curriculum_slug="afr-enterprise-ai-dx-foundation",
                version="1.0.0",
                title="AI/DX全体像と業務活用パターン",
                mdx_path="content/curriculum/ai-field-ready-enterprise/week01-ai-dx-foundation.mdx",
                skill_tags=["ai.foundation", "ai.dx.overview"],
                difficulty=1,
                estimated_minutes=60,
            ),
            CurriculumVersion(
                curriculum_slug="afr-enterprise-business-issue-definition",
                version="1.0.0",
                title="業務課題定義",
                mdx_path="content/curriculum/ai-field-ready-enterprise/week02-business-issue.mdx",
                skill_tags=["ai.business.issue", "ai.kpi"],
                difficulty=2,
                estimated_minutes=90,
            ),
            CurriculumVersion(
                curriculum_slug="afr-enterprise-ai-theme-design",
                version="1.0.0",
                title="AIテーマ化と優先度設計",
                mdx_path="content/curriculum/ai-field-ready-enterprise/week03-ai-theme.mdx",
                skill_tags=["ai.theme.design", "ai.poc.candidate"],
                difficulty=2,
                estimated_minutes=90,
            ),
            CurriculumVersion(
                curriculum_slug="afr-enterprise-data-inventory",
                version="1.0.0",
                title="データ/ナレッジ棚卸し",
                mdx_path="content/curriculum/ai-field-ready-enterprise/week04-data-inventory.mdx",
                skill_tags=["ai.data.inventory", "ai.governance.data"],
                difficulty=2,
                estimated_minutes=75,
            ),
            CurriculumVersion(
                curriculum_slug="afr-enterprise-rag-verification",
                version="1.0.0",
                title="RAG/ナレッジ活用",
                mdx_path="content/curriculum/ai-field-ready-enterprise/week05-rag-knowledge.mdx",
                skill_tags=["ai.rag.design", "ai.knowledge.search"],
                difficulty=3,
                estimated_minutes=90,
            ),
            CurriculumVersion(
                curriculum_slug="afr-enterprise-data-analysis-report",
                version="1.0.0",
                title="データ分析/BI",
                mdx_path="content/curriculum/ai-field-ready-enterprise/week06-data-analysis.mdx",
                skill_tags=["ai.data.analysis", "ai.kpi.dashboard"],
                difficulty=3,
                estimated_minutes=90,
            ),
            CurriculumVersion(
                curriculum_slug="afr-enterprise-ocr-verification",
                version="1.0.0",
                title="AI-OCR/文書処理",
                mdx_path="content/curriculum/ai-field-ready-enterprise/week07-ocr-document.mdx",
                skill_tags=["ai.ocr.design", "ai.document.automation"],
                difficulty=3,
                estimated_minutes=90,
            ),
            CurriculumVersion(
                curriculum_slug="afr-enterprise-agent-automation",
                version="1.0.0",
                title="AIエージェント/自動化",
                mdx_path="content/curriculum/ai-field-ready-enterprise/week08-agent-automation.mdx",
                skill_tags=["ai.agent.design", "ai.workflow.automation"],
                difficulty=3,
                estimated_minutes=90,
            ),
            CurriculumVersion(
                curriculum_slug="afr-enterprise-poc-planning",
                version="1.0.0",
                title="PoC計画",
                mdx_path="content/curriculum/ai-field-ready-enterprise/week09-poc-planning.mdx",
                skill_tags=["ai.poc.planning", "ai.evaluation.design"],
                difficulty=3,
                estimated_minutes=90,
            ),
            CurriculumVersion(
                curriculum_slug="afr-enterprise-prototype-validation",
                version="1.0.0",
                title="プロトタイプ/検証",
                mdx_path="content/curriculum/ai-field-ready-enterprise/week10-prototype.mdx",
                skill_tags=["ai.prototype", "ai.validation.log"],
                difficulty=3,
                estimated_minutes=120,
            ),
            CurriculumVersion(
                curriculum_slug="afr-enterprise-evaluation-report",
                version="1.0.0",
                title="評価・リスク整理",
                mdx_path="content/curriculum/ai-field-ready-enterprise/week11-evaluation.mdx",
                skill_tags=["ai.evaluation.report", "ai.risk.improvement"],
                difficulty=3,
                estimated_minutes=90,
            ),
            CurriculumVersion(
                curriculum_slug="afr-enterprise-project-proposal",
                version="1.0.0",
                title="成果発表とAIプロジェクト提案",
                mdx_path="content/curriculum/ai-field-ready-enterprise/week12-project-proposal.mdx",
                skill_tags=["ai.project.proposal", "ai.roadmap"],
                difficulty=3,
                estimated_minutes=120,
            ),
            CurriculumVersion(
                curriculum_slug="afr-enterprise-ai-governance-foundation",
                version="1.0.0",
                title="AIガバナンス基礎",
                mdx_path="content/curriculum/ai-field-ready-enterprise/common-m05-ai-governance.mdx",
                skill_tags=["ai.governance.foundation", "ai.risk"],
                difficulty=2,
                estimated_minutes=75,
            ),
        ]
    )
    progress_repo = InMemoryProgressRepository()
    company_repo = InMemoryCompanyRepository(
        initial_values=[
            Company(
                id="company-example",
                name="株式会社Example",
                industry="EdTech",
                status="active",
                contact_email="dx@example.co.jp",
                contact_person_name="山田 太郎",
                contact_person_phone="+81-90-0000-1111",
            ),
            Company(
                id="company-manufacturing",
                name="Example Manufacturing",
                industry="Manufacturing",
                status="active",
                contact_email="ai-lab@example-mfg.co.jp",
                contact_person_name="鈴木 花子",
                contact_person_phone="+81-90-2222-3333",
            ),
        ]
    )
    moderation_repo = InMemoryModerationRepository(
        initial_values=[
            ModerationCase(
                id="mod-001",
                target_type="submission",
                target_id="submission-unsafe-1",
                reason="不適切な個人情報が含まれる可能性",
                status="accepted",
                reported_by="demo-user",
                due_at="2025-01-10T09:00:00+00:00",
            ),
            ModerationCase(
                id="mod-002",
                target_type="evidence",
                target_id="evidence-unsafe-1",
                reason="個人情報の露出が疑われる",
                status="investigating",
                reported_by="recruiter-user",
                assigned_admin="admin-user",
                due_at="2099-01-10T09:00:00+00:00",
            ),
        ]
    )
    notification_repo = InMemoryNotificationRepository(
        initial_values=[
            Notification(
                user_id="demo-user",
                category="learning",
                title="演習レビューが完了しました",
                body="業務課題定義書のフィードバックを確認してください。",
                target_url="/learner/evidence",
                is_important=True,
            ),
            Notification(
                user_id="demo-user",
                category="learning",
                title="新しい教材が公開されました",
                body="AI/DX全体像と業務活用パターン v1.0 を確認してください。",
                target_url="/learn/afr-enterprise-ai-dx-foundation/main",
            ),
            Notification(
                user_id="demo-user",
                category="admin",
                title="教材公開申請があります",
                body="AIガバナンス基礎 v1.0.1 の公開承認待ちです。",
                target_url="/admin/curriculum",
            ),
        ]
    )
    audit_log_repo = InMemoryAuditLogRepository()
    user_repo = InMemoryUserRepository(
        initial_values=[
            UserAccount(
                user_id="demo-user",
                display_name="Demo Learner",
                role="learner",
                state="active",
            ),
            UserAccount(
                user_id="admin-user",
                display_name="Platform Admin",
                role="admin",
                state="active",
            ),
            UserAccount(
                user_id="recruiter-user",
                display_name="Recruiter User",
                role="recruiter",
                state="active",
            ),
        ]
    )
    notification_delivery_setting_repo = InMemoryNotificationDeliverySettingRepository(
        initial_values=[
            NotificationDeliverySetting(
                user_id="demo-user",
                category="learning",
                email_enabled=False,
                in_app_enabled=True,
                push_enabled=True,
            ),
            NotificationDeliverySetting(
                user_id="demo-user",
                category="career",
                email_enabled=True,
                in_app_enabled=True,
                push_enabled=False,
            ),
            NotificationDeliverySetting(
                user_id="demo-user",
                category="dm",
                email_enabled=True,
                in_app_enabled=True,
                push_enabled=True,
            ),
            NotificationDeliverySetting(
                user_id="demo-user",
                category="admin",
                email_enabled=False,
                in_app_enabled=True,
                push_enabled=False,
            ),
        ]
    )

    audit_log_service = AuditLogService(audit_log_repo)

    return ServiceContainer(
        auth_service=AuthService(user_repo),
        consent_service=ConsentService(consent_repo),
        goal_service=GoalService(goal_repo),
        roadmap_service=RoadmapService(goal_repo, roadmap_repo, curriculum_repo),
        curriculum_service=CurriculumService(curriculum_repo),
        progress_service=ProgressService(progress_repo, roadmap_repo),
        skill_gap_service=SkillGapService(goal_repo, roadmap_repo, progress_repo),
        company_service=CompanyService(company_repo, audit_log_repo),
        moderation_service=ModerationService(moderation_repo, audit_log_repo),
        curriculum_impact_service=CurriculumImpactService(roadmap_repo),
        notification_service=NotificationService(notification_repo, notification_delivery_setting_repo),
        user_management_service=UserManagementService(user_repo, audit_log_repo),
        audit_log_service=audit_log_service,
        b2b_service=B2BService(repository=postgres_b2b_repository),
    )


CONTAINER = build_container()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/sign-in")


def get_current_user(
    authorization: str | None = Header(default=None),
    auth_cookie: str | None = Cookie(default=None, alias=load_settings().auth_cookie_name),
) -> UserContext:
    token: str | None = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    elif auth_cookie:
        token = auth_cookie
    if not token:
        raise HTTPException(status_code=401, detail="Missing access token")
    try:
        claims = decode_access_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    role = claims.get("role")
    user_id = claims.get("sub")
    tenant_id = claims.get("tenant_id")
    if role not in {"learner", "recruiter", "admin", "content_editor", "mentor"}:
        raise HTTPException(status_code=403, detail="Unsupported role")
    if not user_id or not tenant_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return UserContext(user_id=user_id, role=role, tenant_id=tenant_id)  # type: ignore[arg-type]
