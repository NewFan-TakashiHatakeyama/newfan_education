"use client";

import { use, useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";

import type {
  VentureApplicability,
  VentureMaster,
  VentureSource,
  VentureTask,
  VentureTaskStatus
} from "@newfan/contracts";

import {
  decideVentureApplicability,
  fetchVentureMaster,
  fetchVentureMembers,
  fetchVentureStandards,
  fetchVentureTasks,
  updateVentureTask
} from "@/lib/api";

import { Section } from "@/app/components/ui/Section";
import { Drawer } from "@/app/components/ui/Drawer";
import { SkeletonRow } from "@/app/components/ui/Skeleton";
import { EmptyState } from "@/app/components/ui/EmptyState";

import { ApplicabilityPill, TaskStatusPill, VentureNav } from "../../VentureNav";
import { useVentureRole } from "../../useVentureRole";
import styles from "../../ventures.module.css";

const APPLICABILITY: VentureApplicability[] = ["未判定", "適用", "対象外"];
const TASK_STATUS: VentureTaskStatus[] = ["未着手", "進行中", "完了", "保留"];

export default function VentureTasksPage({
  params
}: {
  params: Promise<{ ventureId: string }>;
}) {
  const { ventureId } = use(params);
  const searchParams = useSearchParams();

  const [tasks, setTasks] = useState<VentureTask[] | null>(null);
  const [master, setMaster] = useState<VentureMaster | null>(null);
  const [members, setMembers] = useState<{ userId: string; userName: string }[]>([]);
  // 原本24の調査ソース。タスクの根拠IDを資料名・URLに解決する。
  const [sources, setSources] = useState<Record<string, VentureSource>>({});
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const [phaseId, setPhaseId] = useState(searchParams.get("phaseId") ?? "");
  const [applicability, setApplicability] = useState("");
  const [status, setStatus] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [bulkReason, setBulkReason] = useState("");
  const [detail, setDetail] = useState<VentureTask | null>(null);
  // ドロワーの自由入力は下書きに溜めて明示的に保存する。onBlur だけに頼ると
  // Escape で閉じたときに入力が捨てられる。
  const [draft, setDraft] = useState<Record<string, string>>({});
  const { canManage: canEdit, roleIds, userId } = useVentureRole(ventureId);

  const refresh = useCallback(() => {
    fetchVentureTasks(ventureId, {
      phaseId: phaseId || undefined,
      applicability: applicability || undefined,
      status: status || undefined
    })
      .then((res) => setTasks(res.items))
      .catch((err: unknown) => {
        setTasks([]);
        setError(err instanceof Error ? err.message : "工程タスクを取得できませんでした。");
      });
  }, [ventureId, phaseId, applicability, status]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    fetchVentureMaster()
      .then(setMaster)
      .catch(() => setMaster(null));
    fetchVentureMembers(ventureId)
      .then((res) =>
        setMembers(res.items.map((item) => ({ userId: item.userId, userName: item.userName })))
      )
      .catch(() => setMembers([]));
    fetchVentureStandards()
      .then((res) =>
        setSources(Object.fromEntries(res.sources.map((item) => [item.sourceId, item])))
      )
      .catch(() => setSources({}));
  }, [ventureId]);

  const counts = useMemo(() => {
    const list = tasks ?? [];
    return {
      total: list.length,
      undecided: list.filter((task) => task.applicability === "未判定").length,
      applied: list.filter((task) => task.applicability === "適用").length,
      completed: list.filter((task) => task.status === "完了").length
    };
  }, [tasks]);

  // 選択したままフィルタを変えると、画面に出ていない行に一括判定が当たる。
  const changeFilter = (apply: (value: string) => void) => (value: string) => {
    apply(value);
    setSelected(new Set());
  };

  const toggle = (id: string) => {
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const applyBulk = async (value: VentureApplicability) => {
    if (selected.size === 0) return;
    if (value === "対象外" && !bulkReason.trim()) {
      setError("対象外にする理由（代替証拠）を入力してください。");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await decideVentureApplicability(ventureId, {
        taskRowIds: Array.from(selected),
        applicability: value,
        reason: bulkReason
      });
      setSelected(new Set());
      setBulkReason("");
      refresh();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "適用判定を保存できませんでした。");
    } finally {
      setSaving(false);
    }
  };

  // 担当者が触れる項目はサーバ側の許可キーに合わせる（venture_services.py）。
  const DRAFT_KEYS = [
    "plannedStart",
    "plannedEnd",
    "actualStart",
    "actualEnd",
    "evidenceUri",
    "blocker",
    "note",
    "applicabilityReason"
  ] as const;
  const ASSIGNEE_DRAFT_KEYS = ["actualStart", "actualEnd", "evidenceUri", "blocker", "note"];

  const openDetail = (task: VentureTask) => {
    setDetail(task);
    setDraft({
      plannedStart: task.plannedStart,
      plannedEnd: task.plannedEnd,
      actualStart: task.actualStart,
      actualEnd: task.actualEnd,
      evidenceUri: task.evidenceUri,
      blocker: task.blocker,
      note: task.note,
      applicabilityReason: task.applicabilityReason
    });
  };

  const draftChanges = (task: VentureTask | null) => {
    if (!task) return {};
    const editable = canEdit ? DRAFT_KEYS : ASSIGNEE_DRAFT_KEYS;
    const changed: Record<string, string> = {};
    for (const key of editable) {
      const before = (task as unknown as Record<string, string>)[key] ?? "";
      if ((draft[key] ?? "") !== before) changed[key] = draft[key] ?? "";
    }
    return changed;
  };

  const dirty = Object.keys(draftChanges(detail)).length > 0;

  const saveDraft = async (task: VentureTask | null) => {
    const changed = draftChanges(task);
    if (!task || Object.keys(changed).length === 0) return true;
    return await patchTask(task.id, changed);
  };

  const closeDetail = async () => {
    // 閉じる前に書きかけを保存する。黙って捨てない。
    const current = detail;
    if (await saveDraft(current)) setDetail(null);
  };

  const patchTask = async (taskRowId: string, payload: Parameters<typeof updateVentureTask>[2]) => {
    setSaving(true);
    setError(null);
    try {
      const updated = await updateVentureTask(ventureId, taskRowId, payload);
      setTasks((current) =>
        current ? current.map((task) => (task.id === updated.id ? updated : task)) : current
      );
      setDetail((current) => (current && current.id === updated.id ? updated : current));
      return true;
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "更新できませんでした。");
      return false;
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <VentureNav ventureId={ventureId} />

      <Section
        title="工程タスク台帳"
        meta="適用判定は人が決めます。条件から自動提案された値も、確定するには判定の操作が必要です。"
        theme="company"
      >
        {error ? <p className={styles.error}>{error}</p> : null}

        <div className={styles.toolbar}>
          <label className={styles.field}>
            工程
            <select value={phaseId} onChange={(event) => changeFilter(setPhaseId)(event.target.value)}>
              <option value="">すべて</option>
              {(master?.phases ?? []).map((phase) => (
                <option key={phase.phaseId} value={phase.phaseId}>
                  {phase.phaseId} {phase.name}
                </option>
              ))}
            </select>
          </label>
          <label className={styles.field}>
            適用判定
            <select value={applicability} onChange={(event) => changeFilter(setApplicability)(event.target.value)}>
              <option value="">すべて</option>
              {APPLICABILITY.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
          <label className={styles.field}>
            状態
            <select value={status} onChange={(event) => changeFilter(setStatus)(event.target.value)}>
              <option value="">すべて</option>
              {TASK_STATUS.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
          <span className={styles.count}>
            {counts.total}件 / 適用 {counts.applied} / 判定待ち {counts.undecided} / 完了{" "}
            {counts.completed}
          </span>
        </div>

        {selected.size > 0 && canEdit ? (
          <div className={styles.toolbar}>
            <span className={styles.muted}>{selected.size}件を選択中</span>
            <label className={styles.field} style={{ minWidth: 260 }}>
              対象外にする理由・代替証拠
              <input
                value={bulkReason}
                onChange={(event) => setBulkReason(event.target.value)}
                placeholder="対象外を選ぶ場合は必須（原本17の除外理由）"
              />
            </label>
            {APPLICABILITY.filter((value) => value !== "未判定").map((value) => (
              <button
                key={value}
                type="button"
                className="ghost-button"
                disabled={saving}
                onClick={() => applyBulk(value)}
              >
                {value}にする
              </button>
            ))}
            <button type="button" className={styles.rowButton} onClick={() => setSelected(new Set())}>
              選択を解除
            </button>
          </div>
        ) : null}

        {tasks === null ? (
          <SkeletonRow />
        ) : tasks.length === 0 ? (
          <EmptyState title="該当するタスクがありません" message="絞り込み条件を変えてください。" />
        ) : (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  {canEdit ? <th style={{ width: 34 }} /> : null}
                  <th>ID</th>
                  <th>タスク</th>
                  <th>適用条件</th>
                  <th>適用判定</th>
                  <th>状態</th>
                  <th>担当</th>
                  <th>Gate</th>
                  <th>証拠</th>
                </tr>
              </thead>
              <tbody>
                {tasks.map((task) => (
                  <tr key={task.id}>
                    {canEdit ? (
                      <td>
                        <input
                          type="checkbox"
                          checked={selected.has(task.id)}
                          onChange={() => toggle(task.id)}
                          aria-label={`${task.taskId} を選択`}
                        />
                      </td>
                    ) : null}
                    <td className={styles.taskId}>{task.taskId}</td>
                    <td>
                      <button
                        type="button"
                        className={styles.rowButton}
                        onClick={() => openDetail(task)}
                      >
                        {task.name}
                      </button>
                      <div className={styles.muted}>{task.workType}</div>
                    </td>
                    <td className={styles.muted}>{task.applicabilityCondition}</td>
                    <td>
                      <ApplicabilityPill value={task.applicability} />
                    </td>
                    <td>
                      <TaskStatusPill value={task.status} />
                    </td>
                    <td className={styles.muted}>{task.assigneeName || "—"}</td>
                    <td className={styles.taskId}>{task.gateId}</td>
                    <td>
                      {task.completionValid ? (
                        <span className={`${styles.pill} ${styles.pillDone}`}>完了条件充足</span>
                      ) : task.evidenceUri ? (
                        <span className={`${styles.pill} ${styles.pillProgress}`}>記録あり</span>
                      ) : (
                        <span className={styles.muted}>{task.completionCheck || "未確認"}</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>

      <Drawer
        open={detail !== null}
        title={detail ? `${detail.taskId} ${detail.name}` : ""}
        onClose={closeDetail}
      >
        {detail ? (
          <div>
            <dl className={styles.detailList}>
              <dt>工程</dt>
              <dd>
                {detail.phaseId} {detail.phaseName} / {detail.workType}
              </dd>
              <dt>実施内容</dt>
              <dd>{detail.description}</dd>
              <dt>成果物</dt>
              <dd>{detail.deliverables}</dd>
              <dt>完了条件</dt>
              <dd>{detail.completionCriteria}</dd>
              <dt>正本の置き場</dt>
              <dd>{detail.recommendedSource || "—"}</dd>
              <dt>AIと人の境界</dt>
              <dd>{detail.aiBoundary || "—"}</dd>
              <dt>実施ロール</dt>
              <dd>
                {detail.execRoleIds.join(", ") || "—"} / 承認 {detail.approverRoleId || "—"}
              </dd>
              <dt>依存</dt>
              <dd>{detail.dependsOn.join(", ") || "—"}</dd>
              <dt>必要スキル</dt>
              <dd>{detail.skillIds.join(", ") || "—"}</dd>
              {detail.sourceIds.length > 0 ? (
                <>
                  <dt>根拠</dt>
                  <dd>
                    {detail.sourceIds.map((sourceId) => {
                      const source = sources[sourceId];
                      return (
                        <div key={sourceId}>
                          <span className={styles.taskId}>{sourceId}</span>{" "}
                          {source ? `${source.organization} ${source.title}` : "（出典未解決）"}
                          {source?.url && source.url.startsWith("http") ? (
                            <>
                              {" "}
                              <a href={source.url} target="_blank" rel="noreferrer">
                                原典
                              </a>
                            </>
                          ) : null}
                        </div>
                      );
                    })}
                  </dd>
                </>
              ) : null}
              {detail.referenceUrls.length > 0 ? (
                <>
                  <dt>確認用URL</dt>
                  <dd>
                    {detail.referenceUrls.map((url) => (
                      <div key={url}>
                        <a href={url} target="_blank" rel="noreferrer">
                          {url}
                        </a>
                      </div>
                    ))}
                  </dd>
                </>
              ) : null}
            </dl>

            <div className={styles.formGrid}>
              <label className={styles.field}>
                適用判定
                <select
                  value={detail.applicability}
                  disabled={saving || !canEdit}
                  onChange={(event) =>
                    patchTask(detail.id, {
                      applicability: event.target.value as VentureApplicability,
                      applicabilityReason: draft.applicabilityReason ?? ""
                    })
                  }
                >
                  {APPLICABILITY.map((value) => (
                    <option key={value} value={value}>
                      {value}
                    </option>
                  ))}
                </select>
              </label>
              <label className={styles.field}>
                状態
                <select
                  value={detail.status}
                  // サーバは編集担当に加えて、自分が担当するタスクの状態更新も許可する。
                  disabled={saving || (!canEdit && detail.assigneeUserId !== userId)}
                  onChange={(event) =>
                    patchTask(detail.id, { status: event.target.value as VentureTaskStatus })
                  }
                >
                  {TASK_STATUS.map((value) => (
                    <option key={value} value={value}>
                      {value}
                    </option>
                  ))}
                </select>
              </label>
              <label className={styles.field}>
                担当者
                <select
                  value={detail.assigneeUserId ?? ""}
                  disabled={saving || !canEdit}
                  onChange={(event) =>
                    patchTask(detail.id, { assigneeUserId: event.target.value || null })
                  }
                >
                  <option value="">未割当</option>
                  {members.map((member) => (
                    <option key={member.userId} value={member.userId}>
                      {member.userName}
                    </option>
                  ))}
                </select>
              </label>
              <label className={styles.field}>
                予定開始
                <input
                  type="date"
                  value={draft.plannedStart ?? ""}
                  disabled={saving || !canEdit}
                  onChange={(event) =>
                    setDraft((current) => ({ ...current, plannedStart: event.target.value }))
                  }
                />
              </label>
              <label className={styles.field}>
                予定完了
                <input
                  type="date"
                  value={draft.plannedEnd ?? ""}
                  disabled={saving || !canEdit}
                  onChange={(event) =>
                    setDraft((current) => ({ ...current, plannedEnd: event.target.value }))
                  }
                />
              </label>
              <label className={styles.field}>
                実開始
                <input
                  type="date"
                  value={draft.actualStart ?? ""}
                  disabled={saving}
                  onChange={(event) =>
                    setDraft((current) => ({ ...current, actualStart: event.target.value }))
                  }
                />
              </label>
              <label className={styles.field}>
                実完了
                <input
                  type="date"
                  value={draft.actualEnd ?? ""}
                  disabled={saving}
                  onChange={(event) =>
                    setDraft((current) => ({ ...current, actualEnd: event.target.value }))
                  }
                />
              </label>
            </div>

            <label className={styles.field} style={{ marginTop: 12 }}>
              完了証拠のURI
              <input
                value={draft.evidenceUri ?? ""}
                disabled={saving}
                placeholder={detail.minimumEvidence || "Issue・ドキュメント・評価Runの場所"}
                onChange={(event) =>
                  setDraft((current) => ({ ...current, evidenceUri: event.target.value }))
                }
              />
            </label>
            {detail.minimumEvidence ? (
              <p className={styles.note}>最低限の証拠: {detail.minimumEvidence}</p>
            ) : null}

            <label className={styles.field}>
              阻害要因
              <input
                value={draft.blocker ?? ""}
                disabled={saving}
                onChange={(event) =>
                  setDraft((current) => ({ ...current, blocker: event.target.value }))
                }
              />
            </label>
            <label className={styles.field}>
              メモ
              <textarea
                value={draft.note ?? ""}
                disabled={saving}
                onChange={(event) => setDraft((current) => ({ ...current, note: event.target.value }))}
              />
            </label>

            {canEdit ? (
              <label className={styles.field}>
                対象外にする理由・代替証拠
                <textarea
                  value={draft.applicabilityReason ?? ""}
                  disabled={saving}
                  placeholder="対象外にするには理由が必要です（原本17の除外理由・代替証拠）"
                  onChange={(event) =>
                    setDraft((current) => ({ ...current, applicabilityReason: event.target.value }))
                  }
                />
              </label>
            ) : null}

            <div className={styles.actionRow}>
              <button
                type="button"
                className="primary-button"
                disabled={saving || !dirty}
                onClick={() => saveDraft(detail)}
              >
                {saving ? "保存中…" : dirty ? "入力を保存" : "保存済み"}
              </button>
            </div>

            <div className={styles.actionRow}>
              {detail.completionApprovedAt ? (
                <>
                  <span className={`${styles.pill} ${detail.completionValid ? styles.pillDone : styles.pillProgress}`}>
                    {detail.completionValid ? "完了条件充足" : `承認記録あり・${detail.completionCheck}`} / {detail.completionApprovedByName || detail.completionApprovedBy}
                  </span>
                  {canEdit ? (
                    <button
                      type="button"
                      className="ghost-button"
                      disabled={saving}
                      onClick={() => patchTask(detail.id, { approveCompletion: false })}
                    >
                      承認を取り消す
                    </button>
                  ) : null}
                </>
              ) : (
                <button
                  type="button"
                  className="primary-button"
                  disabled={saving || dirty || !roleIds.includes(detail.approverRoleId) || !detail.evidenceUri || detail.status !== "完了"}
                  onClick={async () => {
                    await patchTask(detail.id, { approveCompletion: true });
                  }}
                  title={
                    !roleIds.includes(detail.approverRoleId)
                      ? `完了承認には ${detail.approverRoleId} の案件割当が必要です`
                      : !detail.evidenceUri
                        ? "先に完了証拠のURIを記録してください"
                        : detail.status !== "完了"
                          ? "先に状態を「完了」にしてください"
                          : undefined
                  }
                >
                  完了を承認する
                </button>
              )}
            </div>
            {detail.applicabilityDecidedAt ? (
              <p className={styles.muted} style={{ marginTop: 10 }}>
                適用判定: {detail.applicabilityDecidedByName || detail.applicabilityDecidedBy} /{" "}
                {new Date(detail.applicabilityDecidedAt).toLocaleString("ja-JP")}
                {detail.applicabilityReason ? ` / ${detail.applicabilityReason}` : ""}
              </p>
            ) : null}
          </div>
        ) : null}
      </Drawer>
    </>
  );
}
