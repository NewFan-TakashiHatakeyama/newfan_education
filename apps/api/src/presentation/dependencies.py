from __future__ import annotations

from dataclasses import dataclass

from fastapi import Cookie, Header, HTTPException
from fastapi.security import OAuth2PasswordBearer

from application.services import (
    AuditLogService,
    AuthService,
    ApplicationService,
    CompanyService,
    ConsentService,
    CourseService,
    CurriculumImpactService,
    CurriculumService,
    GoalService,
    MessageService,
    MessageTemplateService,
    ModerationService,
    NotificationService,
    OpportunityService,
    OpportunityApplicationService,
    PortfolioArtifactService,
    PublicProfileSettingService,
    ProgressService,
    RoadmapService,
    SkillGapService,
    UserManagementService,
)
from application.b2b_services import B2BService
from domain.models import (
    Company,
    CurriculumVersion,
    Message,
    MessageTemplate,
    MessageThread,
    ModerationCase,
    NotificationDeliverySetting,
    Notification,
    Opportunity,
    PortfolioArtifact,
    PublicProfileSetting,
    UserAccount,
    UserContext,
)
from infrastructure.auth import decode_access_token
from infrastructure.db import Base, SessionLocal, engine
from infrastructure.course_seed import default_courses
from infrastructure.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryCompanyRepository,
    InMemoryConsentRepository,
    InMemoryCourseRepository,
    InMemoryCurriculumRepository,
    InMemoryGoalRepository,
    InMemoryMessageRepository,
    InMemoryMessageTemplateAuditLogRepository,
    InMemoryMessageTemplateRepository,
    InMemoryModerationRepository,
    InMemoryNotificationDeliverySettingRepository,
    InMemoryNotificationRepository,
    InMemoryOpportunityRepository,
    InMemoryOpportunityApplicationRepository,
    InMemoryPortfolioArtifactRepository,
    InMemoryPublicProfileSettingRepository,
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
    course_service: CourseService
    progress_service: ProgressService
    skill_gap_service: SkillGapService
    opportunity_service: OpportunityService
    opportunity_application_service: OpportunityApplicationService
    application_service: ApplicationService
    company_service: CompanyService
    moderation_service: ModerationService
    portfolio_artifact_service: PortfolioArtifactService
    curriculum_impact_service: CurriculumImpactService
    notification_service: NotificationService
    message_service: MessageService
    message_template_service: MessageTemplateService
    public_profile_setting_service: PublicProfileSettingService
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
            # Seed one published curriculum so roadmap generation works immediately.
            # Path points to the checked-in MDX sample in content/curriculum.
            CurriculumVersion(
                curriculum_slug="python-basic",
                version="1.0.0",
                title="Pythonの変数",
                mdx_path="content/curriculum/python-basic/variables-v1.mdx",
                skill_tags=["python.syntax.variables"],
                difficulty=1,
                estimated_minutes=20,
            ),
            CurriculumVersion(
                curriculum_slug="python-fastapi",
                version="1.0.0",
                title="FastAPI 入門",
                mdx_path="content/curriculum/python-fastapi/intro-v1.mdx",
                skill_tags=["python.api.fastapi"],
                difficulty=2,
                estimated_minutes=35,
            ),
        ]
    )
    course_repo = InMemoryCourseRepository(initial_values=default_courses())
    progress_repo = InMemoryProgressRepository()
    opportunity_repo = InMemoryOpportunityRepository(
        initial_values=[
            Opportunity(
                id="job-001",
                type="employment",
                title="Python Backend Engineer",
                provider="株式会社Example",
                contract_type="正社員",
                compensation="年収 520万〜680万円",
                skill_match_score=86,
                caution="週3日以上の出社が必要",
                summary="FastAPI と PostgreSQL を用いた学習系サービス開発。",
                required_skills=["Python", "FastAPI", "SQL", "Git"],
                payment_terms="月給制 / 試用期間3か月",
                is_recommended=True,
                is_saved=True,
            ),
            Opportunity(
                id="proj-101",
                type="freelance",
                title="学習進捗ダッシュボード改修案件",
                provider="Data Team合同会社",
                contract_type="業務委託（準委任）",
                compensation="月額 55万円",
                skill_match_score=79,
                caution="納期3週間 / 週2回レビュー",
                summary="Next.js + FastAPI の既存画面改善および指標追加。",
                required_skills=["Next.js", "TypeScript", "FastAPI"],
                payment_terms="月末締め翌月末払い",
                is_recommended=True,
            ),
            Opportunity(
                id="job-002",
                type="employment",
                title="Junior API Engineer",
                provider="Alpha Learning",
                contract_type="契約社員",
                compensation="年収 420万〜520万円",
                skill_match_score=72,
                caution="英語ドキュメント読解が必要",
                summary="教育系APIの運用改善とテスト追加。",
                required_skills=["Python", "API設計", "テスト"],
                payment_terms="月給制 / 契約更新あり",
            ),
        ]
    )
    opportunity_application_repo = InMemoryOpportunityApplicationRepository()
    company_repo = InMemoryCompanyRepository(
        initial_values=[
            Company(
                id="company-example",
                name="株式会社Example",
                industry="EdTech",
                status="active",
                open_opportunity_count=2,
                contact_email="recruit@example.co.jp",
                contact_person_name="山田 太郎",
                contact_person_phone="+81-90-0000-1111",
            ),
            Company(
                id="company-data-team",
                name="Data Team合同会社",
                industry="Data Consulting",
                status="stopped",
                open_opportunity_count=1,
                contact_email="biz@datateam.co.jp",
                contact_person_name="鈴木 花子",
                contact_person_phone="+81-90-2222-3333",
            ),
            Company(
                id="company-alpha",
                name="Alpha Learning",
                industry="Learning Platform",
                status="active",
                open_opportunity_count=1,
                contact_email="contact@alpha-learning.jp",
                contact_person_name="佐藤 次郎",
                contact_person_phone="+81-90-4444-5555",
            ),
        ]
    )
    moderation_repo = InMemoryModerationRepository(
        initial_values=[
            ModerationCase(
                id="mod-001",
                target_type="message",
                target_id="thread-unsafe-1",
                reason="スパムに該当する可能性",
                status="accepted",
                reported_by="demo-user",
                due_at="2025-01-10T09:00:00+00:00",
            ),
            ModerationCase(
                id="mod-002",
                target_type="portfolio",
                target_id="artifact-unsafe-1",
                reason="個人情報の露出が疑われる",
                status="investigating",
                reported_by="recruiter-user",
                assigned_admin="admin-user",
                due_at="2099-01-10T09:00:00+00:00",
            ),
        ]
    )
    portfolio_artifact_repo = InMemoryPortfolioArtifactRepository(
        initial_values=[
            PortfolioArtifact(
                id="artifact-fastapi-todo",
                user_id="demo-user",
                title="FastAPI Todo API",
                summary="認証付きCRUD APIを実装し、テストとOpenAPIを整備。",
                skill_tags=["Python", "FastAPI", "SQLAlchemy", "Pytest"],
                related_skills=["REST API設計", "テスト自動化", "CI/CD"],
                evidence_links=[
                    "https://github.com/demo/fastapi-todo",
                    "https://demo.example.com/fastapi-todo",
                ],
                visibility="public",
                evaluation="A",
                evaluation_history=[
                    {
                        "evaluatedAt": "2026-05-10T10:00:00+00:00",
                        "evaluator": "mentor-01",
                        "score": "B+",
                        "comment": "基礎要件を満たしています。",
                    },
                    {
                        "evaluatedAt": "2026-05-20T10:00:00+00:00",
                        "evaluator": "mentor-02",
                        "score": "A",
                        "comment": "テスト観点が改善されました。",
                    },
                ],
            ),
            PortfolioArtifact(
                id="artifact-python-basic",
                user_id="demo-user",
                title="Python基礎課題",
                summary="基礎文法・アルゴリズム課題を提出しレビュー完了。",
                skill_tags=["Python", "Algorithm", "Git"],
                related_skills=["データ構造", "問題分解"],
                evidence_links=["https://github.com/demo/python-basic"],
                visibility="limited",
                evaluation="B+",
                evaluation_history=[
                    {
                        "evaluatedAt": "2026-04-30T10:00:00+00:00",
                        "evaluator": "mentor-01",
                        "score": "B+",
                        "comment": "ロジックは明確で、境界値テストが今後の課題。",
                    }
                ],
            ),
        ]
    )
    notification_repo = InMemoryNotificationRepository(
        initial_values=[
            Notification(
                user_id="demo-user",
                category="learning",
                title="受講中の教材が更新されました",
                body="FastAPI 入門 v1.1 の差分を確認してください。",
                target_url="/learn/python-fastapi/lesson",
                is_important=True,
            ),
            Notification(
                user_id="demo-user",
                category="career",
                title="応募ステータスが更新されました",
                body="Python Backend Engineer の応募がレビュー中です。",
                target_url="/career",
            ),
            Notification(
                user_id="demo-user",
                category="dm",
                title="新しいメッセージがあります",
                body="Data Team合同会社から相談メッセージが届きました。",
                target_url="/messages",
            ),
            Notification(
                user_id="demo-user",
                category="admin",
                title="教材公開申請があります",
                body="Pythonの変数 v1.0.1 の公開承認待ちです。",
                target_url="/admin/curriculum",
            ),
        ]
    )
    message_thread_general = MessageThread(
        owner_user_id="demo-user",
        channel="dm",
        counterpart_name="Data Team合同会社",
        related_opportunity_label="学習進捗ダッシュボード改修案件",
        can_send=True,
        restriction_reason=None,
        context_summary="応募前の技術相談",
        unread_count=1,
    )
    message_thread_limited = MessageThread(
        owner_user_id="demo-user",
        channel="applications",
        counterpart_name="株式会社Example",
        related_opportunity_label="Python Backend Engineer",
        can_send=False,
        restriction_reason="このユーザーはDMを許可していません",
        context_summary="接触同意待ち",
        unread_count=0,
    )
    message_repo = InMemoryMessageRepository(
        initial_threads=[message_thread_general, message_thread_limited],
        initial_messages=[
            Message(
                thread_id=message_thread_general.id,
                sender_user_id="company-user",
                body="ポートフォリオを拝見しました。案件要件に興味はありますか？",
                attachments=[],
            ),
            Message(
                thread_id=message_thread_general.id,
                sender_user_id="demo-user",
                body="ありがとうございます。稼働条件を確認したいです。",
                attachments=[],
            ),
            Message(
                thread_id=message_thread_limited.id,
                sender_user_id="company-user-example",
                body="接触許可が有効になり次第、面談候補日をお送りします。",
                attachments=[],
            ),
        ],
    )
    message_template_repo = InMemoryMessageTemplateRepository(
        initial_values=[
            MessageTemplate(
                key="learner_intro",
                label="初回挨拶",
                body="はじめまして。プロフィールを拝見し、ご相談したくご連絡しました。",
                target_roles=["learner"],
                channels=["dm", "applications"],
            ),
            MessageTemplate(
                key="learner_schedule",
                label="日程確認",
                body="ありがとうございます。30分ほどお時間をいただける候補日を2-3ついただけますか？",
                target_roles=["learner"],
                channels=["dm", "applications", "teams"],
            ),
            MessageTemplate(
                key="recruiter_followup",
                label="営業フォロー",
                body="ご検討状況の確認です。追加で必要な情報があればご連絡ください。",
                target_roles=["recruiter"],
                channels=["applications"],
            ),
            MessageTemplate(
                key="admin_notice",
                label="運営連絡",
                body="運営からのお知らせです。対応期限をご確認ください。",
                target_roles=["admin", "content_editor"],
                channels=["dm", "teams"],
            ),
        ]
    )
    message_template_audit_log_repo = InMemoryMessageTemplateAuditLogRepository()
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
    public_profile_setting_repo = InMemoryPublicProfileSettingRepository(
        initial_values=[
            PublicProfileSetting(
                user_id="demo-user",
                visibility="limited",
                show_goal=True,
                show_skill_evidence=True,
                show_portfolio=True,
                allow_recruiter_contact=True,
            )
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
        course_service=CourseService(course_repo),
        progress_service=ProgressService(progress_repo, roadmap_repo),
        skill_gap_service=SkillGapService(goal_repo, roadmap_repo, progress_repo),
        opportunity_service=OpportunityService(opportunity_repo),
        opportunity_application_service=OpportunityApplicationService(
            opportunity_application_repo,
            opportunity_repo,
            audit_log_repo,
        ),
        application_service=ApplicationService(opportunity_application_repo, opportunity_repo),
        company_service=CompanyService(company_repo, audit_log_repo),
        moderation_service=ModerationService(moderation_repo, audit_log_repo),
        portfolio_artifact_service=PortfolioArtifactService(portfolio_artifact_repo),
        curriculum_impact_service=CurriculumImpactService(roadmap_repo),
        notification_service=NotificationService(notification_repo, notification_delivery_setting_repo),
        message_service=MessageService(message_repo),
        message_template_service=MessageTemplateService(
            message_template_repo,
            message_template_audit_log_repo,
            audit_log_repo,
        ),
        public_profile_setting_service=PublicProfileSettingService(
            public_profile_setting_repo,
            audit_log_repo,
        ),
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
