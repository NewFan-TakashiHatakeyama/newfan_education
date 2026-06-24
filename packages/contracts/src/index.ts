export type Role = "learner" | "recruiter" | "admin" | "content_editor" | "mentor";
export type UserState = "active" | "invited" | "suspended";

export interface ConsentRecord {
  id: string;
  userId: string;
  consentType: "career_profile" | "talent_search";
  granted: boolean;
  grantedAt: string;
}

export interface Goal {
  id: string;
  userId: string;
  title: string;
  targetRole: string;
  availableHoursPerWeek: number;
  createdAt: string;
}

export interface RoadmapItem {
  id: string;
  title: string;
  difficulty: number;
  estimatedMinutes: number;
  curriculumVersionId: string;
  prerequisiteSkillTags: string[];
}

export interface Roadmap {
  id: string;
  goalId: string;
  userId: string;
  generatedAt: string;
  items: RoadmapItem[];
}

export interface CurriculumVersion {
  id: string;
  curriculumSlug: string;
  version: string;
  title: string;
  mdxPath: string;
  published: boolean;
  skillTags?: string[];
  difficulty?: number;
  estimatedMinutes?: number;
}

export interface ProgressEvent {
  id: string;
  userId: string;
  roadmapId: string;
  roadmapItemId: string;
  eventType: "lesson_started" | "lesson_completed";
  occurredAt: string;
}

export type CourseLevel = "beginner" | "intermediate" | "advanced";
export type CourseLessonKind = "reading" | "code";
export type CourseSort = "popular" | "newest" | "rating";

export interface CourseLesson {
  lessonSlug: string;
  title: string;
  kind: CourseLessonKind;
  estimatedMinutes: number;
  skillTags: string[];
  contentRef: string | null;
  exerciseId: string | null;
  isPreview: boolean;
}

export interface CourseSection {
  title: string;
  lessons: CourseLesson[];
  lessonCount: number;
  estimatedMinutes: number;
}

export interface CourseSummary {
  id: string;
  slug: string;
  title: string;
  subtitle: string;
  category: string;
  level: CourseLevel;
  instructor: string;
  summary: string;
  tags: string[];
  rating: number;
  ratingCount: number;
  enrolledCount: number;
  isBestseller: boolean;
  isTopRated: boolean;
  totalLessons: number;
  totalExercises: number;
  estimatedMinutes: number;
  updatedAt: string;
}

export interface CourseDetail extends CourseSummary {
  description: string;
  outcomes: string[];
  targetAudience: string[];
  prerequisites: string[];
  sections: CourseSection[];
}

export interface CoursesSummary {
  items: CourseSummary[];
}

export interface CourseCategory {
  category: string;
  courseCount: number;
}

export interface CourseCategoriesSummary {
  items: CourseCategory[];
}

export interface CourseTrendingSummary {
  items: string[];
}

export interface CoursesQuery {
  q?: string;
  category?: string;
  level?: CourseLevel;
  sort?: CourseSort;
}

export interface DashboardSummary {
  userId: string;
  completedItems: number;
  totalItems: number;
  completionRate: number;
  recentEvents: ProgressEvent[];
}

export interface SkillGapItem {
  id: string;
  name: string;
  currentLevel: number;
  targetLevel: number;
  evidenceCount: number;
  evidenceLink: string;
  isCareerVisible: boolean;
  gapScore: number;
}

export interface SkillsGapSummary {
  userId: string;
  targetRole: string;
  attainmentRate: number;
  lastUpdatedAt: string;
  items: SkillGapItem[];
}

export interface Company {
  id: string;
  name: string;
  industry: string;
  status: "active" | "stopped";
  contactEmail: string;
  contactPersonName: string;
  contactPersonPhone: string;
  updatedAt: string;
}

export interface CompaniesSummary {
  items: Company[];
}

export interface CompanyPatchPayload {
  status?: "active" | "stopped";
  contactPersonName?: string;
  contactPersonPhone?: string;
}

export interface CompanyBulkStatusPatchPayload {
  companyIds: string[];
  status: "active" | "stopped";
}

export interface CompanyBulkStatusPatchResponse {
  updatedCompanyIds: string[];
  skippedCompanyIds: string[];
  status: "active" | "stopped";
}

export type ModerationCaseStatus = "accepted" | "investigating" | "acted" | "closed";

export interface ModerationCase {
  id: string;
  targetType: "evidence" | "submission" | "profile";
  targetId: string;
  reason: string;
  status: ModerationCaseStatus;
  reportedBy: string;
  assignedAdmin: string | null;
  dueAt: string;
  isOverdue: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface ModerationCasesSummary {
  items: ModerationCase[];
}

export interface ModerationBulkClosePayload {
  caseIds: string[];
  assignedAdmin?: string | null;
}

export interface ModerationBulkCloseResponse {
  closedCaseIds: string[];
  skippedCaseIds: string[];
}

export interface CurriculumImpactSummary {
  curriculumVersionId: string;
  affectedRoadmapCount: number;
  affectedRoadmapIds: string[];
  affectedUserCount: number;
  affectedUserIds: string[];
  notificationTargetCount: number;
  notificationUserIds: string[];
}

export type NotificationCategory = "learning" | "career" | "dm" | "admin";

export interface NotificationItem {
  id: string;
  category: NotificationCategory;
  title: string;
  body: string;
  targetUrl: string;
  isImportant: boolean;
  readAt: string | null;
  createdAt: string;
}

export interface NotificationsSummary {
  userId: string;
  unreadCount: number;
  items: NotificationItem[];
}

export interface NotificationDeliverySetting {
  category: NotificationCategory;
  emailEnabled: boolean;
  inAppEnabled: boolean;
  pushEnabled: boolean;
  updatedAt: string | null;
}

export interface NotificationDeliverySettingsSummary {
  userId: string;
  items: NotificationDeliverySetting[];
}

export interface AuthSession {
  accessToken: string;
  tokenType: "bearer";
  expiresIn: number;
  userId: string;
  displayName: string;
  role: Role;
  state: UserState;
  tenantId: string;
}

export interface Team {
  id: string;
  name: string;
  description: string | null;
}

export interface TeamsSummary {
  items: Team[];
}

export interface Invite {
  id: string;
  email: string;
  role: Role;
  teamId: string | null;
  status: string;
  token: string;
}

export interface InviteCsvResult {
  created: Invite[];
  skipped: string[];
}

export interface FitAssessmentListItem {
  id: string;
  requirementId: string;
  fitScore: number;
  matchedSkills: string[];
  gapSkills: string[];
  recommendedLearnerId: string;
  createdAt: string;
}

export interface FitAssessmentsSummary {
  items: FitAssessmentListItem[];
}

export interface ReportExportJob {
  jobId: string;
  status: string;
  resultUrl: string;
  reportId: string;
}

export interface UserAccount {
  userId: string;
  displayName: string;
  role: Role;
  state: UserState;
  createdAt: string;
  updatedAt: string;
}

export interface UserAccountsSummary {
  items: UserAccount[];
}

export interface AuditLogEvent {
  id: string;
  eventType: string;
  resourceType: string;
  resourceId: string;
  action: string;
  actorUserId: string;
  actorRole: Role;
  summary: string;
  metadata: Record<string, string>;
  occurredAt: string;
}

export interface AuditLogEventsSummary {
  items: AuditLogEvent[];
}

export interface AdminAuditLogsQuery {
  limit?: number;
  eventType?: string;
  actorUserId?: string;
  resourceType?: string;
  resourceId?: string;
  occurredFrom?: string;
  occurredTo?: string;
}

export interface B2BCompany {
  id: string;
  name: string;
  plan: string;
  status: string;
  activeLearnerCount: number;
}

export interface RoleTemplate {
  id: string;
  code: string;
  name: string;
  description: string;
  targetSkills: string[];
}

export interface RoleTemplatesSummary {
  items: RoleTemplate[];
}

export interface LearnerSummary {
  id: string;
  name: string;
  teamName: string;
  targetRole: string;
  roadmapCompletionRate: number;
  readiness: string;
  pendingSubmissionCount?: number;
  strongSkills?: string[];
  gapSkills?: string[];
}

export interface LearnersSummary {
  items: LearnerSummary[];
}

export interface AssignRoadmapPayload {
  learnerId: string;
  roleTemplateId: string;
}

export interface AssignRoadmapResult {
  roadmapId: string;
  status: string;
}

export interface Exercise {
  id: string;
  kind: "notebook" | "sql" | "rag" | "ocr";
  title: string;
  prompt: string;
  starterCode: string;
  metadata?: Record<string, unknown>;
}

export interface ExerciseRunResult {
  status: string;
  stdout: string;
  stderr: string;
  engine: "pyodide" | "docker_sandbox";
  pipeline: "notebook" | "sql" | "rag" | "ocr";
  details: Record<string, unknown>;
}

export interface Submission {
  id: string;
  exerciseId: string;
  learnerId: string;
  status: string;
  code: string;
  executionStatus?: string | null;
  executionStdout?: string | null;
  executionStderr?: string | null;
  executionEngine?: string | null;
  executionPipeline?: string | null;
  executionDetails?: Record<string, unknown> | null;
  createdAt: string;
}

export interface SubmissionsSummary {
  items: Submission[];
}

export interface ReviewResult {
  submissionId: string;
  reviewerType: "ai" | "mentor";
  status: string;
  score: number;
  comments: string;
}

export type EvidenceStrength =
  | "weak"
  | "standard"
  | "strong"
  | "improved"
  | "approved"
  | "matched";

export type EvidenceReviewType = "ai" | "mentor" | "ai_and_mentor";

export type EvidenceStatus =
  | "completed"
  | "submitted"
  | "passed"
  | "resubmit"
  | "approved";

export interface EvidenceItem {
  id: string;
  learnerId: string;
  title: string;
  summary: string;
  skillTags: string[];
  strength?: EvidenceStrength | null;
  reviewType?: EvidenceReviewType | null;
  status?: EvidenceStatus | null;
  useCase?: string | null;
  rubricSummary?: string | null;
  exerciseId?: string | null;
  submissionId?: string | null;
  score?: number | null;
  submittedAt?: string | null;
  updatedAt?: string | null;
  relatedRequirementIds?: string[] | null;
}

export interface EvidenceItemsSummary {
  items: EvidenceItem[];
}

export interface Requirement {
  id: string;
  title: string;
  description: string;
  requiredSkills: string[];
}

export interface RequirementsSummary {
  items: Requirement[];
}

export interface FitAssessment {
  requirementId: string;
  fitScore: number;
  matchedSkills: string[];
  gapSkills: string[];
  recommendedLearnerId: string;
}

export interface SalesSummaryReport {
  id: string;
  title: string;
  summary: string;
}
