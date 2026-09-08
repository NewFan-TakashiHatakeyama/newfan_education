"""事業PJ台帳（Venture Ledger）のエンドポイント.

工程マスタ（7工程・6ゲート・132タスク・106スキル・13台帳）は読み取り専用の標準定義で、
案件ごとの台帳はテナントでスコープする。マスタは
`docs/AIシステム自社事業PJ工程管理_v1_1_敵対的レビュー反映版.xlsx` が原本。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from application.venture_services import (
    VentureAccessError,
    VentureNotFoundError,
    VentureValidationError,
)
from domain.models import UserContext
from presentation.dependencies import CONTAINER, get_current_user
from presentation.venture_schemas import (
    VentureApplicabilityBulkRequest,
    VentureApplicabilityBulkResponse,
    VentureCreateRequest,
    VentureGateResponse,
    VentureGateUpdateRequest,
    VentureGatesResponse,
    VentureLedgerEntryResponse,
    VentureLedgerEntryUpsertRequest,
    VentureLedgerResponse,
    VentureMasterResponse,
    VentureMasterSkillsResponse,
    VentureStandardsResponse,
    VentureMasterTasksResponse,
    VentureMemberCreateRequest,
    VentureMemberResponse,
    VentureMembersResponse,
    VentureRemovedResponse,
    VentureResponse,
    VentureSkillAssessmentUpsertRequest,
    VentureSkillAssessmentUpsertResponse,
    VentureSkillGapResponse,
    VentureSummaryResponse,
    VentureTaskResponse,
    VentureTaskUpdateRequest,
    VentureTasksResponse,
    VentureUpdateRequest,
    VenturesResponse,
)

router = APIRouter(prefix="/api/v1", tags=["ventures"])

VENTURE_ERRORS = (VentureAccessError, VentureNotFoundError, VentureValidationError)


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, VentureAccessError):
        return HTTPException(status_code=403, detail=str(exc))
    if isinstance(exc, VentureNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    return HTTPException(status_code=400, detail=str(exc))


# ── マスタ ──────────────────────────────────────────
@router.get("/ventures/master", response_model=VentureMasterResponse)
def get_venture_master(actor: UserContext = Depends(get_current_user)):
    try:
        return CONTAINER.venture_service.get_master(actor)
    except VENTURE_ERRORS as exc:
        raise _http_error(exc) from exc


@router.get("/ventures/master/tasks", response_model=VentureMasterTasksResponse)
def get_venture_master_tasks(
    phaseId: str | None = None,
    actor: UserContext = Depends(get_current_user),
):
    try:
        return CONTAINER.venture_service.get_master_tasks(actor, phaseId)
    except VENTURE_ERRORS as exc:
        raise _http_error(exc) from exc


@router.get("/ventures/master/standards", response_model=VentureStandardsResponse)
def get_venture_master_standards(actor: UserContext = Depends(get_current_user)):
    """工程の標準。案件を作らなくても読める参照情報。"""
    try:
        return CONTAINER.venture_service.get_master_standards(actor)
    except VENTURE_ERRORS as exc:
        raise _http_error(exc) from exc


@router.get("/ventures/master/skills", response_model=VentureMasterSkillsResponse)
def get_venture_master_skills(actor: UserContext = Depends(get_current_user)):
    try:
        return CONTAINER.venture_service.get_master_skills(actor)
    except VENTURE_ERRORS as exc:
        raise _http_error(exc) from exc


# ── 案件 ────────────────────────────────────────────
@router.get("/ventures", response_model=VenturesResponse)
def list_ventures(actor: UserContext = Depends(get_current_user)):
    try:
        return CONTAINER.venture_service.list_ventures(actor)
    except VENTURE_ERRORS as exc:
        raise _http_error(exc) from exc


@router.post("/ventures", response_model=VentureResponse)
def create_venture(
    payload: VentureCreateRequest,
    actor: UserContext = Depends(get_current_user),
):
    try:
        return CONTAINER.venture_service.create_venture(actor, payload.model_dump(exclude_none=True))
    except VENTURE_ERRORS as exc:
        raise _http_error(exc) from exc


@router.get("/ventures/{venture_id}", response_model=VentureResponse)
def get_venture(venture_id: str, actor: UserContext = Depends(get_current_user)):
    try:
        return CONTAINER.venture_service.get_venture(actor, venture_id)
    except VENTURE_ERRORS as exc:
        raise _http_error(exc) from exc


@router.patch("/ventures/{venture_id}", response_model=VentureResponse)
def update_venture(
    venture_id: str,
    payload: VentureUpdateRequest,
    actor: UserContext = Depends(get_current_user),
):
    try:
        return CONTAINER.venture_service.update_venture(
            actor, venture_id, payload.model_dump(exclude_none=True)
        )
    except VENTURE_ERRORS as exc:
        raise _http_error(exc) from exc


@router.delete("/ventures/{venture_id}", response_model=VentureRemovedResponse)
def delete_venture(venture_id: str, actor: UserContext = Depends(get_current_user)):
    try:
        return CONTAINER.venture_service.delete_venture(actor, venture_id)
    except VENTURE_ERRORS as exc:
        raise _http_error(exc) from exc


@router.get("/ventures/{venture_id}/summary", response_model=VentureSummaryResponse)
def get_venture_summary(venture_id: str, actor: UserContext = Depends(get_current_user)):
    try:
        return CONTAINER.venture_service.summary(actor, venture_id)
    except VENTURE_ERRORS as exc:
        raise _http_error(exc) from exc


# ── 工程タスク台帳 ──────────────────────────────────
@router.get("/ventures/{venture_id}/tasks", response_model=VentureTasksResponse)
def list_venture_tasks(
    venture_id: str,
    phaseId: str | None = None,
    applicability: str | None = None,
    status: str | None = None,
    assigneeUserId: str | None = None,
    actor: UserContext = Depends(get_current_user),
):
    try:
        return CONTAINER.venture_service.list_tasks(
            actor,
            venture_id,
            phase_id=phaseId,
            applicability=applicability,
            status=status,
            assignee_user_id=assigneeUserId,
        )
    except VENTURE_ERRORS as exc:
        raise _http_error(exc) from exc


@router.patch("/ventures/{venture_id}/tasks/{task_row_id}", response_model=VentureTaskResponse)
def update_venture_task(
    venture_id: str,
    task_row_id: str,
    payload: VentureTaskUpdateRequest,
    actor: UserContext = Depends(get_current_user),
):
    try:
        return CONTAINER.venture_service.update_task(
            actor, venture_id, task_row_id, payload.model_dump(exclude_unset=True)
        )
    except VENTURE_ERRORS as exc:
        raise _http_error(exc) from exc


@router.post(
    "/ventures/{venture_id}/tasks/applicability",
    response_model=VentureApplicabilityBulkResponse,
)
def bulk_decide_venture_applicability(
    venture_id: str,
    payload: VentureApplicabilityBulkRequest,
    actor: UserContext = Depends(get_current_user),
):
    try:
        return CONTAINER.venture_service.bulk_decide_applicability(actor, venture_id, payload.model_dump())
    except VENTURE_ERRORS as exc:
        raise _http_error(exc) from exc


# ── ゲート ──────────────────────────────────────────
@router.get("/ventures/{venture_id}/gates", response_model=VentureGatesResponse)
def list_venture_gates(venture_id: str, actor: UserContext = Depends(get_current_user)):
    try:
        return CONTAINER.venture_service.list_gates(actor, venture_id)
    except VENTURE_ERRORS as exc:
        raise _http_error(exc) from exc


@router.patch("/ventures/{venture_id}/gates/{gate_row_id}", response_model=VentureGateResponse)
def update_venture_gate(
    venture_id: str,
    gate_row_id: str,
    payload: VentureGateUpdateRequest,
    actor: UserContext = Depends(get_current_user),
):
    try:
        return CONTAINER.venture_service.update_gate(
            actor, venture_id, gate_row_id, payload.model_dump(exclude_unset=True)
        )
    except VENTURE_ERRORS as exc:
        raise _http_error(exc) from exc


# ── 要員 ────────────────────────────────────────────
@router.get("/ventures/{venture_id}/members", response_model=VentureMembersResponse)
def list_venture_members(venture_id: str, actor: UserContext = Depends(get_current_user)):
    try:
        return CONTAINER.venture_service.list_members(actor, venture_id)
    except VENTURE_ERRORS as exc:
        raise _http_error(exc) from exc


@router.post("/ventures/{venture_id}/members", response_model=VentureMemberResponse)
def add_venture_member(
    venture_id: str,
    payload: VentureMemberCreateRequest,
    actor: UserContext = Depends(get_current_user),
):
    try:
        return CONTAINER.venture_service.add_member(actor, venture_id, payload.model_dump())
    except VENTURE_ERRORS as exc:
        raise _http_error(exc) from exc


@router.delete("/ventures/{venture_id}/members/{member_id}", response_model=VentureRemovedResponse)
def remove_venture_member(
    venture_id: str,
    member_id: str,
    actor: UserContext = Depends(get_current_user),
):
    try:
        return CONTAINER.venture_service.remove_member(actor, venture_id, member_id)
    except VENTURE_ERRORS as exc:
        raise _http_error(exc) from exc


# ── 汎用台帳 ────────────────────────────────────────
@router.get("/ventures/{venture_id}/ledgers/{ledger_key}", response_model=VentureLedgerResponse)
def list_venture_ledger(
    venture_id: str,
    ledger_key: str,
    actor: UserContext = Depends(get_current_user),
):
    try:
        return CONTAINER.venture_service.list_ledger(actor, venture_id, ledger_key)
    except VENTURE_ERRORS as exc:
        raise _http_error(exc) from exc


@router.post(
    "/ventures/{venture_id}/ledgers/{ledger_key}/entries",
    response_model=VentureLedgerEntryResponse,
)
def upsert_venture_ledger_entry(
    venture_id: str,
    ledger_key: str,
    payload: VentureLedgerEntryUpsertRequest,
    actor: UserContext = Depends(get_current_user),
):
    try:
        return CONTAINER.venture_service.upsert_ledger_entry(
            actor, venture_id, ledger_key, payload.model_dump(exclude_none=True)
        )
    except VENTURE_ERRORS as exc:
        raise _http_error(exc) from exc


@router.delete(
    "/ventures/{venture_id}/ledgers/{ledger_key}/entries/{entry_id}",
    response_model=VentureRemovedResponse,
)
def delete_venture_ledger_entry(
    venture_id: str,
    ledger_key: str,
    entry_id: str,
    actor: UserContext = Depends(get_current_user),
):
    try:
        return CONTAINER.venture_service.delete_ledger_entry(actor, venture_id, ledger_key, entry_id)
    except VENTURE_ERRORS as exc:
        raise _http_error(exc) from exc


# ── スキル ──────────────────────────────────────────
@router.get("/ventures/{venture_id}/skill-gap", response_model=VentureSkillGapResponse)
def get_venture_skill_gap(venture_id: str, actor: UserContext = Depends(get_current_user)):
    try:
        return CONTAINER.venture_service.skill_gap(actor, venture_id)
    except VENTURE_ERRORS as exc:
        raise _http_error(exc) from exc


@router.post(
    "/ventures/{venture_id}/skill-assessments",
    response_model=VentureSkillAssessmentUpsertResponse,
)
def upsert_venture_skill_assessment(
    venture_id: str,
    payload: VentureSkillAssessmentUpsertRequest,
    actor: UserContext = Depends(get_current_user),
):
    try:
        return CONTAINER.venture_service.upsert_skill_assessment(actor, venture_id, payload.model_dump())
    except VENTURE_ERRORS as exc:
        raise _http_error(exc) from exc
