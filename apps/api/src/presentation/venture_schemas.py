"""事業PJ台帳のリクエスト／レスポンススキーマ。

台帳の列は Excel 由来でシートごとに違うため、行の値は `dict[str, str]` で扱う。
列の定義はマスタ（GET /ventures/master）が返す。
"""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

# DBの列長を超える入力は、SQLite では通るが PostgreSQL では 22001 で落ちる。
# 開発環境をすり抜けて本番だけで500になるので、入口で列長に合わせて弾く。
DATE_PATTERN = r"^(\d{4}-\d{2}-\d{2})?$"
# 自由記述（Text列）の上限。列長の制約は無いが、無制限の入力は受け付けない。
TEXT_MAX = 20000


# ── マスタ ──────────────────────────────────────────
class VenturePhaseResponse(BaseModel):
    phaseId: str
    name: str
    purpose: str
    precondition: str
    gateId: str
    approverRoleId: str
    requiredEvidence: str
    decision: str
    taskCount: int


class VentureGateDefinitionResponse(BaseModel):
    gateId: str
    subject: str
    standardTaskId: str
    approverRoleId: str
    requiredEvidence: str
    allowedDecisions: list[str]


class VentureRiskTierResponse(BaseModel):
    tierId: str
    name: str
    impact: str
    rigor: str
    caution: str


class VentureRoleResponse(BaseModel):
    roleId: str
    name: str
    responsibility: str
    involvement: str
    independenceNote: str


class VentureColumnRuleResponse(BaseModel):
    """原本の入力規則。select は候補、date は YYYY-MM-DD、number は下限。"""

    type: str
    options: list[str] = []
    min: float | None = None
    source: str = ""


class VentureLedgerDefinitionResponse(BaseModel):
    key: str
    name: str
    summary: str
    sourceSheet: str
    idColumn: str
    seeded: bool
    masterColumns: list[str]
    inputColumns: list[str]
    notes: list[str]
    columnRules: dict[str, VentureColumnRuleResponse] = {}
    # 原本が数式で埋める列。入力列ではないが、点検結果として表示する。
    derivedColumns: list[str] = []
    checkColumns: list[str] = []
    # 原本33 K03 の予約行数。超える記録は正本側で管理する。
    rowLimit: int | None = None
    stateColumn: str = ""
    lockedStates: list[str] = []
    masterRowCount: int


class VentureMasterResponse(BaseModel):
    version: str
    phases: list[VenturePhaseResponse]
    gates: list[VentureGateDefinitionResponse]
    riskTiers: list[VentureRiskTierResponse]
    roles: list[VentureRoleResponse]
    conditionKeys: list[str]
    ledgers: list[VentureLedgerDefinitionResponse]
    taskCount: int
    skillCount: int


# ── 工程の標準（案件を作らずに読める参照情報） ────────────
class VentureTailoringResponse(BaseModel):
    aspect: str
    approach: str
    operation: str
    caution: str


class VentureEffortReferenceResponse(BaseModel):
    phase: str
    sMin: str
    sMax: str
    mMin: str
    mMax: str
    lMin: str
    lMax: str
    unit: str


class VentureEvalTypeResponse(BaseModel):
    evalTypeId: str
    axis: str
    metrics: str
    designNote: str
    applicability: str


class VentureHarnessResponse(BaseModel):
    controlId: str
    target: str
    standard: str
    detail: str
    ownerRoleId: str
    evidence: str
    relatedTaskIds: list[str]


class VentureHarnessTestResponse(BaseModel):
    testId: str
    appliesWhen: str
    theme: str
    specification: str
    ownerRoleId: str
    evidence: str
    relatedTaskIds: list[str]
    note: str


class VentureDevLoopStepResponse(BaseModel):
    step: str
    name: str
    input: str
    aiRole: str
    humanRole: str
    stopCondition: str


class VentureRuntimeSettingResponse(BaseModel):
    name: str
    check: str


class VentureSourceResponse(BaseModel):
    sourceId: str
    published: str
    organization: str
    title: str
    evidenceType: str
    adopted: str
    limitation: str
    appliedTo: str
    url: str
    checkedOn: str


class VentureInvestmentDecisionResponse(BaseModel):
    decision: str
    condition: str
    caution: str


class VentureStandardsResponse(BaseModel):
    version: str
    tailoring: list[VentureTailoringResponse]
    scales: dict[str, list[VentureTailoringResponse]]
    effortReference: list[VentureEffortReferenceResponse]
    evalTypes: list[VentureEvalTypeResponse]
    harness: list[VentureHarnessResponse]
    harnessTests: list[VentureHarnessTestResponse]
    devLoop: list[VentureDevLoopStepResponse]
    runtimeSettings: list[VentureRuntimeSettingResponse]
    investmentDecisions: list[VentureInvestmentDecisionResponse] = []
    sources: list[VentureSourceResponse]


class VentureMasterTaskResponse(BaseModel):
    taskId: str
    phaseId: str
    phaseName: str
    workType: str
    name: str
    description: str
    deliverables: str
    completionCriteria: str
    applicability: str
    gateId: str
    execRoleIds: list[str]
    approverRoleId: str
    dependsOn: list[str]
    skillIds: list[str]
    aiBoundary: str
    sourceIds: list[str] = []
    referenceUrls: list[str] = []


class VentureMasterTasksResponse(BaseModel):
    items: list[VentureMasterTaskResponse]


class VentureMasterSkillResponse(BaseModel):
    skillId: str
    axis: str
    category: str
    name: str
    definition: str
    level1: str
    level2: str
    level3: str
    evidence: str
    sourceIds: list[str] = []
    note: str = ""


class VentureMasterSkillsResponse(BaseModel):
    items: list[VentureMasterSkillResponse]


# ── 案件 ────────────────────────────────────────────
class VentureCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    summary: str = Field(default="", max_length=TEXT_MAX)
    offeringType: str = Field(default="社内事業", max_length=32)
    industry: str = Field(default="", max_length=120)
    serviceCountries: str = Field(default="", max_length=255)
    processingCountries: str = Field(default="", max_length=255)
    scale: str = Field(default="S", max_length=8)
    riskTier: str = Field(default="未判定", max_length=8)
    riskTierRationale: str = Field(default="", max_length=TEXT_MAX)
    currentPhaseId: str = Field(default="B0", max_length=8)
    businessOwnerUserId: str | None = Field(default=None, max_length=64)
    asOfDate: str = Field(default="", pattern=DATE_PATTERN)
    conditions: dict[str, str] | None = None


class VentureUpdateRequest(BaseModel):
    confirmRisk: bool = False
    riskEvidenceUri: str = Field(default="", max_length=TEXT_MAX)
    name: str | None = Field(default=None, max_length=200)
    summary: str | None = Field(default=None, max_length=TEXT_MAX)
    offeringType: str | None = Field(default=None, max_length=32)
    industry: str | None = Field(default=None, max_length=120)
    serviceCountries: str | None = Field(default=None, max_length=255)
    processingCountries: str | None = Field(default=None, max_length=255)
    scale: str | None = Field(default=None, max_length=8)
    riskTier: str | None = Field(default=None, max_length=8)
    riskTierRationale: str | None = Field(default=None, max_length=TEXT_MAX)
    status: str | None = Field(default=None, max_length=16)
    currentPhaseId: str | None = Field(default=None, max_length=8)
    businessOwnerUserId: str | None = Field(default=None, max_length=64)
    asOfDate: str | None = Field(default=None, pattern=DATE_PATTERN)
    conditions: dict[str, str] | None = None


class VentureResponse(BaseModel):
    governance: dict = {}
    capabilities: dict = {}
    id: str
    name: str
    summary: str
    offeringType: str
    industry: str
    serviceCountries: str
    processingCountries: str
    scale: str
    riskTier: str
    riskTierRationale: str
    status: str
    currentPhaseId: str
    businessOwnerUserId: str | None
    conditions: dict[str, str]
    # 原本00の管理基準日。空ならサーバ当日を使う（asOfDateSource が 'today' になる）。
    asOfDate: str = ""
    asOfDateSource: str = ""
    createdBy: str
    createdAt: str | None
    updatedAt: str | None
    taskTotal: int = 0
    taskApplied: int = 0
    taskUndecided: int = 0
    taskCompleted: int = 0


class VenturesResponse(BaseModel):
    items: list[VentureResponse]


# ── 工程タスク ──────────────────────────────────────
class VentureTaskResponse(BaseModel):
    completionValid: bool = False
    completionCheck: str = "未確認"
    id: str
    ventureId: str
    taskId: str
    phaseId: str
    phaseName: str
    workType: str
    name: str
    description: str
    deliverables: str
    completionCriteria: str
    aiBoundary: str
    applicabilityCondition: str
    execRoleIds: list[str]
    approverRoleId: str
    dependsOn: list[str]
    standardDependsOn: list[str] = []
    dependencyChangeReason: str = ""
    dependencyChangeApprovedBy: str | None = None
    dependencyChangeApprovedAt: str | None = None
    dependencyCheck: str = ""
    skillIds: list[str]
    gateId: str
    evidenceId: str
    recommendedSource: str
    minimumEvidence: str
    sourceIds: list[str] = []
    referenceUrls: list[str] = []
    legacyTaskIds: list[str] = []
    applicability: str
    applicabilityReason: str
    applicabilityDecidedBy: str | None
    applicabilityDecidedByName: str
    applicabilityDecidedAt: str | None
    status: str
    assigneeUserId: str | None
    assigneeName: str
    roleId: str
    plannedStart: str
    plannedEnd: str
    actualStart: str
    actualEnd: str
    plannedHours: int | None
    actualHours: int | None
    evidenceUri: str
    completionApprovedBy: str | None
    completionApprovedByName: str
    completionApprovedAt: str | None
    blocker: str
    note: str
    updatedAt: str | None


class VentureTasksResponse(BaseModel):
    items: list[VentureTaskResponse]


class VentureTaskUpdateRequest(BaseModel):
    applicability: str | None = Field(default=None, max_length=16)
    applicabilityReason: str | None = Field(default=None, max_length=TEXT_MAX)
    status: str | None = Field(default=None, max_length=16)
    assigneeUserId: str | None = Field(default=None, max_length=64)
    roleId: str | None = Field(default=None, max_length=8)
    plannedStart: str | None = Field(default=None, pattern=DATE_PATTERN)
    plannedEnd: str | None = Field(default=None, pattern=DATE_PATTERN)
    actualStart: str | None = Field(default=None, pattern=DATE_PATTERN)
    actualEnd: str | None = Field(default=None, pattern=DATE_PATTERN)
    plannedHours: int | None = Field(default=None, ge=0, le=1_000_000)
    actualHours: int | None = Field(default=None, ge=0, le=1_000_000)
    evidenceUri: str | None = Field(default=None, max_length=TEXT_MAX)
    blocker: str | None = Field(default=None, max_length=TEXT_MAX)
    note: str | None = Field(default=None, max_length=TEXT_MAX)
    dependsOn: list[str] | None = Field(default=None, max_length=8)
    dependencyChangeReason: str | None = Field(default=None, max_length=TEXT_MAX)
    approveCompletion: bool | None = None


class VentureApplicabilityBulkRequest(BaseModel):
    taskRowIds: list[str] = Field(max_length=1000)
    applicability: str = Field(max_length=16)
    reason: str = Field(default="", max_length=TEXT_MAX)


class VentureApplicabilityBulkResponse(BaseModel):
    updated: int


# ── ゲート ──────────────────────────────────────────
class VentureGateResponse(BaseModel):
    recordedDecision: str = "未審査"
    effective: bool = False
    validity: str = "判断記録なし"
    gateRunId: str = ""
    id: str
    gateId: str
    subject: str
    standardTaskId: str
    approverRoleId: str
    requiredEvidence: str
    allowedDecisions: list[str]
    decision: str
    scope: str
    evidencePackageUri: str
    conditions: str
    conditionDue: str
    decidedBy: str | None
    decidedByName: str
    recordedByName: str
    decidedAt: str | None
    nextAction: str
    reviewTrigger: str
    appliedTaskCount: int
    completedTaskCount: int
    unapprovedTaskCount: int
    updatedAt: str | None


class VentureGatesResponse(BaseModel):
    items: list[VentureGateResponse]


class VentureGateUpdateRequest(BaseModel):
    decision: str | None = Field(default=None, max_length=32)
    scope: str | None = Field(default=None, max_length=TEXT_MAX)
    evidencePackageUri: str | None = Field(default=None, max_length=TEXT_MAX)
    conditions: str | None = Field(default=None, max_length=TEXT_MAX)
    conditionDue: str | None = Field(default=None, pattern=DATE_PATTERN)
    decidedByName: str | None = Field(default=None, max_length=120)
    nextAction: str | None = Field(default=None, max_length=TEXT_MAX)
    reviewTrigger: str | None = Field(default=None, max_length=TEXT_MAX)


# ── 要員 ────────────────────────────────────────────
class VentureMemberResponse(BaseModel):
    id: str
    userId: str
    userName: str
    roleId: str
    roleName: str
    allocationNote: str
    createdAt: str | None


class VentureMembersResponse(BaseModel):
    items: list[VentureMemberResponse]


class VentureMemberCreateRequest(BaseModel):
    userId: str = Field(max_length=64)
    roleId: str = Field(max_length=8)
    allocationNote: str = Field(default="", max_length=TEXT_MAX)


class VentureRemovedResponse(BaseModel):
    removed: bool


# ── 汎用台帳 ────────────────────────────────────────
class VentureLedgerEntryResponse(BaseModel):
    checks: dict[str, dict[str, str]] = {}
    createdAt: str | None = None
    id: str
    rowKey: str
    isMasterRow: bool
    status: str
    master: dict[str, str]
    values: dict[str, str]
    # 原本の点検列（記録点検・日時点検など）の判定結果。
    derived: dict[str, str] = {}
    updatedBy: str | None
    updatedByName: str
    updatedAt: str | None


class VentureLedgerResponse(BaseModel):
    ledger: VentureLedgerDefinitionResponse | None = None
    items: list[VentureLedgerEntryResponse]


class VentureLedgerEntryUpsertRequest(BaseModel):
    verifyRecord: bool = False
    id: str | None = Field(default=None, max_length=80)
    rowKey: str | None = Field(default=None, max_length=64)
    status: str | None = Field(default=None, max_length=32)
    values: dict[str, str] | None = None

    @field_validator("values")
    @classmethod
    def _limit_values(cls, value: dict[str, str] | None) -> dict[str, str] | None:
        # 台帳の値はJSON列なので列長の制約が効かない。ここで上限を掛ける。
        for column, item in (value or {}).items():
            if len(item) > TEXT_MAX:
                raise ValueError(f"{column} の入力が長すぎます（上限 {TEXT_MAX} 文字）")
        return value


# ── スキル ──────────────────────────────────────────
class VentureSkillAssessmentResponse(BaseModel):
    id: str
    userId: str
    userName: str
    assessedLevel: int
    evidenceUri: str
    developmentPlan: str
    dueDate: str
    assessedAt: str | None


class VentureSkillCourseResponse(BaseModel):
    """そのスキルを埋められる学習コース。対応が無いスキルは空配列になる。"""

    courseSlug: str
    title: str
    coversLevel: int
    note: str


class VentureSkillGapItemResponse(BaseModel):
    assignments: list[dict] = []
    skillId: str
    name: str
    axis: str
    category: str
    definition: str
    requiredLevel: int
    taskIds: list[str]
    coveredLevel: int
    gap: int
    courses: list[VentureSkillCourseResponse] = []
    assessments: list[VentureSkillAssessmentResponse]


class VentureSkillGapResponse(BaseModel):
    items: list[VentureSkillGapItemResponse]
    appliedTaskCount: int
    gapCount: int


class VentureSkillAssessmentUpsertRequest(BaseModel):
    skillId: str = Field(max_length=16)
    userId: str = Field(max_length=64)
    assessedLevel: int = Field(ge=0, le=3)
    evidenceUri: str = Field(default="", max_length=TEXT_MAX)
    developmentPlan: str = Field(default="", max_length=TEXT_MAX)
    dueDate: str = Field(default="", pattern=DATE_PATTERN)


class VentureSkillAssessmentUpsertResponse(BaseModel):
    id: str
    skillId: str
    userId: str
    userName: str
    assessedLevel: int
    evidenceUri: str
    developmentPlan: str
    dueDate: str
    assessedAt: str | None


# ── ダッシュボード ──────────────────────────────────
class VenturePhaseProgressResponse(BaseModel):
    phaseId: str
    name: str
    purpose: str
    gateId: str
    total: int
    applied: int
    undecided: int
    excluded: int
    completed: int
    inProgress: int
    blocked: int


class VentureLedgerProgressResponse(BaseModel):
    key: str
    name: str
    total: int
    filled: int


class VentureSummaryResponse(BaseModel):
    decisions: dict = {}
    venture: VentureResponse
    phases: list[VenturePhaseProgressResponse]
    gates: list[VentureGateResponse]
    skillGapCount: int
    topSkillGaps: list[VentureSkillGapItemResponse]
    ledgers: list[VentureLedgerProgressResponse]
    members: list[VentureMemberResponse]
