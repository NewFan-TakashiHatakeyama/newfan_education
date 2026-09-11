"use client";

import { use, useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";

import type {
  VentureMasterSkill,
  VentureMember,
  VentureSkillGapItem,
  VentureSkillGapSummary
} from "@newfan/contracts";

import {
  fetchVentureAssessmentHistory,
  type AssessmentHistoryRow,
  fetchVentureMasterSkills,
  fetchVentureMembers,
  fetchVentureSkillGap,
  saveVentureSkillAssessment
} from "@/lib/api";

import { LoadFailure } from "@/app/components/ui/LoadFailure";
import { Section } from "@/app/components/ui/Section";
import { Disclosure } from "@/app/components/ui/Disclosure";
import { Feedback } from "@/app/components/ui/Feedback";
import { Drawer, Modal } from "@/app/components/ui/Drawer";
import { SkeletonRow } from "@/app/components/ui/Skeleton";
import { EmptyState } from "@/app/components/ui/EmptyState";

import { VentureNav } from "../../VentureNav";
import { useVentureRole } from "../../useVentureRole";
import styles from "../../ventures.module.css";

export default function VentureSkillsPage({
  params
}: {
  params: Promise<{ ventureId: string }>;
}) {
  const { ventureId } = use(params);
  const [gap, setGap] = useState<VentureSkillGapSummary | null>(null);
  const [members, setMembers] = useState<VentureMember[]>([]);
  const [skills, setSkills] = useState<Record<string, VentureMasterSkill>>({});
  const [loadFailed, setLoadFailed] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [onlyGap, setOnlyGap] = useState(true);
  const [view, setView] = useState<"summary" | "edit" | "history">("summary");
  const [history, setHistory] = useState<AssessmentHistoryRow[] | null>(null);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [cancelOpen, setCancelOpen] = useState(false);
  const [detail, setDetail] = useState<VentureSkillGapItem | null>(null);
  const [assessUserId, setAssessUserId] = useState("");
  const [assessLevel, setAssessLevel] = useState(0);
  const [assessPlan, setAssessPlan] = useState("");
  const [cancelReason, setCancelReason] = useState("");
  const [assessDueDate, setAssessDueDate] = useState("");
  const [assessEvidence, setAssessEvidence] = useState("");
  const { userId: selfUserId, canAssess } = useVentureRole(ventureId);

  const refresh = useCallback(() => {
    fetchVentureSkillGap(ventureId)
      .then(result => { setGap(result); setLoadFailed(false); setError(null); })
      .catch((err: unknown) => {
        setGap(null); setLoadFailed(true);
        setError(err instanceof Error ? err.message : "スキル充足を取得できませんでした。");
      });
  }, [ventureId]);

  useEffect(() => {
    refresh();
    fetchVentureMembers(ventureId)
      .then((res) => setMembers(res.items))
      .catch(() => setMembers([]));
    fetchVentureMasterSkills()
      .then((res) =>
        setSkills(Object.fromEntries(res.items.map((item) => [item.skillId, item])))
      )
      .catch(() => setSkills({}));
  }, [ventureId, refresh]);

  const rows = useMemo(() => {
    const items = gap?.items ?? [];
    return onlyGap ? items.filter((item) => item.gap > 0) : items;
  }, [gap, onlyGap]);

  // 原本28「自己申告だけで配置しない」。自分自身は評価対象に出さない。
  const assessable = useMemo(
    () => members.filter((member, index) => member.userId !== selfUserId && members.findIndex(m => m.userId === member.userId) === index),
    [members, selfUserId]
  );

  /** その人の現在の到達Lv。未評価なら0。チーム最高値を初期値にすると誤って上書きする。 */
  const levelOf = (item: VentureSkillGapItem, userId: string) =>
    item.assessments.find((assessment) => assessment.userId === userId)?.assessedLevel ?? 0;

  const openDetail = (item: VentureSkillGapItem) => {
    const first = assessable[0]?.userId ?? "";
    setCancelReason(""); setView("summary"); setHistory(null); setHistoryError(null); setError(null);
    setDetail(item);
    setAssessUserId(first);
    setAssessLevel(first ? levelOf(item, first) : 0);
    setAssessPlan(item.assessments.find(a => a.userId === first)?.developmentPlan ?? "");
    setAssessDueDate(item.assessments.find(a => a.userId === first)?.dueDate ?? "");
    setAssessEvidence(item.assessments.find(a => a.userId === first)?.evidenceUri ?? "");
  };

  const changeAssessUser = (userId: string) => {
    setAssessUserId(userId); setCancelReason("");
    if (detail) {
      setAssessLevel(levelOf(detail, userId));
      const current = detail.assessments.find(a => a.userId === userId);
      setAssessDueDate(current?.dueDate ?? "");
      setAssessEvidence(current?.evidenceUri ?? "");
      setAssessPlan(current?.developmentPlan ?? "");
    }
  };

  const currentAssessment = detail?.assessments.find(a => a.userId === assessUserId);
  const dirty = canAssess && !!detail && (assessLevel !== (currentAssessment?.assessedLevel ?? 0) || assessPlan !== (currentAssessment?.developmentPlan ?? "") || assessEvidence !== (currentAssessment?.evidenceUri ?? "") || assessDueDate !== (currentAssessment?.dueDate ?? ""));
  const loadHistory = async () => {
    setView("history"); setHistoryError(null);
    try { setHistory((await fetchVentureAssessmentHistory(ventureId)).items); }
    catch (err) { setHistoryError(err instanceof Error ? err.message : "履歴を取得できませんでした。"); }
  };

  return (
    <>
      <VentureNav ventureId={ventureId} />

      <Section
        title="スキル充足"
        meta="必要なレベルと現在の評価を比較します。"
        theme="company"
      >
        {error ? <p className={styles.error}>{error}</p> : null}

        <div className={styles.toolbar}>
          <label className={styles.field} style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
            <input
              type="checkbox"
              checked={onlyGap}
              onChange={(event) => setOnlyGap(event.target.checked)}
            />
            不足のみ
          </label>
          {gap ? (
            <span className={styles.count}>
              適用タスク {gap.appliedTaskCount}件 / 要求スキル {gap.items.length}件 / 不足{" "}
              {gap.gapCount}件
            </span>
          ) : null}
        </div>

        {loadFailed ? <LoadFailure onRetry={refresh} /> : gap === null ? (
          <SkeletonRow />
        ) : rows.length === 0 ? (
          <EmptyState
            title={onlyGap ? "不足しているスキルはありません" : "要求スキルがありません"}
            message={
              onlyGap
                ? "要員の到達Lvが、適用タスクの必要Lvを満たしています。"
                : "適用判定を済ませると、必要なスキルが集計されます。"
            }
          />
        ) : (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>スキル</th>
                  <th>軸 / 分類</th>
                  <th>必要Lv</th>
                  <th>到達Lv</th>
                  <th>不足</th>
                  <th>対象タスク</th>
                  <th>学習</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((item) => (
                  <tr key={item.skillId}>
                    <td>
                      <button
                        type="button"
                        className={styles.rowButton}
                        onClick={() => openDetail(item)}
                      >
                        {item.name}
                      </button>
                      <div className={styles.taskId}>{item.skillId}</div>
                    </td>
                    <td className={styles.muted}>
                      {item.axis} / {item.category}
                    </td>
                    <td>{item.requiredLevel}</td>
                    <td>{item.coveredLevel}</td>
                    <td
                      className={`${styles.gapBadge} ${item.gap > 0 ? styles.gapHigh : styles.gapNone}`}
                    >
                      {item.gap > 0 ? `-${item.gap}` : "充足"}
                    </td>
                    <td className={styles.muted}>{item.taskIds.length}件</td>
                    <td className={styles.muted}>
                      {item.courses.length > 0 ? `${item.courses.length}コース` : "—"}
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
        title={detail ? `${detail.skillId} ${detail.name}` : ""}
        onClose={() => setDetail(null)}
        dirty={dirty}
        busy={saving}
        footer={detail && view === "edit" && canAssess ? (
            <div className={styles.actionRow}>
              <button
                type="button"
                className="primary-button"
                disabled={saving || !assessUserId || !canAssess}
                onClick={async () => {
                  setSaving(true);
                  setError(null);
                  try {
                    await saveVentureSkillAssessment(ventureId, {
                      skillId: detail.skillId,
                      userId: assessUserId,
                      assessedLevel: assessLevel,
                      developmentPlan: assessPlan,
                      dueDate: assessDueDate,
                      evidenceUri: assessEvidence
                    });
                    setDetail(null);
                    refresh();
                  } catch (err: unknown) {
                    setError(err instanceof Error ? err.message : "保存できませんでした。");
                  } finally {
                    setSaving(false);
                  }
                }}
              >
                評価を保存
              </button>

            </div>
        ) : null}
      >
        {detail ? (
          <div>
            <Feedback message={error} error />
            <div className="page-actions" aria-label="スキルの表示切替">
              <button aria-pressed={view === "summary"} onClick={() => setView("summary")}>現在の評価</button>
              {canAssess && <button aria-pressed={view === "edit"} onClick={() => setView("edit")}>評価を編集</button>}
              <button aria-pressed={view === "history"} onClick={() => void loadHistory()}>評価履歴</button>
            </div>
            <div hidden={view !== "summary"}>
            <dl className={styles.detailList}>
              <dt>定義</dt>
              <dd>{detail.definition || skills[detail.skillId]?.definition || "—"}</dd>
              <dt>必要Lv</dt>
              <dd>
                {detail.requiredLevel}（到達 {detail.coveredLevel}）
              </dd>
              <dt>対象タスク</dt>
              <dd className={styles.taskId}>{detail.taskIds.join(", ")}</dd>
            </dl>

            {skills[detail.skillId] ? (
              <Disclosure title="レベルの基準・根拠"><dl className={styles.detailList}>
                <dt>Lv1</dt>
                <dd>{skills[detail.skillId].level1 || "—"}</dd>
                <dt>Lv2</dt>
                <dd>{skills[detail.skillId].level2 || "—"}</dd>
                <dt>Lv3</dt>
                <dd>{skills[detail.skillId].level3 || "—"}</dd>
                <dt>評価に必要な証拠</dt>
                <dd>{skills[detail.skillId].evidence || "—"}</dd>
                <dt>根拠</dt>
                <dd className={styles.taskId}>
                  {skills[detail.skillId].sourceIds.join(", ") || "—"}
                </dd>
                {skills[detail.skillId].note ? (
                  <>
                    <dt>補足</dt>
                    <dd>{skills[detail.skillId].note}</dd>
                  </>
                ) : null}
              </dl></Disclosure>
            ) : null}

            {detail.assessments.length > 0 ? (
              <div className={styles.tableWrap} style={{ marginBottom: 14 }}>
                <table className={styles.table}>
                  <thead>
                    <tr>
                      <th>担当者</th>
                      <th>到達Lv</th>
                      <th>評価の根拠</th><th>育成計画</th>
                    </tr>
                  </thead>
                  <tbody>
                    {detail.assessments.map((assessment) => (
                      <tr key={assessment.id}>
                        <td>{assessment.userName}</td>
                        <td>{assessment.assessedLevel}</td><td>{assessment.evidenceUri || "未登録"}</td>
                        <td className={styles.muted}>{assessment.developmentPlan || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}

            <p className={styles.note}>
              配置の充足には、有効な評価と期間内の稼働余力が必要です。
            </p>

            <p><Link href={`/ventures/${ventureId}/ledgers/assignment`}>工程別スキル割当</Link> / <Link href={`/ventures/${ventureId}/ledgers/role_staffing`}>配置・稼働計画</Link></p>
            <ul>{detail.assignments?.map(a => <li key={`${a.taskId}/${a.roleId}`}>{a.taskId} / {a.roleId}: 必要Lv{a.requiredLevel} / 有効な配置Lv{a.coveredLevel} / 不足{a.gap}</li>)}</ul>
              {detail.courses.length > 0 ? (
                detail.courses.map((course) => (
                  <Link
                    key={course.courseSlug}
                    href={`/courses/${course.courseSlug}`}
                    className="ghost-button"
                    title={course.note}
                  >
                    {course.title}（Lv{course.coversLevel}まで）
                  </Link>
                ))
              ) : (
                <span className={styles.muted}>
                  対応するコースは未登録です。
                </span>
              )}
            </div>
            {view === "history" && <div><Feedback message={historyError} error />
              {history === null && !historyError ? <SkeletonRow /> : <>
                {!history?.some(row => row.skillId === detail.skillId) && <p>評価履歴はありません。</p>}
                {history?.filter(row => row.skillId === detail.skillId).map(row => <article key={row.id} className={styles.phaseCard}>
                  <strong>{members.find(m => m.userId === row.userId)?.userName || row.userId} · {row.revoked ? "取消" : `Lv${row.assessedLevel}`}</strong>
                  <p>{row.assessedAt ? new Date(row.assessedAt).toLocaleString("ja-JP") : "日時未記録"} / 有効期限：{row.dueDate || "未設定"}</p>
                  <p>{row.developmentPlan || "計画・取消理由は未記録"}</p>
                  <Disclosure title="評価の証拠・記録ID"><p>{row.evidenceUri || "証拠未登録"}</p><p>記録ID：{row.id}</p><p>評価者：{members.find(m => m.userId === row.assessedBy)?.userName || row.assessedBy || "未記録"}</p><p>前の記録：{row.supersedesId || "なし"}</p></Disclosure>
                </article>)}
              </>}
            </div>}
            <div hidden={view !== "edit" || !canAssess}>
            <p className={styles.note}>本人以外の評価を記録します。訂正・取消後も履歴は残ります。</p>
            {dirty && <p role="status">編集中です。担当者を変える前に保存してください。</p>}
            <div className={styles.formGrid}>
              <label className={styles.field}>
                担当者
                <select
                  value={assessUserId}
                  disabled={!canAssess || dirty || saving}
                  onChange={(event) => changeAssessUser(event.target.value)}
                >
                  <option value="">選択してください</option>
                  {assessable.map((member) => (
                    <option key={member.id} value={member.userId}>
                      {member.userName}（{member.roleId}）
                    </option>
                  ))}
                </select>
              </label>
              <label className={styles.field}>
                到達Lv
                <select
                  value={assessLevel}
                  disabled={!canAssess}
                  onChange={(event) => setAssessLevel(Number(event.target.value))}
                >
                  {[0, 1, 2, 3].map((value) => (
                    <option key={value} value={value}>
                      Lv{value}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <label className={styles.field}>評価有効期限<input type="date" value={assessDueDate} disabled={!canAssess} onChange={e => setAssessDueDate(e.target.value)} /></label>
            <label className={styles.field}>評価根拠のリンク<input value={assessEvidence} disabled={!canAssess} onChange={e => setAssessEvidence(e.target.value)} /></label>
            <label className={styles.field}>
              育成・支援の計画
              <textarea
                value={assessPlan}
                onChange={(event) => setAssessPlan(event.target.value)}
                placeholder="例: 該当コースを受講後、B2-04で指導付き実施"
              />
            </label>

            {canAssess && currentAssessment && <p><button className="danger-button" onClick={() => { setCancelReason(""); setCancelOpen(true); }}>評価を取り消す</button></p>}

            </div>
            <Modal open={cancelOpen} title="評価を取り消しますか？" onClose={() => { setCancelOpen(false); setCancelReason(""); }} busy={saving} dirty={!!cancelReason}>
              <p>この評価は配置判定に使われなくなります。履歴は保持されます。</p><Feedback message={error} error />
              <label className={styles.field}>取消理由<input value={cancelReason} onChange={e => setCancelReason(e.target.value)} /></label>
              <button type="button" disabled={saving || !cancelReason.trim()} onClick={async () => {
                setSaving(true); setError(null);
                try { await saveVentureSkillAssessment(ventureId, {skillId: detail.skillId, userId: assessUserId, assessedLevel: 0, revoked: true, developmentPlan: cancelReason}); setCancelOpen(false); setDetail(null); refresh(); }
                catch (err) { setError(err instanceof Error ? err.message : "取消できませんでした"); }
                finally { setSaving(false); }
              }}>評価を取り消す</button>
            </Modal>

          </div>
        ) : null}
      </Drawer>
    </>
  );
}
