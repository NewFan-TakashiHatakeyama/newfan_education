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
  fetchVentureMasterSkills,
  fetchVentureMembers,
  fetchVentureSkillGap,
  saveVentureSkillAssessment
} from "@/lib/api";

import { Section } from "@/app/components/ui/Section";
import { Drawer } from "@/app/components/ui/Drawer";
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
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [onlyGap, setOnlyGap] = useState(true);
  const [detail, setDetail] = useState<VentureSkillGapItem | null>(null);
  const [assessUserId, setAssessUserId] = useState("");
  const [assessLevel, setAssessLevel] = useState(0);
  const [assessPlan, setAssessPlan] = useState("");
  const { userId: selfUserId, canAssess } = useVentureRole();

  const refresh = useCallback(() => {
    fetchVentureSkillGap(ventureId)
      .then(setGap)
      .catch((err: unknown) => {
        setGap({ items: [], appliedTaskCount: 0, gapCount: 0 });
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
    () => members.filter((member) => member.userId !== selfUserId),
    [members, selfUserId]
  );

  /** その人の現在の到達Lv。未評価なら0。チーム最高値を初期値にすると誤って上書きする。 */
  const levelOf = (item: VentureSkillGapItem, userId: string) =>
    item.assessments.find((assessment) => assessment.userId === userId)?.assessedLevel ?? 0;

  const openDetail = (item: VentureSkillGapItem) => {
    const first = assessable[0]?.userId ?? "";
    setDetail(item);
    setAssessUserId(first);
    setAssessLevel(first ? levelOf(item, first) : 0);
    setAssessPlan("");
  };

  const changeAssessUser = (userId: string) => {
    setAssessUserId(userId);
    if (detail) setAssessLevel(levelOf(detail, userId));
  };

  return (
    <>
      <VentureNav ventureId={ventureId} />

      <Section
        title="スキル充足"
        meta="適用タスクが求めるLvと、要員の到達Lvの差です。不足しているスキルは学習に戻して埋めます。"
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
            不足しているものだけ表示
          </label>
          {gap ? (
            <span className={styles.count}>
              適用タスク {gap.appliedTaskCount}件 / 要求スキル {gap.items.length}件 / 不足{" "}
              {gap.gapCount}件
            </span>
          ) : null}
        </div>

        {gap === null ? (
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
      >
        {detail ? (
          <div>
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
              <dl className={styles.detailList}>
                <dt>Lv1</dt>
                <dd>{skills[detail.skillId].level1 || "—"}</dd>
                <dt>Lv2</dt>
                <dd>{skills[detail.skillId].level2 || "—"}</dd>
                <dt>Lv3</dt>
                <dd>{skills[detail.skillId].level3 || "—"}</dd>
                <dt>判定エビデンス</dt>
                <dd>{skills[detail.skillId].evidence || "—"}</dd>
                <dt>根拠</dt>
                <dd className={styles.taskId}>
                  {skills[detail.skillId].sourceIds.join(", ") || "—"}
                </dd>
                {skills[detail.skillId].note ? (
                  <>
                    <dt>再編・適用メモ</dt>
                    <dd>{skills[detail.skillId].note}</dd>
                  </>
                ) : null}
              </dl>
            ) : null}

            {detail.assessments.length > 0 ? (
              <div className={styles.tableWrap} style={{ marginBottom: 14 }}>
                <table className={styles.table}>
                  <thead>
                    <tr>
                      <th>担当者</th>
                      <th>到達Lv</th>
                      <th>育成計画</th>
                    </tr>
                  </thead>
                  <tbody>
                    {detail.assessments.map((assessment) => (
                      <tr key={assessment.id}>
                        <td>{assessment.userName}</td>
                        <td>{assessment.assessedLevel}</td>
                        <td className={styles.muted}>{assessment.developmentPlan || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}

            <p className={styles.note}>
              到達Lvを記録すると不足が更新されます。不足が残る場合は、学習コースで埋めてから
              担当を割り当ててください。評価は第三者が行います（自分自身は選べません）。
            </p>

            <div className={styles.formGrid}>
              <label className={styles.field}>
                担当者
                <select
                  value={assessUserId}
                  disabled={!canAssess}
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
            <label className={styles.field}>
              育成・採用・外部支援の計画
              <textarea
                value={assessPlan}
                onChange={(event) => setAssessPlan(event.target.value)}
                placeholder="例: 該当コースを受講後、B2-04で指導付き実施"
              />
            </label>

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
                      developmentPlan: assessPlan
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
                到達Lvを記録
              </button>
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
                  このスキルに対応する学習コースはまだありません。
                </span>
              )}
            </div>
          </div>
        ) : null}
      </Drawer>
    </>
  );
}
