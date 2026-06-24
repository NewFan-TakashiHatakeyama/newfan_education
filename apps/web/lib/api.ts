import type {
  AdminAuditLogsQuery,
  AssignRoadmapPayload,
  AssignRoadmapResult,
  AuditLogEventsSummary,
  B2BCompany,
  AuthSession,
  CompanyPatchPayload,
  CompanyBulkStatusPatchPayload,
  CompanyBulkStatusPatchResponse,
  CompaniesSummary,
  ConsentRecord,
  ModerationCase,
  ModerationBulkClosePayload,
  ModerationBulkCloseResponse,
  ModerationCasesSummary,
  ModerationCaseStatus,
  CurriculumImpactSummary,
  CurriculumVersion,
  DashboardSummary,
  EvidenceItemsSummary,
  Exercise,
  ExerciseRunResult,
  FitAssessment,
  FitAssessmentsSummary,
  Invite,
  InviteCsvResult,
  Goal,
  LearnersSummary,
  LearnerSummary,
  Requirement,
  RequirementsSummary,
  ReviewResult,
  NotificationDeliverySettingsSummary,
  NotificationsSummary,
  Role,
  UserAccount,
  UserAccountsSummary,
  Roadmap,
  SalesSummaryReport,
  Submission,
  SubmissionsSummary,
  RoleTemplatesSummary,
  TeamsSummary,
  Team,
  ReportExportJob,
  SkillsGapSummary
} from "@newfan/contracts";
import { getAuthHeaders, handleUnauthorizedSession, isDemoAuthenticated, getDemoAuthSession } from "@/lib/auth";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type JsonValue = Record<string, unknown>;

function mapApiErrorMessage(status: number): string {
  if (status === 400 || status === 422) {
    return "入力内容を確認してください。";
  }
  if (status === 401) {
    return "サインインの有効期限が切れました。もう一度サインインしてください。";
  }
  if (status === 403) {
    return "この操作を行う権限がありません。";
  }
  if (status === 404) {
    return "対象の情報が見つかりませんでした。";
  }
  if (status >= 500) {
    return "現在アクセスが集中しています。時間をおいて再度お試しください。";
  }
  return "通信に失敗しました。時間をおいて再度お試しください。";
}

const PUBLIC_API_PATH_PREFIXES = ["/api/v1/auth/sign-in", "/api/v1/auth/sign-up"] as const;

function isPublicApiPath(path: string): boolean {
  return PUBLIC_API_PATH_PREFIXES.some((prefix) => path.startsWith(prefix));
}

async function request<T>(
  path: string,
  init: RequestInit = {},
  idempotencyKey?: string
): Promise<T> {
  if (!isPublicApiPath(path) && !isDemoAuthenticated(getDemoAuthSession())) {
    throw new Error(mapApiErrorMessage(401));
  }

  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  if (idempotencyKey) {
    headers.set("Idempotency-Key", idempotencyKey);
  }
  const authHeaders = getAuthHeaders();
  for (const [key, value] of Object.entries(authHeaders)) {
    headers.set(key, value);
  }

  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
    credentials: "include",
    cache: "no-store"
  });

  if (!res.ok) {
    if (res.status === 401 && authHeaders.Authorization && !isPublicApiPath(path)) {
      handleUnauthorizedSession();
    }
    throw new Error(mapApiErrorMessage(res.status));
  }
  return (await res.json()) as T;
}

export function createConsent(payload: {
  consentType: "career_profile" | "talent_search";
  granted: boolean;
}) {
  return request<ConsentRecord>("/api/v1/consents", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getMyConsents() {
  return request<ConsentRecord[]>("/api/v1/consents/me");
}

export function createGoal(payload: {
  title: string;
  targetRole: string;
  availableHoursPerWeek: number;
}) {
  return request<Goal>("/api/v1/goals", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function generateRoadmap(payload: {
  goalId: string;
  preferredDifficulty: number;
}) {
  return request<Roadmap>("/api/v1/roadmaps/generate", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getRoadmap(roadmapId: string) {
  return request<Roadmap>(`/api/v1/roadmaps/${roadmapId}`);
}

export function listCurriculumVersions() {
  return request<CurriculumVersion[]>("/api/v1/curriculum");
}

export function publishCurriculum(payload: JsonValue) {
  return request<CurriculumVersion>("/api/v1/admin/curriculum/publish", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function postProgressEvent(payload: JsonValue) {
  return request<{ accepted: boolean }>("/api/v1/progress/events", {
    method: "POST",
    body: JSON.stringify(payload)
  }, `evt-${Date.now()}`);
}

export function getDashboard() {
  return request<DashboardSummary>("/api/v1/dashboard");
}

export function getSkillsGap() {
  return request<SkillsGapSummary>("/api/v1/skills/gap");
}

export function getCurriculumImpact(curriculumVersionId: string) {
  return request<CurriculumImpactSummary>(`/api/v1/admin/curriculum/${curriculumVersionId}/impact`);
}

export function getNotifications(params?: { tab?: "all" | "learning" | "career" | "dm" | "admin"; unread?: boolean }) {
  const search = new URLSearchParams();
  if (params?.tab) {
    search.set("tab", params.tab);
  }
  if (params?.unread) {
    search.set("unread", "true");
  }
  const query = search.toString();
  return request<NotificationsSummary>(`/api/v1/notifications${query ? `?${query}` : ""}`);
}

export function markNotificationRead(notificationId: string) {
  return request<{ id: string; readAt: string | null }>(`/api/v1/notifications/${notificationId}/read`, {
    method: "POST",
    body: JSON.stringify({})
  });
}

export function markAllNotificationsRead() {
  return request<{ updatedCount: number }>("/api/v1/notifications/read-all", {
    method: "POST",
    body: JSON.stringify({})
  });
}

export function getNotificationDeliverySettings() {
  return request<NotificationDeliverySettingsSummary>("/api/v1/notifications/settings");
}

export function patchNotificationDeliverySetting(
  category: "learning" | "career" | "dm" | "admin",
  payload: { emailEnabled: boolean; inAppEnabled: boolean; pushEnabled: boolean }
) {
  return request<{
    category: "learning" | "career" | "dm" | "admin";
    emailEnabled: boolean;
    inAppEnabled: boolean;
    pushEnabled: boolean;
    updatedAt: string | null;
  }>(`/api/v1/notifications/settings/${category}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function getCurrentCompany() {
  return request<B2BCompany>("/api/v1/companies/current");
}

export function getLearners() {
  return request<LearnersSummary>("/api/v1/learners");
}

export function getLearnerDetail(learnerId: string) {
  return request<LearnerSummary>(`/api/v1/learners/${learnerId}`);
}

export function getRoleTemplates() {
  return request<RoleTemplatesSummary>("/api/v1/role-templates");
}

export function assignRoadmap(payload: AssignRoadmapPayload) {
  return request<AssignRoadmapResult>("/api/v1/roadmaps/assign", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getExercise(exerciseId: string) {
  return request<Exercise>(`/api/v1/exercises/${exerciseId}`);
}

export function runExercise(exerciseId: string, payload: { code: string }) {
  return request<ExerciseRunResult>(`/api/v1/exercises/${exerciseId}/run`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function submitExercise(exerciseId: string, payload: { code: string }) {
  return request<Submission>(`/api/v1/exercises/${exerciseId}/submit`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getSubmissions() {
  return request<SubmissionsSummary>("/api/v1/submissions");
}

export function getSubmission(submissionId: string) {
  return request<Submission>(`/api/v1/submissions/${submissionId}`);
}

export function requestAiReview(submissionId: string) {
  return request<ReviewResult>(`/api/v1/submissions/${submissionId}/ai-review`, {
    method: "POST",
    body: JSON.stringify({})
  });
}

export function submitMentorReview(
  submissionId: string,
  payload: { status: "approved" | "needs_resubmit"; comments: string }
) {
  return request<ReviewResult>(`/api/v1/submissions/${submissionId}/mentor-review`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getEvidenceItems() {
  return request<EvidenceItemsSummary>("/api/v1/evidence");
}

export function createRequirement(payload: {
  title: string;
  description: string;
  requiredSkills: string[];
}) {
  return request<Requirement>("/api/v1/requirements", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getRequirements() {
  return request<RequirementsSummary>("/api/v1/requirements");
}

export function assessRequirement(requirementId: string) {
  return request<FitAssessment>(`/api/v1/requirements/${requirementId}/assess`, {
    method: "POST",
    body: JSON.stringify({})
  });
}

export function createSalesSummaryReport(payload: {
  requirementId: string;
  learnerId: string;
}) {
  return request<SalesSummaryReport>("/api/v1/reports/sales-summary", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getSalesSummaryReport(reportId: string) {
  return request<SalesSummaryReport>(`/api/v1/reports/${reportId}`);
}

export function signInDemoUser(payload: { email: string; password: string }) {
  return request<AuthSession>("/api/v1/auth/sign-in", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function signUpDemoUser(payload: {
  userId: string;
  email: string;
  displayName: string;
  role: Role;
  password: string;
  tenantId?: string;
}) {
  return request<AuthSession>("/api/v1/auth/sign-up", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getCurrentSession() {
  return request<AuthSession>("/api/v1/auth/me");
}

export function signOutSession() {
  return request<{ signedOut: boolean }>("/api/v1/auth/sign-out", {
    method: "POST",
    body: JSON.stringify({})
  });
}

export function getCurrentDemoAuthSession() {
  return getDemoAuthSession();
}

export function getTeams() {
  return request<TeamsSummary>("/api/v1/company/teams");
}

export function createTeam(payload: { name: string; description?: string | null }) {
  return request<Team>("/api/v1/company/teams", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function inviteUser(payload: { email: string; role: Role; teamId?: string | null }) {
  return request<Invite>("/api/v1/company/invites", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function inviteUsersByCsv(payload: { csvContent: string; defaultRole: Role }) {
  return request<InviteCsvResult>("/api/v1/company/invites/csv-import", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function listFitAssessments() {
  return request<FitAssessmentsSummary>("/api/v1/fit-assessments");
}

export function exportReport(reportId: string, reportFormat: "csv" | "pdf") {
  return request<ReportExportJob>(`/api/v1/reports/${reportId}/export`, {
    method: "POST",
    body: JSON.stringify({ reportFormat })
  });
}

export function getCompanySettings() {
  return request<{
    tenantId: string;
    branding: { companyName: string; theme: string };
    notifications: { curriculumUpdate: boolean; reportExport: boolean };
    security: { sessionTtlMinutes: number };
  }>("/api/v1/company/settings");
}

export function getAdminTaskTemplates() {
  return request<{ items: Array<{ id: string; title: string; category: string; defaultDifficulty: number }> }>(
    "/api/v1/admin/task-templates"
  );
}

export function getAdminUsers(params?: { role?: Role; state?: "active" | "invited" | "suspended"; q?: string }) {
  const search = new URLSearchParams();
  if (params?.role) {
    search.set("role", params.role);
  }
  if (params?.state) {
    search.set("state", params.state);
  }
  if (params?.q?.trim()) {
    search.set("q", params.q.trim());
  }
  const query = search.toString();
  return request<UserAccountsSummary>(`/api/v1/admin/users${query ? `?${query}` : ""}`);
}

export function patchAdminUser(userId: string, payload: {
  displayName?: string;
  role?: Role;
  state?: "active" | "invited" | "suspended";
}) {
  return request<UserAccount>(`/api/v1/admin/users/${userId}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function getAdminAuditLogs(params?: AdminAuditLogsQuery) {
  const search = new URLSearchParams();
  search.set("limit", String(params?.limit ?? 100));
  if (params?.eventType?.trim()) {
    search.set("eventType", params.eventType.trim());
  }
  if (params?.actorUserId?.trim()) {
    search.set("actorUserId", params.actorUserId.trim());
  }
  if (params?.resourceType?.trim()) {
    search.set("resourceType", params.resourceType.trim());
  }
  if (params?.resourceId?.trim()) {
    search.set("resourceId", params.resourceId.trim());
  }
  if (params?.occurredFrom) {
    search.set("occurredFrom", params.occurredFrom);
  }
  if (params?.occurredTo) {
    search.set("occurredTo", params.occurredTo);
  }
  return request<AuditLogEventsSummary>(`/api/v1/admin/audit-logs?${search.toString()}`);
}

export function getAdminCompanies() {
  return request<CompaniesSummary>("/api/v1/admin/companies");
}

export function patchAdminCompany(companyId: string, payload: CompanyPatchPayload) {
  return request<{
    id: string;
    status: "active" | "stopped";
    contactPersonName: string;
    contactPersonPhone: string;
  }>(`/api/v1/admin/companies/${companyId}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function patchAdminCompaniesBulkStatus(payload: CompanyBulkStatusPatchPayload) {
  return request<CompanyBulkStatusPatchResponse>("/api/v1/admin/companies/status/bulk", {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function getAdminModerationCases(params?: { pendingOnly?: boolean; overdueOnly?: boolean }) {
  const search = new URLSearchParams();
  if (params?.pendingOnly) {
    search.set("pendingOnly", "true");
  }
  if (params?.overdueOnly) {
    search.set("overdueOnly", "true");
  }
  const query = search.toString();
  return request<ModerationCasesSummary>(`/api/v1/admin/moderation${query ? `?${query}` : ""}`);
}

export function patchAdminModerationCase(
  caseId: string,
  payload: { status: ModerationCaseStatus; assignedAdmin?: string | null }
) {
  return request<ModerationCase>(`/api/v1/admin/moderation/${caseId}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function patchAdminModerationBulkClose(payload: ModerationBulkClosePayload) {
  return request<ModerationBulkCloseResponse>("/api/v1/admin/moderation/close/bulk", {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}
