"use client";

import { use, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import type { VentureApplicability, VentureMaster, VentureSummary } from "@newfan/contracts";

import {
  addVentureMember,
  deleteVenture,
  fetchVentureMaster,
  fetchVentureSummary,
  getLearners,
  removeVentureMember,
  updateVenture
} from "@/lib/api";

import { PageHero } from "@/app/components/ui/PageHero";
import { Section } from "@/app/components/ui/Section";
import { SkeletonRow } from "@/app/components/ui/Skeleton";
import { EmptyState } from "@/app/components/ui/EmptyState";

import { GateDecisionPill, VentureNav } from "../VentureNav";
import { useVentureRole } from "../useVentureRole";
import styles from "../ventures.module.css";

const APPLICABILITY: VentureApplicability[] = ["未判定", "適用", "対象外"];
const VENTURE_STATUS = ["計画中", "進行中", "停止", "終了"];

export default function VentureOverviewPage({
  params
}: {
  params: Promise<{ ventureId: string }>;
}) {
  const { ventureId } = use(params);
  const router = useRouter();
  const [summary, setSummary] = useState<VentureSummary | null>(null);
  const [master, setMaster] = useState<VentureMaster | null>(null);
  const [learners, setLearners] = useState<{ id: string; name: string }[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const { canManage } = useVentureRole();

  const [memberUserId, setMemberUserId] = useState("");
  const [memberRoleId, setMemberRoleId] = useState("");
  const [memberNote, setMemberNote] = useState("");
  const [deleteConfirmName, setDeleteConfirmName] = useState("");

  const refresh = useCallback(() => {
    fetchVentureSummary(ventureId)
      .then(setSummary)
      .catch((err: unknown) =>
        setError(err instanceof Error ? err.message : "案件の概要を取得できませんでした。")
      );
  }, [ventureId]);

  useEffect(() => {
    refresh();
    fetchVentureMaster()
      .then(setMaster)
      .catch(() => setMaster(null));
    getLearners()
      .then((res) => setLearners(res.items.map((item) => ({ id: item.id, name: item.name }))))
      .catch(() => setLearners([]));
  }, [refresh]);

  const patchVenture = async (payload: Parameters<typeof updateVenture>[1]) => {
    setSaving(true);
    setError(null);
    try {
      await updateVenture(ventureId, payload);
      refresh();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "更新できませんでした。");
    } finally {
      setSaving(false);
    }
  };

  if (!summary) {
    return (
      <>
        <VentureNav ventureId={ventureId} />
        {error ? <p className={styles.error}>{error}</p> : <SkeletonRow />}
      </>
    );
  }

  const venture = summary.venture;
  const appliedTotal = summary.phases.reduce((sum, phase) => sum + phase.applied, 0);
  const completedTotal = summary.phases.reduce((sum, phase) => sum + phase.completed, 0);
  const undecidedTotal = summary.phases.reduce((sum, phase) => sum + phase.undecided, 0);

  return (
    <>
      <VentureNav ventureId={ventureId} />

      <PageHero
        eyebrow={`${venture.currentPhaseId} / 規模 ${venture.scale} / ${venture.riskTier}`}
        title={venture.name}
        lead={venture.summary || "概要は未入力です。"}
        theme="company"
        metrics={[
          {
            label: "適用タスクの完了",
            value: `${completedTotal} / ${appliedTotal}`,
            icon: "clipboardCheck",
            progress: appliedTotal ? completedTotal / appliedTotal : 0
          },
          { label: "適用判定待ち", value: undecidedTotal, icon: "circleAlert" },
          { label: "スキル不足", value: summary.skillGapCount, icon: "graduationCap" },
          { label: "要員", value: summary.members.length, icon: "users" }
        ]}
      />

      {error ? <p className={styles.error}>{error}</p> : null}

      <Section
        title="案件の前提"
        meta="規模・Risk Tier・機能の条件は、工程タスクの適用提案に使われます。人が決めた判定は上書きされません。"
        theme="company"
      >
        <div className={styles.formGrid}>
          <label className={styles.field}>
            状態
            <select
              value={venture.status}
              disabled={saving || !canManage}
              onChange={(event) => patchVenture({ status: event.target.value as never })}
            >
              {VENTURE_STATUS.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
          <label className={styles.field}>
            現在の工程
            <select
              value={venture.currentPhaseId}
              disabled={saving || !canManage}
              onChange={(event) => patchVenture({ currentPhaseId: event.target.value })}
            >
              {summary.phases.map((phase) => (
                <option key={phase.phaseId} value={phase.phaseId}>
                  {phase.phaseId} {phase.name}
                </option>
              ))}
            </select>
          </label>
          <label className={styles.field}>
            規模
            <select
              value={venture.scale}
              disabled={saving || !canManage}
              onChange={(event) => patchVenture({ scale: event.target.value as "S" | "M" | "L" })}
            >
              <option value="S">S（小規模）</option>
              <option value="M">M（中規模）</option>
              <option value="L">L（大規模）</option>
            </select>
          </label>
          <label className={styles.field}>
            Risk Tier
            <select
              value={venture.riskTier}
              disabled={saving || !canManage}
              onChange={(event) => patchVenture({ riskTier: event.target.value })}
            >
              {(master?.riskTiers ?? []).map((tier) => (
                <option key={tier.tierId} value={tier.tierId}>
                  {tier.tierId} {tier.name}
                </option>
              ))}
            </select>
          </label>
        </div>

        {master && master.conditionKeys.length > 0 ? (
          <div style={{ marginTop: 16 }}>
            <p className={styles.muted} style={{ marginBottom: 8 }}>
              機能・条件の判定
            </p>
            <div className={styles.conditionGrid}>
              {master.conditionKeys.map((key) => (
                <label key={key} className={styles.field}>
                  {key}
                  <select
                    value={venture.conditions[key] ?? "未判定"}
                    disabled={saving || !canManage}
                    onChange={(event) =>
                      patchVenture({
                        conditions: { [key]: event.target.value as VentureApplicability }
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
              ))}
            </div>
          </div>
        ) : null}
      </Section>

      <Section
        title="工程の進捗"
        meta="七工程は反復・並行できます。適用判定が済んでいないタスクは進捗に数えません。"
        theme="company"
        actions={
          <Link href={`/ventures/${ventureId}/tasks`} className="ghost-button">
            工程タスクを開く
          </Link>
        }
      >
        <div className={styles.phaseGrid}>
          {summary.phases.map((phase) => {
            const done = phase.applied ? phase.completed / phase.applied : 0;
            const running = phase.applied ? phase.inProgress / phase.applied : 0;
            return (
              <div key={phase.phaseId} className={styles.phaseCard}>
                <div className={styles.phaseHead}>
                  <span className={styles.phaseId}>{phase.phaseId}</span>
                  <span className={styles.phaseName}>{phase.name}</span>
                </div>
                <div className={styles.bar} aria-hidden>
                  <span className={styles.barDone} style={{ width: `${done * 100}%` }} />
                  <span className={styles.barProgress} style={{ width: `${running * 100}%` }} />
                </div>
                <div className={styles.phaseStats}>
                  <span>適用 {phase.applied}</span>
                  <span>完了 {phase.completed}</span>
                  <span>進行 {phase.inProgress}</span>
                  {phase.undecided > 0 ? <span>判定待ち {phase.undecided}</span> : null}
                  {phase.blocked > 0 ? <span>阻害 {phase.blocked}</span> : null}
                </div>
                <Link
                  href={`/ventures/${ventureId}/tasks?phaseId=${phase.phaseId}`}
                  className={styles.rowButton}
                >
                  この工程を見る
                </Link>
              </div>
            );
          })}
        </div>
      </Section>

      <Section
        title="ゲート"
        meta="投資と公開の判断。品質・法令の不合格を事業判断で上書きしません。"
        theme="company"
        actions={
          <Link href={`/ventures/${ventureId}/gates`} className="ghost-button">
            承認記録を開く
          </Link>
        }
      >
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Gate</th>
                <th>判断対象</th>
                <th>判断</th>
                <th>適用タスク</th>
                <th>完了</th>
                <th>未承認</th>
              </tr>
            </thead>
            <tbody>
              {summary.gates.map((gate) => (
                <tr key={gate.id}>
                  <td className={styles.taskId}>{gate.gateId}</td>
                  <td>{gate.subject}</td>
                  <td>
                    <GateDecisionPill value={gate.decision} />
                  </td>
                  <td>{gate.appliedTaskCount}</td>
                  <td>{gate.completedTaskCount}</td>
                  <td>{gate.unapprovedTaskCount}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      <Section
        title="台帳"
        meta="データ・依存・ADR・リスクなど。点検行はマスタ由来で、案件側で入力を埋めます。"
        theme="company"
      >
        <div className={styles.ledgerLinks}>
          {summary.ledgers.map((ledger) => (
            <Link
              key={ledger.key}
              href={`/ventures/${ventureId}/ledgers/${ledger.key}`}
              className={styles.ledgerLink}
            >
              <span className={styles.ledgerName}>{ledger.name}</span>
              <span className={styles.muted}>
                {ledger.total === 0
                  ? "行なし（起票して使う）"
                  : `${ledger.filled} / ${ledger.total} 行に入力あり`}
              </span>
            </Link>
          ))}
        </div>
      </Section>

      <Section
        title="要員"
        meta="ロールは工程マスタの定義（R01〜）に合わせます。担当者は学習者アカウントから選びます。"
        theme="company"
      >
        {canManage ? (
        <div className={styles.toolbar}>
          <label className={styles.field}>
            担当者
            <select value={memberUserId} onChange={(event) => setMemberUserId(event.target.value)}>
              <option value="">選択してください</option>
              {learners.map((learner) => (
                <option key={learner.id} value={learner.id}>
                  {learner.name}
                </option>
              ))}
            </select>
          </label>
          <label className={styles.field}>
            ロール
            <select value={memberRoleId} onChange={(event) => setMemberRoleId(event.target.value)}>
              <option value="">選択してください</option>
              {(master?.roles ?? []).map((role) => (
                <option key={role.roleId} value={role.roleId}>
                  {role.roleId} {role.name}
                </option>
              ))}
            </select>
          </label>
          <label className={styles.field}>
            メモ
            <input
              value={memberNote}
              onChange={(event) => setMemberNote(event.target.value)}
              placeholder="例: 0.5FTE"
            />
          </label>
          <button
            type="button"
            className="primary-button"
            disabled={!memberUserId || !memberRoleId || saving}
            onClick={async () => {
              setSaving(true);
              setError(null);
              try {
                await addVentureMember(ventureId, {
                  userId: memberUserId,
                  roleId: memberRoleId,
                  allocationNote: memberNote
                });
                setMemberUserId("");
                setMemberRoleId("");
                setMemberNote("");
                refresh();
              } catch (err: unknown) {
                setError(err instanceof Error ? err.message : "要員を追加できませんでした。");
              } finally {
                setSaving(false);
              }
            }}
          >
            要員を追加
          </button>
        </div>
        ) : null}

        {summary.members.length === 0 ? (
          <EmptyState
            title="要員が未登録です"
            message="ロールごとに担当者を割り当てると、スキル充足の判定ができます。"
          />
        ) : (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>ロール</th>
                  <th>担当者</th>
                  <th>メモ</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {summary.members.map((member) => (
                  <tr key={member.id}>
                    <td>
                      <span className={styles.taskId}>{member.roleId}</span> {member.roleName}
                    </td>
                    <td>{member.userName}</td>
                    <td className={styles.muted}>{member.allocationNote || "—"}</td>
                    <td>
                      <button
                        type="button"
                        className={styles.rowButton}
                        disabled={saving || !canManage}
                        onClick={async () => {
                          setSaving(true);
                          try {
                            await removeVentureMember(ventureId, member.id);
                            refresh();
                          } catch (err: unknown) {
                            setError(
                              err instanceof Error ? err.message : "要員を外せませんでした。"
                            );
                          } finally {
                            setSaving(false);
                          }
                        }}
                      >
                        外す
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>

      {summary.topSkillGaps.length > 0 ? (
        <Section
          title="不足しているスキル"
          meta="適用タスクが求めるLvに対し、要員の到達Lvが届いていないものです。"
          theme="company"
          actions={
            <Link href={`/ventures/${ventureId}/skills`} className="ghost-button">
              スキル充足を開く
            </Link>
          }
        >
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>スキル</th>
                  <th>軸</th>
                  <th>必要Lv</th>
                  <th>到達Lv</th>
                  <th>不足</th>
                </tr>
              </thead>
              <tbody>
                {summary.topSkillGaps.map((item) => (
                  <tr key={item.skillId}>
                    <td>
                      <span className={styles.taskId}>{item.skillId}</span> {item.name}
                    </td>
                    <td className={styles.muted}>{item.axis}</td>
                    <td>{item.requiredLevel}</td>
                    <td>{item.coveredLevel}</td>
                    <td className={`${styles.gapBadge} ${styles.gapHigh}`}>-{item.gap}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>
      ) : null}

      {canManage ? (
        <Section
          title="危険操作"
          meta="案件と、その工程タスク・ゲート判断・要員・台帳の記録を全て削除します。取り消せません。"
          theme="company"
        >
          <div className={styles.dangerZone}>
            <label className={styles.field} style={{ flex: "1 1 240px" }}>
              事業・サービス名を入力して確認
              <input
                value={deleteConfirmName}
                onChange={(event) => setDeleteConfirmName(event.target.value)}
                placeholder={venture.name}
              />
            </label>
            <button
              type="button"
              className="ghost-button"
              disabled={saving || deleteConfirmName !== venture.name}
              onClick={async () => {
                setSaving(true);
                setError(null);
                try {
                  await deleteVenture(ventureId);
                  router.push("/ventures");
                } catch (err: unknown) {
                  setError(err instanceof Error ? err.message : "案件を削除できませんでした。");
                  setSaving(false);
                }
              }}
            >
              この案件を完全に削除する
            </button>
          </div>
        </Section>
      ) : null}
    </>
  );
}
