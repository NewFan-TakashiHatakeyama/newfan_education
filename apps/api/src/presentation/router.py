from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Response

from domain.models import Course, UserContext
from presentation.dependencies import CONTAINER, get_current_user
from infrastructure.auth import create_access_token, hash_password, verify_password
from infrastructure.settings import load_settings
from presentation.schemas import (
    AssignRoadmapRequest,
    AssignRoadmapResponse,
    B2BCompanyResponse,
    EvidenceItemsResponse,
    ExerciseResponse,
    ExerciseRunRequest,
    ExerciseRunResponse,
    ExerciseSubmitRequest,
    FitAssessmentResponse,
    FitAssessmentListResponse,
    LearnerSummaryResponse,
    LearnersResponse,
    MentorReviewRequest,
    ReportResponse,
    RequirementCreateRequest,
    RequirementResponse,
    RequirementsResponse,
    RoleTemplatesResponse,
    ReviewResponse,
    SalesSummaryCreateRequest,
    SubmissionResponse,
    SubmissionsResponse,
    ApplicationsResponse,
    AuditLogEventsResponse,
    AuthSessionResponse,
    AuthSignInRequest,
    AuthSignUpRequest,
    InviteCsvRequest,
    InviteCsvResponse,
    InviteRequest,
    InviteResponse,
    ReportExportJobResponse,
    ReportExportRequest,
    TeamCreateRequest,
    TeamResponse,
    TeamsResponse,
    CompanyBulkStatusPatchRequest,
    CompanyBulkStatusPatchResponse,
    CompanyPatchRequest,
    CompanyResponse,
    CompaniesResponse,
    ConsentCreateRequest,
    ConsentResponse,
    CourseCategoriesResponse,
    CourseCategoryResponse,
    CourseDetailResponse,
    CourseLessonResponse,
    CourseSectionResponse,
    CourseSummaryResponse,
    CoursesResponse,
    CourseTrendingResponse,
    CurriculumPublishRequest,
    CurriculumImpactResponse,
    CurriculumVersionResponse,
    DashboardResponse,
    GoalCreateRequest,
    GoalResponse,
    ModerationBulkCloseRequest,
    ModerationBulkCloseResponse,
    ModerationCasePatchRequest,
    ModerationCaseResponse,
    ModerationCasesResponse,
    MessageThreadDetailResponse,
    MessageThreadsResponse,
    MessageTemplateResponse,
    MessageTemplateCreateRequest,
    MessageTemplateAuditLogsResponse,
    MessageTemplateDeleteResponse,
    MessageTemplatePatchRequest,
    MessageTemplatesResponse,
    MessageResponse,
    NotificationReadAllResponse,
    NotificationReadResponse,
    NotificationDeliverySettingPatchRequest,
    NotificationDeliverySettingResponse,
    NotificationDeliverySettingsResponse,
    NotificationsResponse,
    OpportunityApplicationsResponse,
    OpportunityApplicationProgressPatchRequest,
    OpportunityApplicationStateResponse,
    OpportunityApplyRequest,
    OpportunitiesResponse,
    PortfolioArtifactResponse,
    PortfolioArtifactsResponse,
    PublicProfileSettingPatchRequest,
    PublicProfileSettingResponse,
    ProgressEventRequest,
    ProgressEventResponse,
    RoadmapGenerateRequest,
    RoadmapItemResponse,
    RoadmapResponse,
    SendMessageRequest,
    SkillsGapResponse,
    UserAccountPatchRequest,
    UserAccountResponse,
    UserAccountsResponse,
)

router = APIRouter(prefix="/api/v1", tags=["priority-settings"])
LEGACY_B2C_ENABLED = False


def _ensure_legacy_b2c_enabled() -> None:
    if not LEGACY_B2C_ENABLED:
        raise HTTPException(
            status_code=410,
            detail="Legacy B2C career/message/profile/portfolio features are retired",
        )


def _to_consent_response(consent) -> ConsentResponse:
    return ConsentResponse(
        id=consent.id,
        userId=consent.user_id,
        consentType=consent.consent_type,
        granted=consent.granted,
        grantedAt=consent.granted_at,
    )


def _to_goal_response(goal) -> GoalResponse:
    return GoalResponse(
        id=goal.id,
        userId=goal.user_id,
        title=goal.title,
        targetRole=goal.target_role,
        availableHoursPerWeek=goal.available_hours_per_week,
        createdAt=goal.created_at,
    )


def _to_roadmap_response(roadmap) -> RoadmapResponse:
    return RoadmapResponse(
        id=roadmap.id,
        userId=roadmap.user_id,
        goalId=roadmap.goal_id,
        generatedAt=roadmap.generated_at,
        items=[
            RoadmapItemResponse(
                id=item.id,
                title=item.title,
                difficulty=item.difficulty,
                estimatedMinutes=item.estimated_minutes,
                curriculumVersionId=item.curriculum_version_id,
                prerequisiteSkillTags=item.prerequisite_skill_tags,
            )
            for item in roadmap.items
        ],
    )


def _to_curriculum_response(value) -> CurriculumVersionResponse:
    return CurriculumVersionResponse(
        id=value.id,
        curriculumSlug=value.curriculum_slug,
        version=value.version,
        title=value.title,
        mdxPath=value.mdx_path,
        published=value.published,
        skillTags=value.skill_tags,
        difficulty=value.difficulty,
        estimatedMinutes=value.estimated_minutes,
    )


@router.post("/auth/sign-in", response_model=AuthSessionResponse)
def sign_in(payload: AuthSignInRequest, response: Response):
    settings = load_settings()
    user = CONTAINER.b2b_service.repository.get_user_by_email(payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    access_token = create_access_token(
        user_id=user.user_id,
        role=user.role,
        tenant_id=user.tenant_id,
        display_name=user.display_name,
    )
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
    )
    return {
        "accessToken": access_token,
        "tokenType": "bearer",
        "expiresIn": settings.access_token_expire_minutes * 60,
        "userId": user.user_id,
        "displayName": user.display_name,
        "role": user.role,
        "state": user.state,
        "tenantId": user.tenant_id,
    }


@router.post("/auth/sign-up", response_model=AuthSessionResponse)
def sign_up(payload: AuthSignUpRequest, response: Response):
    settings = load_settings()
    existing_user = CONTAINER.b2b_service.repository.get_user_by_user_id(payload.userId)
    if existing_user is not None:
        raise HTTPException(status_code=409, detail="User already exists")
    existing_email = CONTAINER.b2b_service.repository.get_user_by_email(payload.email)
    if existing_email is not None:
        raise HTTPException(status_code=409, detail="Email already exists")
    created = CONTAINER.b2b_service.repository.create_user(
        user_id=payload.userId,
        email=payload.email,
        display_name=payload.displayName,
        role=payload.role,
        tenant_id=payload.tenantId,
        password_hash_value=hash_password(payload.password),
    )
    access_token = create_access_token(
        user_id=created.user_id,
        role=created.role,
        tenant_id=created.tenant_id,
        display_name=created.display_name,
    )
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
    )
    return {
        "accessToken": access_token,
        "tokenType": "bearer",
        "expiresIn": settings.access_token_expire_minutes * 60,
        "userId": created.user_id,
        "displayName": created.display_name,
        "role": created.role,
        "state": created.state,
        "tenantId": created.tenant_id,
    }


@router.get("/auth/me", response_model=AuthSessionResponse)
def auth_me(actor: UserContext = Depends(get_current_user)):
    settings = load_settings()
    user = CONTAINER.b2b_service.repository.get_user_by_user_id(actor.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    access_token = create_access_token(
        user_id=user.user_id,
        role=user.role,
        tenant_id=user.tenant_id,
        display_name=user.display_name,
    )
    return {
        "accessToken": access_token,
        "tokenType": "bearer",
        "expiresIn": settings.access_token_expire_minutes * 60,
        "userId": user.user_id,
        "displayName": user.display_name,
        "role": user.role,
        "state": user.state,
        "tenantId": user.tenant_id,
    }


@router.post("/auth/sign-out")
def sign_out(response: Response):
    response.delete_cookie(load_settings().auth_cookie_name)
    return {"signedOut": True}


@router.post("/consents", response_model=ConsentResponse)
def create_consent(
    payload: ConsentCreateRequest,
    actor: UserContext = Depends(get_current_user),
):
    created = CONTAINER.consent_service.create(actor, payload.consentType, payload.granted)
    return _to_consent_response(created)


@router.get("/consents/me", response_model=list[ConsentResponse])
def list_my_consents(actor: UserContext = Depends(get_current_user)):
    return [_to_consent_response(value) for value in CONTAINER.consent_service.list_mine(actor)]


@router.post("/goals", response_model=GoalResponse)
def create_goal(
    payload: GoalCreateRequest,
    actor: UserContext = Depends(get_current_user),
):
    goal = CONTAINER.goal_service.create(
        actor=actor,
        title=payload.title,
        target_role=payload.targetRole,
        available_hours_per_week=payload.availableHoursPerWeek,
    )
    return _to_goal_response(goal)


@router.post("/roadmaps/generate", response_model=RoadmapResponse)
def generate_roadmap(
    payload: RoadmapGenerateRequest,
    actor: UserContext = Depends(get_current_user),
):
    try:
        roadmap = CONTAINER.roadmap_service.generate(
            actor=actor,
            goal_id=payload.goalId,
            preferred_difficulty=payload.preferredDifficulty,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return _to_roadmap_response(roadmap)


@router.get("/roadmaps/{roadmap_id}", response_model=RoadmapResponse)
def get_roadmap(roadmap_id: str, actor: UserContext = Depends(get_current_user)):
    try:
        roadmap = CONTAINER.roadmap_service.get(actor=actor, roadmap_id=roadmap_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return _to_roadmap_response(roadmap)


@router.get("/curriculum", response_model=list[CurriculumVersionResponse])
def list_curriculum(actor: UserContext = Depends(get_current_user)):
    values = CONTAINER.b2b_service.list_curriculum_versions(actor)
    return values


@router.get("/curriculum/{curriculum_version_id}", response_model=CurriculumVersionResponse)
def get_curriculum_version(curriculum_version_id: str, actor: UserContext = Depends(get_current_user)):
    values = CONTAINER.b2b_service.list_curriculum_versions(actor)
    value = next((item for item in values if item["id"] == curriculum_version_id), None)
    if value is None:
        raise HTTPException(status_code=404, detail="Curriculum version not found")
    return value


@router.post("/admin/curriculum/publish", response_model=CurriculumVersionResponse)
def publish_curriculum(
    payload: CurriculumPublishRequest,
    actor: UserContext = Depends(get_current_user),
):
    if actor.role not in {"content_editor", "admin"}:
        raise HTTPException(status_code=403, detail="Only content editor can publish curriculum")
    created = CONTAINER.b2b_service.repository.publish_curriculum(
        actor.tenant_id,
        payload={
            "curriculumSlug": payload.curriculumSlug,
            "version": payload.version,
            "title": payload.title,
            "mdxPath": payload.mdxPath,
            "skillTags": payload.skillTags,
            "difficulty": payload.difficulty,
            "estimatedMinutes": payload.estimatedMinutes,
        },
    )
    learners = CONTAINER.b2b_service.repository.list_learners(actor.tenant_id)
    for learner in learners:
        CONTAINER.b2b_service.repository.enqueue_notification_job(
            tenant_id=actor.tenant_id,
            user_id=learner["id"],
            category="learning",
            title="教材が公開されました",
            body=f"{created['title']} ({created['version']}) が公開されました。",
            target_url="/learner/learn",
            channels=["in_app"],
            is_important=True,
        )
    CONTAINER.b2b_service.repository.append_audit_log(
        tenant_id=actor.tenant_id,
        event_type="curriculum.published",
        resource_type="curriculum_version",
        resource_id=created["id"],
        action="publish",
        actor_user_id=actor.user_id,
        actor_role=actor.role,
        summary=f"教材公開と通知対象計算を実行 ({len(learners)} users)",
        metadata={"notificationTargets": str(len(learners))},
    )
    return created


def _to_course_summary(course: Course) -> CourseSummaryResponse:
    return CourseSummaryResponse(
        id=course.id,
        slug=course.slug,
        title=course.title,
        subtitle=course.subtitle,
        category=course.category,
        level=course.level,
        instructor=course.instructor,
        summary=course.summary,
        tags=course.tags,
        rating=course.rating,
        ratingCount=course.rating_count,
        enrolledCount=course.enrolled_count,
        isBestseller=course.is_bestseller,
        isTopRated=course.is_top_rated,
        totalLessons=course.total_lessons,
        totalExercises=course.total_exercises,
        estimatedMinutes=course.estimated_minutes,
        updatedAt=course.updated_at,
    )


def _to_course_detail(course: Course) -> CourseDetailResponse:
    sections = [
        CourseSectionResponse(
            title=section.title,
            lessonCount=len(section.lessons),
            estimatedMinutes=sum(lesson.estimated_minutes for lesson in section.lessons),
            lessons=[
                CourseLessonResponse(
                    lessonSlug=lesson.lesson_slug,
                    title=lesson.title,
                    kind=lesson.kind,
                    estimatedMinutes=lesson.estimated_minutes,
                    skillTags=lesson.skill_tags,
                    contentRef=lesson.content_ref,
                    exerciseId=lesson.exercise_id,
                    isPreview=lesson.is_preview,
                )
                for lesson in section.lessons
            ],
        )
        for section in course.sections
    ]
    return CourseDetailResponse(
        **_to_course_summary(course).model_dump(),
        description=course.description,
        outcomes=course.outcomes,
        targetAudience=course.target_audience,
        prerequisites=course.prerequisites,
        sections=sections,
    )


@router.get("/courses", response_model=CoursesResponse)
def list_courses(
    q: str | None = None,
    category: str | None = None,
    level: str | None = None,
    sort: str = "popular",
    actor: UserContext = Depends(get_current_user),
):
    courses = CONTAINER.course_service.list_courses(
        query=q,
        category=category,
        level=level,
        sort=sort,
    )
    return CoursesResponse(items=[_to_course_summary(course) for course in courses])


@router.get("/courses/categories", response_model=CourseCategoriesResponse)
def list_course_categories(actor: UserContext = Depends(get_current_user)):
    categories = CONTAINER.course_service.list_categories()
    return CourseCategoriesResponse(
        items=[
            CourseCategoryResponse(category=category, courseCount=count)
            for category, count in categories
        ]
    )


@router.get("/courses/trending", response_model=CourseTrendingResponse)
def list_course_trending(actor: UserContext = Depends(get_current_user)):
    return CourseTrendingResponse(items=CONTAINER.course_service.list_trending())


@router.get("/courses/{slug}", response_model=CourseDetailResponse)
def get_course(slug: str, actor: UserContext = Depends(get_current_user)):
    course = CONTAINER.course_service.get_course(slug)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return _to_course_detail(course)


@router.post("/progress/events", response_model=ProgressEventResponse)
def post_progress_event(
    payload: ProgressEventRequest,
    actor: UserContext = Depends(get_current_user),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key header is required")
    try:
        accepted = CONTAINER.progress_service.track(
            actor=actor,
            roadmap_id=payload.roadmapId,
            roadmap_item_id=payload.roadmapItemId,
            event_type=payload.eventType,
            idempotency_key=idempotency_key,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return ProgressEventResponse(accepted=accepted)


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(actor: UserContext = Depends(get_current_user)):
    return CONTAINER.progress_service.dashboard(actor)


@router.get("/skills/gap", response_model=SkillsGapResponse)
def get_skills_gap(actor: UserContext = Depends(get_current_user)):
    return CONTAINER.skill_gap_service.get_gap(actor)


@router.get("/opportunities", response_model=OpportunitiesResponse)
def list_opportunities(
    type: str | None = None,
    recommended: bool = False,
    saved: bool = False,
):
    _ensure_legacy_b2c_enabled()
    return CONTAINER.opportunity_service.list_catalog(
        opportunity_type=type,
        recommended_only=recommended,
        saved_only=saved,
    )


@router.get("/opportunities/applications/me", response_model=OpportunityApplicationsResponse)
def list_my_opportunity_applications(actor: UserContext = Depends(get_current_user)):
    _ensure_legacy_b2c_enabled()
    return CONTAINER.opportunity_application_service.list_mine(actor)


@router.get("/applications/me", response_model=ApplicationsResponse)
def list_my_applications(
    state: str | None = None,
    opportunityType: str | None = None,
    updatedFrom: str | None = None,
    updatedTo: str | None = None,
    actor: UserContext = Depends(get_current_user),
):
    _ensure_legacy_b2c_enabled()
    return CONTAINER.application_service.list_mine(
        actor=actor,
        state=state,
        opportunity_type=opportunityType,
        updated_from=updatedFrom,
        updated_to=updatedTo,
    )


@router.post(
    "/opportunities/{opportunity_id}/apply",
    response_model=OpportunityApplicationStateResponse,
)
def apply_opportunity(
    opportunity_id: str,
    payload: OpportunityApplyRequest,
    actor: UserContext = Depends(get_current_user),
):
    _ensure_legacy_b2c_enabled()
    try:
        return CONTAINER.opportunity_application_service.apply(
            actor=actor,
            opportunity_id=opportunity_id,
            opportunity_type=payload.opportunityType,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/opportunities/{opportunity_id}/withdraw",
    response_model=OpportunityApplicationStateResponse,
)
def withdraw_opportunity(
    opportunity_id: str,
    actor: UserContext = Depends(get_current_user),
):
    _ensure_legacy_b2c_enabled()
    try:
        return CONTAINER.opportunity_application_service.withdraw(
            actor=actor,
            opportunity_id=opportunity_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch(
    "/opportunities/{opportunity_id}/state",
    response_model=OpportunityApplicationStateResponse,
)
def patch_opportunity_state(
    opportunity_id: str,
    payload: OpportunityApplicationProgressPatchRequest,
    actor: UserContext = Depends(get_current_user),
):
    _ensure_legacy_b2c_enabled()
    try:
        return CONTAINER.opportunity_application_service.update_progress_state(
            actor=actor,
            opportunity_id=opportunity_id,
            state=payload.state,
        )
    except ValueError as exc:
        if str(exc) == "Opportunity not found":
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/portfolio/artifacts/me", response_model=PortfolioArtifactsResponse)
def list_my_portfolio_artifacts(actor: UserContext = Depends(get_current_user)):
    _ensure_legacy_b2c_enabled()
    return CONTAINER.portfolio_artifact_service.list_mine(actor)


@router.get("/portfolio/artifacts/{artifact_id}", response_model=PortfolioArtifactResponse)
def get_my_portfolio_artifact(
    artifact_id: str,
    actor: UserContext = Depends(get_current_user),
):
    _ensure_legacy_b2c_enabled()
    try:
        return CONTAINER.portfolio_artifact_service.get_mine(actor, artifact_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get(
    "/admin/curriculum/{curriculum_version_id}/impact",
    response_model=CurriculumImpactResponse,
)
def analyze_curriculum_impact(
    curriculum_version_id: str,
    actor: UserContext = Depends(get_current_user),
):
    if actor.role not in {"content_editor", "admin"}:
        raise HTTPException(status_code=403, detail="Only content editor can view impact")
    return CONTAINER.curriculum_impact_service.analyze(curriculum_version_id)


@router.get("/notifications", response_model=NotificationsResponse)
def list_notifications(
    tab: str = "all",
    unread: bool = False,
    actor: UserContext = Depends(get_current_user),
):
    return CONTAINER.b2b_service.list_notifications(actor, tab=tab, unread_only=unread)


@router.post("/notifications/{notification_id}/read", response_model=NotificationReadResponse)
def mark_notification_read(
    notification_id: str,
    actor: UserContext = Depends(get_current_user),
):
    try:
        return CONTAINER.b2b_service.mark_notification_read(actor, notification_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/notifications/read-all", response_model=NotificationReadAllResponse)
def mark_all_notifications_read(actor: UserContext = Depends(get_current_user)):
    return CONTAINER.b2b_service.mark_all_notifications_read(actor)


@router.get("/notifications/settings", response_model=NotificationDeliverySettingsResponse)
def list_notification_delivery_settings(actor: UserContext = Depends(get_current_user)):
    return CONTAINER.b2b_service.list_notification_delivery_settings(actor)


@router.patch(
    "/notifications/settings/{category}",
    response_model=NotificationDeliverySettingResponse,
)
def patch_notification_delivery_setting(
    category: str,
    payload: NotificationDeliverySettingPatchRequest,
    actor: UserContext = Depends(get_current_user),
):
    try:
        return CONTAINER.b2b_service.update_notification_delivery_setting(
            actor,
            category=category,
            email_enabled=payload.emailEnabled,
            in_app_enabled=payload.inAppEnabled,
            push_enabled=payload.pushEnabled,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/messages/threads", response_model=MessageThreadsResponse)
def list_message_threads(
    q: str | None = None,
    unread: bool = False,
    actor: UserContext = Depends(get_current_user),
):
    _ensure_legacy_b2c_enabled()
    return CONTAINER.message_service.list_threads(actor, query=q, unread_only=unread)


@router.get("/messages/threads/{thread_id}", response_model=MessageThreadDetailResponse)
def get_message_thread_detail(
    thread_id: str,
    actor: UserContext = Depends(get_current_user),
):
    _ensure_legacy_b2c_enabled()
    try:
        return CONTAINER.message_service.get_thread_detail(actor, thread_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/messages/threads/{thread_id}/messages", response_model=MessageResponse)
def send_message(
    thread_id: str,
    payload: SendMessageRequest,
    actor: UserContext = Depends(get_current_user),
):
    _ensure_legacy_b2c_enabled()
    try:
        return CONTAINER.message_service.send_message(
            actor=actor,
            thread_id=thread_id,
            body=payload.body,
            attachments=payload.attachments,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/messages/templates", response_model=MessageTemplatesResponse)
def list_message_templates(
    role: str | None = None,
    channel: str | None = None,
    actor: UserContext = Depends(get_current_user),
):
    _ensure_legacy_b2c_enabled()
    try:
        return CONTAINER.message_template_service.list_templates(
            actor=actor,
            role=role,
            channel=channel,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/messages/templates", response_model=MessageTemplateResponse)
def create_message_template(
    payload: MessageTemplateCreateRequest,
    actor: UserContext = Depends(get_current_user),
):
    _ensure_legacy_b2c_enabled()
    try:
        return CONTAINER.message_template_service.create_template(
            actor=actor,
            key=payload.key,
            label=payload.label,
            body=payload.body,
            target_roles=payload.targetRoles,
            channels=payload.channels,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/messages/templates/{template_id}", response_model=MessageTemplateResponse)
def patch_message_template(
    template_id: str,
    payload: MessageTemplatePatchRequest,
    actor: UserContext = Depends(get_current_user),
):
    _ensure_legacy_b2c_enabled()
    try:
        return CONTAINER.message_template_service.update_template(
            actor=actor,
            template_id=template_id,
            key=payload.key,
            label=payload.label,
            body=payload.body,
            target_roles=payload.targetRoles,
            channels=payload.channels,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        if str(exc) == "Template not found":
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/messages/templates/{template_id}", response_model=MessageTemplateDeleteResponse)
def delete_message_template(
    template_id: str,
    actor: UserContext = Depends(get_current_user),
):
    _ensure_legacy_b2c_enabled()
    try:
        return CONTAINER.message_template_service.delete_template(
            actor=actor,
            template_id=template_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/admin/messages/templates/audit-logs", response_model=MessageTemplateAuditLogsResponse)
def list_message_template_audit_logs(
    limit: int = 100,
    actor: UserContext = Depends(get_current_user),
):
    _ensure_legacy_b2c_enabled()
    try:
        return CONTAINER.message_template_service.list_audit_logs(actor, limit=limit)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/public-profile/settings/me", response_model=PublicProfileSettingResponse)
def get_public_profile_settings(actor: UserContext = Depends(get_current_user)):
    _ensure_legacy_b2c_enabled()
    return CONTAINER.public_profile_setting_service.get_mine(actor)


@router.patch("/public-profile/settings/me", response_model=PublicProfileSettingResponse)
def patch_public_profile_settings(
    payload: PublicProfileSettingPatchRequest,
    actor: UserContext = Depends(get_current_user),
):
    _ensure_legacy_b2c_enabled()
    return CONTAINER.public_profile_setting_service.update_mine(
        actor=actor,
        visibility=payload.visibility,
        show_goal=payload.showGoal,
        show_skill_evidence=payload.showSkillEvidence,
        show_portfolio=payload.showPortfolio,
        allow_recruiter_contact=payload.allowRecruiterContact,
    )


@router.get("/admin/users", response_model=UserAccountsResponse)
def list_admin_users(
    role: str | None = None,
    state: str | None = None,
    q: str | None = None,
    actor: UserContext = Depends(get_current_user),
):
    try:
        return CONTAINER.user_management_service.list_users(
            actor=actor,
            role=role,
            state=state,
            query=q,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.patch("/admin/users/{user_id}", response_model=UserAccountResponse)
def patch_admin_user(
    user_id: str,
    payload: UserAccountPatchRequest,
    actor: UserContext = Depends(get_current_user),
):
    try:
        return CONTAINER.user_management_service.update_user(
            actor=actor,
            user_id=user_id,
            role=payload.role,
            state=payload.state,
            display_name=payload.displayName,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        if str(exc) == "User not found":
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/admin/audit-logs", response_model=AuditLogEventsResponse)
def list_admin_audit_logs(
    limit: int = 100,
    eventType: str | None = None,
    actorUserId: str | None = None,
    resourceType: str | None = None,
    resourceId: str | None = None,
    occurredFrom: str | None = None,
    occurredTo: str | None = None,
    actor: UserContext = Depends(get_current_user),
):
    try:
        return CONTAINER.b2b_service.list_admin_audit_logs(
            actor=actor,
            limit=limit,
            event_type=eventType,
            actor_user_id=actorUserId,
            resource_type=resourceType,
            resource_id=resourceId,
            occurred_from=occurredFrom,
            occurred_to=occurredTo,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/company/settings")
def get_company_settings(actor: UserContext = Depends(get_current_user)):
    if actor.role not in {"admin", "recruiter", "content_editor"}:
        raise HTTPException(status_code=403, detail="Role is not allowed")
    return {
        "tenantId": actor.tenant_id,
        "branding": {"companyName": "Newfan Demo Company", "theme": "indigo"},
        "notifications": {"curriculumUpdate": True, "reportExport": True},
        "security": {"sessionTtlMinutes": load_settings().access_token_expire_minutes},
    }


@router.get("/admin/task-templates")
def list_admin_task_templates(actor: UserContext = Depends(get_current_user)):
    if actor.role not in {"admin", "content_editor"}:
        raise HTTPException(status_code=403, detail="Role is not allowed")
    return {
        "items": [
            {
                "id": "tpl-rag-eval",
                "title": "RAG評価タスク",
                "category": "rag",
                "defaultDifficulty": 3,
            },
            {
                "id": "tpl-sql-analysis",
                "title": "SQL分析タスク",
                "category": "sql",
                "defaultDifficulty": 2,
            },
            {
                "id": "tpl-ocr-structuring",
                "title": "OCR構造化タスク",
                "category": "ocr",
                "defaultDifficulty": 2,
            },
        ]
    }


@router.get("/admin/companies", response_model=CompaniesResponse)
def list_admin_companies(actor: UserContext = Depends(get_current_user)):
    try:
        return CONTAINER.company_service.list_companies(actor)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.patch("/admin/companies/{company_id}", response_model=CompanyResponse)
def patch_admin_company(
    company_id: str,
    payload: CompanyPatchRequest,
    actor: UserContext = Depends(get_current_user),
):
    try:
        return CONTAINER.company_service.update_company(
            actor=actor,
            company_id=company_id,
            status=payload.status,
            contact_person_name=payload.contactPersonName,
            contact_person_phone=payload.contactPersonPhone,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        if str(exc) == "Company not found":
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/admin/companies/status/bulk", response_model=CompanyBulkStatusPatchResponse)
def patch_admin_companies_bulk_status(
    payload: CompanyBulkStatusPatchRequest,
    actor: UserContext = Depends(get_current_user),
):
    try:
        return CONTAINER.company_service.bulk_update_status(
            actor=actor,
            company_ids=payload.companyIds,
            status=payload.status,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/admin/moderation", response_model=ModerationCasesResponse)
def list_admin_moderation_cases(
    pendingOnly: bool = False,
    overdueOnly: bool = False,
    actor: UserContext = Depends(get_current_user),
):
    try:
        return CONTAINER.moderation_service.list_cases(
            actor,
            pending_only=pendingOnly,
            overdue_only=overdueOnly,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.patch("/admin/moderation/{case_id}", response_model=ModerationCaseResponse)
def patch_admin_moderation_case(
    case_id: str,
    payload: ModerationCasePatchRequest,
    actor: UserContext = Depends(get_current_user),
):
    try:
        return CONTAINER.moderation_service.update_case(
            actor=actor,
            case_id=case_id,
            status=payload.status,
            assigned_admin=payload.assignedAdmin,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        if str(exc) == "Moderation case not found":
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/admin/moderation/close/bulk", response_model=ModerationBulkCloseResponse)
def patch_admin_moderation_bulk_close(
    payload: ModerationBulkCloseRequest,
    actor: UserContext = Depends(get_current_user),
):
    try:
        return CONTAINER.moderation_service.bulk_close(
            actor=actor,
            case_ids=payload.caseIds,
            assigned_admin=payload.assignedAdmin,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


def _company_id_or_default(company_id: str | None) -> str:
    return company_id or "company-demo"


@router.get("/companies/current", response_model=B2BCompanyResponse)
def get_current_company(
    actor: UserContext = Depends(get_current_user),
    x_company_id: str | None = Header(default=None, alias="X-Company-Id"),
):
    try:
        return CONTAINER.b2b_service.get_current_company(actor, _company_id_or_default(x_company_id))
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/learners", response_model=LearnersResponse)
def list_learners(
    actor: UserContext = Depends(get_current_user),
    x_company_id: str | None = Header(default=None, alias="X-Company-Id"),
):
    try:
        return CONTAINER.b2b_service.list_learners(actor, _company_id_or_default(x_company_id))
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/learners/{learner_id}", response_model=LearnerSummaryResponse)
def get_learner_detail(
    learner_id: str,
    actor: UserContext = Depends(get_current_user),
    x_company_id: str | None = Header(default=None, alias="X-Company-Id"),
):
    try:
        return CONTAINER.b2b_service.get_learner_detail(
            actor,
            _company_id_or_default(x_company_id),
            learner_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/role-templates", response_model=RoleTemplatesResponse)
def list_role_templates(
    actor: UserContext = Depends(get_current_user),
    x_company_id: str | None = Header(default=None, alias="X-Company-Id"),
):
    try:
        return CONTAINER.b2b_service.list_role_templates(actor, _company_id_or_default(x_company_id))
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/company/teams", response_model=TeamsResponse)
def list_company_teams(actor: UserContext = Depends(get_current_user)):
    try:
        return CONTAINER.b2b_service.list_teams(actor)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/company/teams", response_model=TeamResponse)
def create_company_team(
    payload: TeamCreateRequest,
    actor: UserContext = Depends(get_current_user),
):
    try:
        return CONTAINER.b2b_service.create_team(actor, payload.name, payload.description)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/company/invites", response_model=InviteResponse)
def invite_company_user(
    payload: InviteRequest,
    actor: UserContext = Depends(get_current_user),
):
    try:
        return CONTAINER.b2b_service.invite_user(
            actor=actor,
            email=payload.email,
            role=payload.role,
            team_id=payload.teamId,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/company/invites/csv-import", response_model=InviteCsvResponse)
def invite_company_users_from_csv(
    payload: InviteCsvRequest,
    actor: UserContext = Depends(get_current_user),
):
    try:
        return CONTAINER.b2b_service.bulk_invite_from_csv(
            actor=actor,
            csv_content=payload.csvContent,
            default_role=payload.defaultRole,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/roadmaps/assign", response_model=AssignRoadmapResponse)
def assign_roadmap(
    payload: AssignRoadmapRequest,
    actor: UserContext = Depends(get_current_user),
    x_company_id: str | None = Header(default=None, alias="X-Company-Id"),
):
    try:
        return CONTAINER.b2b_service.assign_roadmap(
            actor,
            _company_id_or_default(x_company_id),
            payload.learnerId,
            payload.roleTemplateId,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/exercises/{exercise_id}", response_model=ExerciseResponse)
def get_exercise(
    exercise_id: str,
    actor: UserContext = Depends(get_current_user),
    x_company_id: str | None = Header(default=None, alias="X-Company-Id"),
):
    try:
        return CONTAINER.b2b_service.get_exercise(actor, _company_id_or_default(x_company_id), exercise_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/exercises")
def list_exercises(actor: UserContext = Depends(get_current_user)):
    try:
        return CONTAINER.b2b_service.list_exercises(actor)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/exercises/{exercise_id}/run", response_model=ExerciseRunResponse)
def run_exercise(
    exercise_id: str,
    payload: ExerciseRunRequest,
    actor: UserContext = Depends(get_current_user),
    x_company_id: str | None = Header(default=None, alias="X-Company-Id"),
):
    try:
        return CONTAINER.b2b_service.run_exercise(
            actor,
            _company_id_or_default(x_company_id),
            exercise_id,
            payload.code,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/exercises/{exercise_id}/submit", response_model=SubmissionResponse)
def submit_exercise(
    exercise_id: str,
    payload: ExerciseSubmitRequest,
    actor: UserContext = Depends(get_current_user),
    x_company_id: str | None = Header(default=None, alias="X-Company-Id"),
):
    try:
        return CONTAINER.b2b_service.submit_exercise(
            actor,
            _company_id_or_default(x_company_id),
            exercise_id,
            payload.code,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/submissions", response_model=SubmissionsResponse)
def list_submissions(
    actor: UserContext = Depends(get_current_user),
    x_company_id: str | None = Header(default=None, alias="X-Company-Id"),
):
    try:
        return CONTAINER.b2b_service.list_submissions(actor, _company_id_or_default(x_company_id))
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/submissions/{submission_id}", response_model=SubmissionResponse)
def get_submission(
    submission_id: str,
    actor: UserContext = Depends(get_current_user),
    x_company_id: str | None = Header(default=None, alias="X-Company-Id"),
):
    try:
        return CONTAINER.b2b_service.get_submission(
            actor,
            _company_id_or_default(x_company_id),
            submission_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/submissions/{submission_id}/ai-review", response_model=ReviewResponse)
def run_ai_review(
    submission_id: str,
    actor: UserContext = Depends(get_current_user),
    x_company_id: str | None = Header(default=None, alias="X-Company-Id"),
):
    try:
        return CONTAINER.b2b_service.run_ai_review(
            actor,
            _company_id_or_default(x_company_id),
            submission_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/submissions/{submission_id}/mentor-review", response_model=ReviewResponse)
def submit_mentor_review(
    submission_id: str,
    payload: MentorReviewRequest,
    actor: UserContext = Depends(get_current_user),
    x_company_id: str | None = Header(default=None, alias="X-Company-Id"),
):
    try:
        return CONTAINER.b2b_service.submit_mentor_review(
            actor,
            _company_id_or_default(x_company_id),
            submission_id,
            payload.status,
            payload.comments,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/evidence", response_model=EvidenceItemsResponse)
def list_evidence(
    actor: UserContext = Depends(get_current_user),
    x_company_id: str | None = Header(default=None, alias="X-Company-Id"),
):
    try:
        return CONTAINER.b2b_service.list_evidence(actor, _company_id_or_default(x_company_id))
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/requirements", response_model=RequirementResponse)
def create_requirement(
    payload: RequirementCreateRequest,
    actor: UserContext = Depends(get_current_user),
    x_company_id: str | None = Header(default=None, alias="X-Company-Id"),
):
    try:
        return CONTAINER.b2b_service.create_requirement(
            actor,
            _company_id_or_default(x_company_id),
            payload.title,
            payload.description,
            payload.requiredSkills,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/requirements", response_model=RequirementsResponse)
def list_requirements(
    actor: UserContext = Depends(get_current_user),
    x_company_id: str | None = Header(default=None, alias="X-Company-Id"),
):
    try:
        return CONTAINER.b2b_service.list_requirements(actor, _company_id_or_default(x_company_id))
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/requirements/{requirement_id}/assess", response_model=FitAssessmentResponse)
def assess_requirement(
    requirement_id: str,
    actor: UserContext = Depends(get_current_user),
    x_company_id: str | None = Header(default=None, alias="X-Company-Id"),
):
    try:
        return CONTAINER.b2b_service.assess_requirement(
            actor,
            _company_id_or_default(x_company_id),
            requirement_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/fit-assessments", response_model=FitAssessmentListResponse)
def list_fit_assessments(actor: UserContext = Depends(get_current_user)):
    try:
        return CONTAINER.b2b_service.list_fit_assessments(actor)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/reports/sales-summary", response_model=ReportResponse)
def create_sales_summary(
    payload: SalesSummaryCreateRequest,
    actor: UserContext = Depends(get_current_user),
    x_company_id: str | None = Header(default=None, alias="X-Company-Id"),
):
    try:
        return CONTAINER.b2b_service.create_sales_summary_report(
            actor,
            _company_id_or_default(x_company_id),
            payload.requirementId,
            payload.learnerId,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/reports/{report_id}", response_model=ReportResponse)
def get_report(
    report_id: str,
    actor: UserContext = Depends(get_current_user),
    x_company_id: str | None = Header(default=None, alias="X-Company-Id"),
):
    try:
        return CONTAINER.b2b_service.get_report(actor, _company_id_or_default(x_company_id), report_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/reports/{report_id}/export", response_model=ReportExportJobResponse)
def export_report(
    report_id: str,
    payload: ReportExportRequest,
    actor: UserContext = Depends(get_current_user),
):
    try:
        return CONTAINER.b2b_service.create_report_export_job(
            actor=actor,
            report_id=report_id,
            report_format=payload.reportFormat,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
