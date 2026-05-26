from __future__ import annotations

from pydantic import BaseModel, Field


class ConsentCreateRequest(BaseModel):
    consentType: str
    granted: bool


class ConsentResponse(BaseModel):
    id: str
    userId: str
    consentType: str
    granted: bool
    grantedAt: str


class GoalCreateRequest(BaseModel):
    title: str = Field(min_length=1)
    targetRole: str = Field(min_length=1)
    availableHoursPerWeek: int = Field(ge=1, le=80)


class GoalResponse(BaseModel):
    id: str
    userId: str
    title: str
    targetRole: str
    availableHoursPerWeek: int
    createdAt: str


class RoadmapGenerateRequest(BaseModel):
    goalId: str
    preferredDifficulty: int = Field(ge=1, le=5)


class RoadmapItemResponse(BaseModel):
    id: str
    title: str
    difficulty: int
    estimatedMinutes: int
    curriculumVersionId: str
    prerequisiteSkillTags: list[str]


class RoadmapResponse(BaseModel):
    id: str
    userId: str
    goalId: str
    generatedAt: str
    items: list[RoadmapItemResponse]


class CurriculumPublishRequest(BaseModel):
    curriculumSlug: str
    version: str
    title: str
    mdxPath: str
    skillTags: list[str]
    difficulty: int = Field(ge=1, le=5)
    estimatedMinutes: int = Field(ge=5)


class CurriculumVersionResponse(BaseModel):
    id: str
    curriculumSlug: str
    version: str
    title: str
    mdxPath: str
    published: bool
    skillTags: list[str]
    difficulty: int
    estimatedMinutes: int


class ProgressEventRequest(BaseModel):
    roadmapId: str
    roadmapItemId: str
    eventType: str


class ProgressEventResponse(BaseModel):
    accepted: bool


class DashboardResponse(BaseModel):
    userId: str
    completedItems: int
    totalItems: int
    completionRate: float
    recentEvents: list[dict]


class SkillGapItemResponse(BaseModel):
    id: str
    name: str
    currentLevel: int
    targetLevel: int
    evidenceCount: int
    evidenceLink: str
    isCareerVisible: bool
    gapScore: int


class SkillsGapResponse(BaseModel):
    userId: str
    targetRole: str
    attainmentRate: int
    lastUpdatedAt: str
    items: list[SkillGapItemResponse]


class OpportunityApplyRequest(BaseModel):
    opportunityType: str = Field(pattern="^(employment|freelance)$")


class OpportunityApplicationStateResponse(BaseModel):
    userId: str
    opportunityId: str
    state: str


class OpportunityApplicationProgressPatchRequest(BaseModel):
    state: str = Field(
        pattern="^(applied|screening|interview|offer|proposed|proposal_review|negotiation|contracted)$"
    )


class OpportunityApplicationsResponse(BaseModel):
    userId: str
    applications: dict[str, str]


class OpportunityResponse(BaseModel):
    id: str
    type: str
    title: str
    provider: str
    contractType: str
    compensation: str
    skillMatchScore: int
    caution: str
    summary: str
    requiredSkills: list[str]
    paymentTerms: str
    isRecommended: bool
    isSaved: bool


class OpportunitiesResponse(BaseModel):
    items: list[OpportunityResponse]


class ApplicationListItemResponse(BaseModel):
    opportunityId: str
    opportunityType: str
    state: str
    title: str
    provider: str
    updatedAt: str


class ApplicationsResponse(BaseModel):
    userId: str
    items: list[ApplicationListItemResponse]


class CompanyResponse(BaseModel):
    id: str
    name: str
    industry: str
    status: str
    openOpportunityCount: int
    contactEmail: str
    contactPersonName: str
    contactPersonPhone: str
    updatedAt: str


class CompaniesResponse(BaseModel):
    items: list[CompanyResponse]


class CompanyPatchRequest(BaseModel):
    status: str | None = Field(default=None, pattern="^(active|stopped)$")
    contactPersonName: str | None = Field(default=None, min_length=1, max_length=120)
    contactPersonPhone: str | None = Field(default=None, min_length=1, max_length=40)


class CompanyBulkStatusPatchRequest(BaseModel):
    companyIds: list[str] = Field(min_length=1)
    status: str = Field(pattern="^(active|stopped)$")


class CompanyBulkStatusPatchResponse(BaseModel):
    updatedCompanyIds: list[str]
    skippedCompanyIds: list[str]
    status: str


class ModerationCaseResponse(BaseModel):
    id: str
    targetType: str
    targetId: str
    reason: str
    status: str
    reportedBy: str
    assignedAdmin: str | None
    dueAt: str
    isOverdue: bool
    createdAt: str
    updatedAt: str


class ModerationCasesResponse(BaseModel):
    items: list[ModerationCaseResponse]


class ModerationCasePatchRequest(BaseModel):
    status: str = Field(pattern="^(accepted|investigating|acted|closed)$")
    assignedAdmin: str | None = None


class ModerationBulkCloseRequest(BaseModel):
    caseIds: list[str] = Field(min_length=1)
    assignedAdmin: str | None = None


class ModerationBulkCloseResponse(BaseModel):
    closedCaseIds: list[str]
    skippedCaseIds: list[str]


class PortfolioArtifactResponse(BaseModel):
    id: str
    userId: str
    title: str
    summary: str
    skillTags: list[str]
    relatedSkills: list[str]
    evidenceLinks: list[str]
    visibility: str
    evaluation: str
    evaluationHistory: list[dict[str, str]]
    submittedAt: str


class PortfolioArtifactsResponse(BaseModel):
    userId: str
    items: list[PortfolioArtifactResponse]


class CurriculumImpactResponse(BaseModel):
    curriculumVersionId: str
    affectedRoadmapCount: int
    affectedRoadmapIds: list[str]
    affectedUserCount: int
    affectedUserIds: list[str]
    notificationTargetCount: int
    notificationUserIds: list[str]


class NotificationItemResponse(BaseModel):
    id: str
    category: str
    title: str
    body: str
    targetUrl: str
    isImportant: bool
    readAt: str | None
    createdAt: str


class NotificationsResponse(BaseModel):
    userId: str
    unreadCount: int
    items: list[NotificationItemResponse]


class NotificationReadResponse(BaseModel):
    id: str
    readAt: str | None


class NotificationReadAllResponse(BaseModel):
    updatedCount: int


class NotificationDeliverySettingResponse(BaseModel):
    category: str
    emailEnabled: bool
    inAppEnabled: bool
    pushEnabled: bool
    updatedAt: str | None


class NotificationDeliverySettingsResponse(BaseModel):
    userId: str
    items: list[NotificationDeliverySettingResponse]


class NotificationDeliverySettingPatchRequest(BaseModel):
    emailEnabled: bool
    inAppEnabled: bool
    pushEnabled: bool


class MessageThreadResponse(BaseModel):
    id: str
    channel: str
    counterpartName: str
    relatedOpportunityLabel: str | None
    unreadCount: int
    canSend: bool
    restrictionReason: str | None
    contextSummary: str
    updatedAt: str


class MessageResponse(BaseModel):
    id: str
    threadId: str
    senderUserId: str
    body: str
    attachments: list[str]
    createdAt: str


class MessageThreadsResponse(BaseModel):
    userId: str
    threads: list[MessageThreadResponse]


class MessageThreadDetailResponse(BaseModel):
    thread: MessageThreadResponse
    messages: list[MessageResponse]


class SendMessageRequest(BaseModel):
    body: str = Field(min_length=1, max_length=2000)
    attachments: list[str] = Field(default_factory=list)


class MessageTemplateResponse(BaseModel):
    id: str
    key: str
    label: str
    body: str
    targetRoles: list[str]
    channels: list[str]


class MessageTemplatesResponse(BaseModel):
    role: str
    items: list[MessageTemplateResponse]


class MessageTemplateCreateRequest(BaseModel):
    key: str = Field(min_length=1, max_length=80)
    label: str = Field(min_length=1, max_length=120)
    body: str = Field(min_length=1, max_length=3000)
    targetRoles: list[str] = Field(min_length=1)
    channels: list[str] = Field(min_length=1)


class MessageTemplatePatchRequest(BaseModel):
    key: str | None = Field(default=None, min_length=1, max_length=80)
    label: str | None = Field(default=None, min_length=1, max_length=120)
    body: str | None = Field(default=None, min_length=1, max_length=3000)
    targetRoles: list[str] | None = None
    channels: list[str] | None = None


class MessageTemplateDeleteResponse(BaseModel):
    deleted: bool
    templateId: str


class MessageTemplateAuditLogResponse(BaseModel):
    id: str
    templateId: str
    action: str
    actorUserId: str
    actorRole: str
    templateKey: str
    templateLabel: str
    occurredAt: str


class MessageTemplateAuditLogsResponse(BaseModel):
    items: list[MessageTemplateAuditLogResponse]


class AuthSignInRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=255)


class AuthSignUpRequest(BaseModel):
    userId: str = Field(min_length=1, max_length=64)
    email: str = Field(min_length=3, max_length=255)
    displayName: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=255)
    role: str = Field(pattern="^(learner|recruiter|admin|content_editor|mentor)$")
    tenantId: str = Field(default="company-demo", min_length=3, max_length=64)


class AuthSessionResponse(BaseModel):
    accessToken: str
    tokenType: str = "bearer"
    expiresIn: int
    userId: str
    displayName: str
    role: str
    state: str
    tenantId: str


class TeamCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1000)


class TeamResponse(BaseModel):
    id: str
    name: str
    description: str | None


class TeamsResponse(BaseModel):
    items: list[TeamResponse]


class InviteRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    role: str = Field(pattern="^(learner|recruiter|admin|content_editor|mentor)$")
    teamId: str | None = None


class InviteCsvRequest(BaseModel):
    csvContent: str = Field(min_length=1)
    defaultRole: str = Field(pattern="^(learner|recruiter|admin|content_editor|mentor)$")


class InviteResponse(BaseModel):
    id: str
    email: str
    role: str
    teamId: str | None
    status: str
    token: str


class InviteCsvResponse(BaseModel):
    created: list[InviteResponse]
    skipped: list[str]


class FitAssessmentListItemResponse(BaseModel):
    id: str
    requirementId: str
    fitScore: int
    matchedSkills: list[str]
    gapSkills: list[str]
    recommendedLearnerId: str
    createdAt: str


class FitAssessmentListResponse(BaseModel):
    items: list[FitAssessmentListItemResponse]


class ReportExportRequest(BaseModel):
    reportFormat: str = Field(pattern="^(csv|pdf)$")


class ReportExportJobResponse(BaseModel):
    jobId: str
    status: str
    resultUrl: str
    reportId: str


class PublicProfileSettingResponse(BaseModel):
    userId: str
    visibility: str
    showGoal: bool
    showSkillEvidence: bool
    showPortfolio: bool
    allowRecruiterContact: bool
    updatedAt: str


class PublicProfileSettingPatchRequest(BaseModel):
    visibility: str = Field(pattern="^(public|limited|private)$")
    showGoal: bool
    showSkillEvidence: bool
    showPortfolio: bool
    allowRecruiterContact: bool


class UserAccountResponse(BaseModel):
    userId: str
    displayName: str
    role: str
    state: str
    createdAt: str
    updatedAt: str


class UserAccountsResponse(BaseModel):
    items: list[UserAccountResponse]


class UserAccountPatchRequest(BaseModel):
    displayName: str | None = Field(default=None, min_length=1, max_length=120)
    role: str | None = Field(default=None, pattern="^(learner|recruiter|admin|content_editor|mentor)$")
    state: str | None = Field(default=None, pattern="^(active|invited|suspended)$")


class AuditLogEventResponse(BaseModel):
    id: str
    eventType: str
    resourceType: str
    resourceId: str
    action: str
    actorUserId: str
    actorRole: str
    summary: str
    metadata: dict[str, str]
    occurredAt: str


class AuditLogEventsResponse(BaseModel):
    items: list[AuditLogEventResponse]


class B2BCompanyResponse(BaseModel):
    id: str
    name: str
    plan: str
    status: str
    activeLearnerCount: int


class RoleTemplateResponse(BaseModel):
    id: str
    code: str
    name: str
    description: str
    targetSkills: list[str]


class RoleTemplatesResponse(BaseModel):
    items: list[RoleTemplateResponse]


class LearnerSummaryResponse(BaseModel):
    id: str
    name: str
    teamName: str
    targetRole: str
    roadmapCompletionRate: int
    readiness: str
    pendingSubmissionCount: int | None = None
    strongSkills: list[str] | None = None
    gapSkills: list[str] | None = None


class LearnersResponse(BaseModel):
    items: list[LearnerSummaryResponse]


class AssignRoadmapRequest(BaseModel):
    learnerId: str
    roleTemplateId: str


class AssignRoadmapResponse(BaseModel):
    roadmapId: str
    status: str


class ExerciseResponse(BaseModel):
    id: str
    kind: str
    title: str
    prompt: str
    starterCode: str
    metadata: dict[str, object] = Field(default_factory=dict)


class ExerciseRunRequest(BaseModel):
    code: str


class ExerciseRunResponse(BaseModel):
    status: str
    stdout: str
    stderr: str = ""
    engine: str = "pyodide"
    pipeline: str = "notebook"
    details: dict[str, object] = Field(default_factory=dict)


class ExerciseSubmitRequest(BaseModel):
    code: str


class SubmissionResponse(BaseModel):
    id: str
    exerciseId: str
    learnerId: str
    status: str
    code: str
    executionStatus: str | None = None
    executionStdout: str | None = None
    executionStderr: str | None = None
    executionEngine: str | None = None
    executionPipeline: str | None = None
    executionDetails: dict[str, object] | None = None
    createdAt: str


class SubmissionsResponse(BaseModel):
    items: list[SubmissionResponse]


class ReviewResponse(BaseModel):
    submissionId: str
    reviewerType: str
    status: str
    score: int
    comments: str


class MentorReviewRequest(BaseModel):
    status: str = Field(pattern="^(approved|needs_resubmit)$")
    comments: str


class EvidenceItemResponse(BaseModel):
    id: str
    learnerId: str
    title: str
    summary: str
    skillTags: list[str]
    strength: str | None = None
    reviewType: str | None = None
    status: str | None = None
    useCase: str | None = None
    rubricSummary: str | None = None
    exerciseId: str | None = None
    submissionId: str | None = None
    score: int | None = None
    submittedAt: str | None = None
    updatedAt: str | None = None
    relatedRequirementIds: list[str] | None = None


class EvidenceItemsResponse(BaseModel):
    items: list[EvidenceItemResponse]


class RequirementCreateRequest(BaseModel):
    title: str
    description: str
    requiredSkills: list[str]


class RequirementResponse(BaseModel):
    id: str
    title: str
    description: str
    requiredSkills: list[str]


class RequirementsResponse(BaseModel):
    items: list[RequirementResponse]


class FitAssessmentResponse(BaseModel):
    requirementId: str
    fitScore: int
    matchedSkills: list[str]
    gapSkills: list[str]
    recommendedLearnerId: str


class SalesSummaryCreateRequest(BaseModel):
    requirementId: str
    learnerId: str


class ReportResponse(BaseModel):
    id: str
    title: str
    summary: str
