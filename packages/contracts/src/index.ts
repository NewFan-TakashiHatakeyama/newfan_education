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

/* ─────────────────────────────────────────────────────────────
 * 事業PJ台帳（Venture Ledger）
 *
 * 工程マスタは「AIシステム自社事業PJ工程管理」が原本。
 * 7工程（B0〜B6）・6ゲート（G0〜G5）・132タスク・106スキル・13台帳を持つ。
 * ───────────────────────────────────────────────────────────── */

/** 案件がタスクを実施するかどうかの判定。最終判断は人が行う。 */
export type VentureApplicability = "未判定" | "適用" | "対象外";

/** 工程タスクの進捗状態。 */
export type VentureTaskStatus = "未着手" | "進行中" | "完了" | "保留";

/** 案件そのものの状態。 */
export type VentureStatus = "計画中" | "進行中" | "停止" | "終了" | "アーカイブ";

/** 規模区分。テーラリングの基準。 */
export type VentureScale = "S" | "M" | "L";

export interface VenturePhase {
  phaseId: string;
  name: string;
  purpose: string;
  precondition: string;
  gateId: string;
  approverRoleId: string;
  requiredEvidence: string;
  decision: string;
  taskCount: number;
}

export interface VentureGateDefinition {
  gateId: string;
  subject: string;
  standardTaskId: string;
  approverRoleId: string;
  requiredEvidence: string;
  allowedDecisions: string[];
}

export interface VentureRiskTier {
  tierId: string;
  name: string;
  impact: string;
  rigor: string;
  caution: string;
}

export interface VentureRole {
  roleId: string;
  name: string;
  responsibility: string;
  involvement: string;
  independenceNote: string;
}

/** 原本の入力規則。統制語彙・日付・数値の制約を画面とAPIで守る。 */
export interface VentureColumnRule {
  type: "select" | "date" | "datetime" | "number";
  options: string[];
  min?: number | null;
  source?: string;
}

export interface VentureLedgerDefinition {
  key: string;
  name: string;
  summary: string;
  sourceSheet: string;
  idColumn: string;
  /** マスタ由来の点検行を持つ台帳かどうか。false なら案件側で行を起票する。 */
  seeded: boolean;
  masterColumns: string[];
  inputColumns: string[];
  notes: string[];
  /** 入力列 -> 原本の入力規則。規則の無い列は自由記述。 */
  columnRules: Record<string, VentureColumnRule>;
  /** 原本が数式で埋める列。入力できないが点検結果として表示する。 */
  derivedColumns: string[];
  checkColumns: string[];
  /** 原本33 K03 の予約行数。 */
  rowLimit: number | null;
  stateColumn: string;
  lockedStates: string[];
  masterRowCount: number;
}

export interface VentureMaster {
  version: string;
  phases: VenturePhase[];
  gates: VentureGateDefinition[];
  riskTiers: VentureRiskTier[];
  roles: VentureRole[];
  conditionKeys: string[];
  ledgers: VentureLedgerDefinition[];
  taskCount: number;
  skillCount: number;
}

export interface VentureMasterTask {
  taskId: string;
  phaseId: string;
  phaseName: string;
  workType: string;
  name: string;
  description: string;
  deliverables: string;
  completionCriteria: string;
  applicability: string;
  gateId: string;
  execRoleIds: string[];
  approverRoleId: string;
  dependsOn: string[];
  skillIds: string[];
  aiBoundary: string;
  /** 原本の「根拠ID」。24_調査ソースを引く。 */
  sourceIds: string[];
  referenceUrls: string[];
}

export interface VentureMasterTasksSummary {
  items: VentureMasterTask[];
}

export interface VentureMasterSkill {
  skillId: string;
  axis: string;
  category: string;
  name: string;
  definition: string;
  level1: string;
  level2: string;
  level3: string;
  evidence: string;
  sourceIds: string[];
  note: string;
}

export interface VentureMasterSkillsSummary {
  items: VentureMasterSkill[];
}

/** 工程の標準。案件を作らずに読める参照情報（原本 03/04/14/24/32）。 */
export interface VentureTailoringItem {
  aspect: string;
  approach: string;
  operation: string;
  caution: string;
}

export interface VentureEffortReference {
  phase: string;
  sMin: string;
  sMax: string;
  mMin: string;
  mMax: string;
  lMin: string;
  lMax: string;
  unit: string;
}

export interface VentureEvalType {
  evalTypeId: string;
  axis: string;
  metrics: string;
  designNote: string;
  applicability: string;
}

export interface VentureHarnessControl {
  controlId: string;
  target: string;
  standard: string;
  detail: string;
  ownerRoleId: string;
  evidence: string;
  relatedTaskIds: string[];
}

export interface VentureHarnessTest {
  testId: string;
  appliesWhen: string;
  theme: string;
  specification: string;
  ownerRoleId: string;
  evidence: string;
  relatedTaskIds: string[];
  note: string;
}

export interface VentureDevLoopStep {
  step: string;
  name: string;
  input: string;
  aiRole: string;
  humanRole: string;
  stopCondition: string;
}

export interface VentureRuntimeSetting {
  name: string;
  check: string;
}

export interface VentureSource {
  sourceId: string;
  published: string;
  organization: string;
  title: string;
  evidenceType: string;
  adopted: string;
  limitation: string;
  appliedTo: string;
  url: string;
  checkedOn: string;
}

export interface VentureInvestmentDecision {
  decision: string;
  condition: string;
  caution: string;
}

export interface VentureStandards {
  version: string;
  tailoring: VentureTailoringItem[];
  scales: Record<string, VentureTailoringItem[]>;
  effortReference: VentureEffortReference[];
  evalTypes: VentureEvalType[];
  harness: VentureHarnessControl[];
  harnessTests: VentureHarnessTest[];
  devLoop: VentureDevLoopStep[];
  runtimeSettings: VentureRuntimeSetting[];
  investmentDecisions: VentureInvestmentDecision[];
  sources: VentureSource[];
}

export interface Venture {
  governance?: { riskState?: string; riskConfirmed?: boolean; riskFingerprint?: string };
  capabilities?: { canManage: boolean; canEdit: boolean; canAssess: boolean; canVerify: boolean; roleIds: string[] };
  id: string;
  name: string;
  summary: string;
  offeringType: string;
  industry: string;
  serviceCountries: string;
  processingCountries: string;
  scale: VentureScale;
  riskTier: string;
  riskTierRationale: string;
  status: VentureStatus;
  currentPhaseId: string;
  businessOwnerUserId?: string | null;
  conditions: Record<string, VentureApplicability>;
  createdBy: string;
  createdAt?: string | null;
  updatedAt?: string | null;
  taskTotal: number;
  taskApplied: number;
  taskUndecided: number;
  taskCompleted: number;
}

export interface VenturesSummary {
  items: Venture[];
}

export interface VentureCreatePayload {
  name: string;
  summary?: string;
  offeringType?: string;
  industry?: string;
  serviceCountries?: string;
  processingCountries?: string;
  scale?: VentureScale;
  riskTier?: string;
  riskTierRationale?: string;
  currentPhaseId?: string;
  businessOwnerUserId?: string | null;
  conditions?: Record<string, VentureApplicability>;
}

export type VentureUpdatePayload = Partial<VentureCreatePayload> & {
  confirmRisk?: boolean;
  riskEvidenceUri?: string;
  status?: VentureStatus;
};

export interface VentureTask {
  completionValid?: boolean;
  completionCheck?: string;
  id: string;
  ventureId: string;
  taskId: string;
  phaseId: string;
  phaseName: string;
  workType: string;
  name: string;
  description: string;
  deliverables: string;
  completionCriteria: string;
  aiBoundary: string;
  /** マスタ側の適用条件。「全」または「条件:RAG」などが入る。 */
  applicabilityCondition: string;
  execRoleIds: string[];
  approverRoleId: string;
  dependsOn: string[];
  skillIds: string[];
  gateId: string;
  evidenceId: string;
  recommendedSource: string;
  minimumEvidence: string;
  sourceIds: string[];
  referenceUrls: string[];
  legacyTaskIds: string[];
  /** 案件の実効依存。標準依存から変えたら理由と承認が要る（原本17）。 */
  standardDependsOn: string[];
  dependencyChangeReason: string;
  dependencyChangeApprovedBy: string | null;
  dependencyChangeApprovedAt: string | null;
  dependencyCheck: string;
  applicability: VentureApplicability;
  applicabilityReason: string;
  applicabilityDecidedBy?: string | null;
  applicabilityDecidedByName: string;
  applicabilityDecidedAt?: string | null;
  status: VentureTaskStatus;
  assigneeUserId?: string | null;
  assigneeName: string;
  roleId: string;
  plannedStart: string;
  plannedEnd: string;
  actualStart: string;
  actualEnd: string;
  plannedHours?: number | null;
  actualHours?: number | null;
  evidenceUri: string;
  completionApprovedBy?: string | null;
  completionApprovedByName: string;
  completionApprovedAt?: string | null;
  blocker: string;
  note: string;
  updatedAt?: string | null;
}

export interface VentureTasksSummary {
  items: VentureTask[];
}

export interface VentureTaskUpdatePayload {
  applicability?: VentureApplicability;
  applicabilityReason?: string;
  status?: VentureTaskStatus;
  assigneeUserId?: string | null;
  roleId?: string;
  plannedStart?: string;
  plannedEnd?: string;
  actualStart?: string;
  actualEnd?: string;
  plannedHours?: number | null;
  actualHours?: number | null;
  evidenceUri?: string;
  blocker?: string;
  note?: string;
  approveCompletion?: boolean;
}

export interface VentureGate {
  recordedDecision?: string;
  effective?: boolean;
  validity?: string;
  gateRunId?: string;
  id: string;
  gateId: string;
  subject: string;
  standardTaskId: string;
  approverRoleId: string;
  requiredEvidence: string;
  allowedDecisions: string[];
  decision: string;
  scope: string;
  evidencePackageUri: string;
  conditions: string;
  conditionDue: string;
  decidedBy?: string | null;
  /** 原本29の「A実名」。入力された承認者の実名。 */
  decidedByName: string;
  /** 実際に画面で記録した利用者の表示名。承認者とは別。 */
  recordedByName: string;
  decidedAt?: string | null;
  nextAction: string;
  reviewTrigger: string;
  appliedTaskCount: number;
  completedTaskCount: number;
  unapprovedTaskCount: number;
  updatedAt?: string | null;
}

export interface VentureGatesSummary {
  items: VentureGate[];
}

export interface VentureGateUpdatePayload {
  decision?: string;
  scope?: string;
  evidencePackageUri?: string;
  conditions?: string;
  conditionDue?: string;
  decidedByName?: string;
  nextAction?: string;
  reviewTrigger?: string;
}

export interface VentureMember {
  id: string;
  userId: string;
  userName: string;
  roleId: string;
  roleName: string;
  allocationNote: string;
  createdAt?: string | null;
}

export interface VentureMembersSummary {
  items: VentureMember[];
}

export interface VentureLedgerEntry {
  checks?: Record<string, { code: string; severity: string; label: string }>;
  id: string;
  rowKey: string;
  /** マスタ由来の点検行。削除できず、状態と入力で管理する。 */
  isMasterRow: boolean;
  status: string;
  master: Record<string, string>;
  values: Record<string, string>;
  /** 原本の点検列の判定結果（記録点検・日時点検など）。 */
  derived: Record<string, string>;
  updatedBy?: string | null;
  updatedByName: string;
  updatedAt?: string | null;
}

export interface VentureLedgerSummary {
  ledger?: VentureLedgerDefinition | null;
  items: VentureLedgerEntry[];
}

export interface VentureLedgerEntryPayload {
  verifyRecord?: boolean;
  id?: string;
  rowKey?: string;
  status?: string;
  values?: Record<string, string>;
}

export interface VentureSkillAssessment {
  id: string;
  userId: string;
  userName: string;
  assessedLevel: number;
  evidenceUri: string;
  developmentPlan: string;
  dueDate: string;
  assessedAt?: string | null;
}

/** そのスキルを埋められる学習コース。対応が無いスキルは空配列。 */
export interface VentureSkillCourse {
  courseSlug: string;
  title: string;
  coversLevel: number;
  note: string;
}

export interface VentureSkillGapItem {
  assignments?: { taskId: string; roleId: string; requiredLevel: number; coveredLevel: number; gap: number }[];
  skillId: string;
  name: string;
  axis: string;
  category: string;
  definition: string;
  /** 適用タスクが要求する必要Lvの最大値。 */
  requiredLevel: number;
  taskIds: string[];
  /** 工程・ロール別の不足の最大値を必要Lvから差し引いた保守的な到達Lv。 */
  coveredLevel: number;
  gap: number;
  courses: VentureSkillCourse[];
  assessments: VentureSkillAssessment[];
}

export interface VentureSkillGapSummary {
  items: VentureSkillGapItem[];
  appliedTaskCount: number;
  gapCount: number;
}

export interface VentureSkillAssessmentPayload {
  skillId: string;
  userId: string;
  assessedLevel: number;
  evidenceUri?: string;
  developmentPlan?: string;
  dueDate?: string;
}

export interface VenturePhaseProgress {
  phaseId: string;
  name: string;
  purpose: string;
  gateId: string;
  total: number;
  applied: number;
  undecided: number;
  excluded: number;
  completed: number;
  inProgress: number;
  blocked: number;
}

export interface VentureLedgerProgress {
  key: string;
  name: string;
  total: number;
  filled: number;
}

export interface VentureSummary {
  decisions?: { riskState: string; hypotheses: VentureDecisionRow[]; kpis: VentureDecisionRow[]; conditions: VentureDecisionRow[]; cashPlans: VentureDecisionRow[]; runs: VentureDecisionRow[]; nextActions?: { ledgerKey: string; rowId: string; dueDate: string; overdue: boolean; action: string; owner: string }[] };
  venture: Venture;
  phases: VenturePhaseProgress[];
  gates: VentureGate[];
  skillGapCount: number;
  topSkillGaps: VentureSkillGapItem[];
  ledgers: VentureLedgerProgress[];
  members: VentureMember[];
}

export interface VentureDecisionRow {
  id: string;
  values: Record<string, string>;
  checks: Record<string, string>;
}
