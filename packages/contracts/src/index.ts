export type Role = "learner" | "recruiter" | "admin" | "content_editor" | "mentor";
export type UserState = "active" | "invited" | "suspended";
export type ProfileVisibility = "public" | "limited" | "private";

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

export type OpportunityType = "employment" | "freelance";
export type OpportunityApplicationState =
  | "none"
  | "applied"
  | "screening"
  | "interview"
  | "offer"
  | "proposed"
  | "proposal_review"
  | "negotiation"
  | "contracted";

export interface OpportunityApplication {
  userId: string;
  opportunityId: string;
  state: OpportunityApplicationState;
}

export interface OpportunityApplicationsSummary {
  userId: string;
  applications: Record<string, OpportunityApplicationState>;
}

export interface Opportunity {
  id: string;
  type: OpportunityType;
  title: string;
  provider: string;
  contractType: string;
  compensation: string;
  skillMatchScore: number;
  caution: string;
  summary: string;
  requiredSkills: string[];
  paymentTerms: string;
  isRecommended: boolean;
  isSaved: boolean;
}

export interface OpportunitiesSummary {
  items: Opportunity[];
}

export interface ApplicationListItem {
  opportunityId: string;
  opportunityType: OpportunityType;
  state: OpportunityApplicationState;
  title: string;
  provider: string;
  updatedAt: string;
}

export interface ApplicationsSummary {
  userId: string;
  items: ApplicationListItem[];
}

export interface ApplicationsQuery {
  state?: OpportunityApplicationState;
  opportunityType?: OpportunityType;
  updatedFrom?: string;
  updatedTo?: string;
}

export interface Company {
  id: string;
  name: string;
  industry: string;
  status: "active" | "stopped";
  openOpportunityCount: number;
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
  targetType: "message" | "portfolio" | "profile";
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

export interface PortfolioArtifact {
  id: string;
  userId: string;
  title: string;
  summary: string;
  skillTags: string[];
  relatedSkills: string[];
  evidenceLinks: string[];
  visibility: "private" | "limited" | "public";
  evaluation: string;
  evaluationHistory: {
    evaluatedAt: string;
    evaluator: string;
    score: string;
    comment: string;
  }[];
  submittedAt: string;
}

export interface PortfolioArtifactsSummary {
  userId: string;
  items: PortfolioArtifact[];
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

export type MessageChannel = "dm" | "applications" | "teams";

export interface MessageThread {
  id: string;
  channel: MessageChannel;
  counterpartName: string;
  relatedOpportunityLabel: string | null;
  unreadCount: number;
  canSend: boolean;
  restrictionReason: string | null;
  contextSummary: string;
  updatedAt: string;
}

export interface MessageItem {
  id: string;
  threadId: string;
  senderUserId: string;
  body: string;
  attachments: string[];
  createdAt: string;
}

export interface MessageThreadsSummary {
  userId: string;
  threads: MessageThread[];
}

export interface MessageThreadDetail {
  thread: MessageThread;
  messages: MessageItem[];
}

export interface MessageTemplate {
  id: string;
  key: string;
  label: string;
  body: string;
  targetRoles: Role[];
  channels: MessageChannel[];
}

export interface MessageTemplatesSummary {
  role: Role;
  items: MessageTemplate[];
}

export interface MessageTemplateAuditLogItem {
  id: string;
  templateId: string;
  action: "create" | "update" | "delete";
  actorUserId: string;
  actorRole: Role;
  templateKey: string;
  templateLabel: string;
  occurredAt: string;
}

export interface MessageTemplateAuditLogsSummary {
  items: MessageTemplateAuditLogItem[];
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

export interface PublicProfileSetting {
  userId: string;
  visibility: ProfileVisibility;
  showGoal: boolean;
  showSkillEvidence: boolean;
  showPortfolio: boolean;
  allowRecruiterContact: boolean;
  updatedAt: string;
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
