"use client";

import { use, useCallback, useEffect, useState } from "react";
import Link from "next/link";


import type { VentureApplicability, VentureMaster, VentureSummary } from "@newfan/contracts";

import {
  addVentureMember,
  fetchVentureMaster,
  fetchVentureSummary,
  getVentureMemberCandidates,
  removeVentureMember,
  updateVenture
} from "@/lib/api";

import { LoadFailure } from "@/app/components/ui/LoadFailure";
import { PageHero } from "@/app/components/ui/PageHero";
import { AppIcon } from "@/app/components/ui/Icon";
import { Drawer, Modal } from "@/app/components/ui/Drawer";
import { Disclosure } from "@/app/components/ui/Disclosure";
import { Feedback } from "@/app/components/ui/Feedback";
import { Section } from "@/app/components/ui/Section";
import { SkeletonRow } from "@/app/components/ui/Skeleton";
import { EmptyState } from "@/app/components/ui/EmptyState";

import { GateDecisionPill, VentureNav } from "../VentureNav";
import { useVentureRole } from "../useVentureRole";
import styles from "../ventures.module.css";
import { LedgerDirectory } from "../LedgerDirectory";
import { DecisionPanel } from "../DecisionPanel";

const APPLICABILITY: VentureApplicability[] = ["未判定", "適用", "対象外"];
const VENTURE_STATUS = ["計画中", "進行中", "停止", "終了", "アーカイブ"];

export default function VentureOverviewPage({
  params
}: {
  params: Promise<{ ventureId: string }>;
}) {
  const { ventureId } = use(params);
  const [summary, setSummary] = useState<VentureSummary | null>(null);
  const [master, setMaster] = useState<VentureMaster | null>(null);
  const [learners, setLearners] = useState<{ id: string; name: string }[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [showMembers, setShowMembers] = useState(false);
  const [reopenReason, setReopenReason] = useState("");
  const [reopenOpen, setReopenOpen] = useState(false);
  const [archiveConfirm, setArchiveConfirm] = useState(false);
  const [removeTarget, setRemoveTarget] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const { canManage } = useVentureRole(ventureId);

  const [memberUserId, setMemberUserId] = useState("");
  const [memberRoleId, setMemberRoleId] = useState("");
  const [memberNote, setMemberNote] = useState("");
  const [riskEvidence, setRiskEvidence] = useState("");

  const refresh = useCallback(() => {
    fetchVentureSummary(ventureId)
      .then(setSummary)
      .catch((err: unknown) => { setSummary(null); setError(err instanceof Error ? err.message : "案件の概要を取得できませんでした。"); });
  }, [ventureId]);

  useEffect(() => {
    refresh();
    fetchVentureMaster()
      .then(setMaster)
      .catch(() => setMaster(null));
    getVentureMemberCandidates(ventureId)
      .then((res) => setLearners(res.items.map((item) => ({ id: item.id, name: item.name }))))
      .catch(() => setLearners([]));
  }, [refresh, ventureId]);

  const patchVenture = async (payload: Parameters<typeof updateVenture>[1]) => {
    setSaving(true);
    setError(null);
    try {
      await updateVenture(ventureId, payload);
      window.dispatchEvent(new Event("venture-updated"));
      refresh();
      setNotice("変更を保存しました。");
      return true;
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "更新できませんでした。");
      return false;
    } finally {
      setSaving(false);
    }
  };

  if (!summary) {
    return (
      <>
        <VentureNav ventureId={ventureId} />
        {error ? <LoadFailure onRetry={() => { setError(null); refresh(); }} /> : <SkeletonRow />}
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

      {venture.status === "アーカイブ" && <section><strong>アーカイブ済み · 閲覧専用</strong><p>編集するには、理由を記録して案件を再開してください。</p>
        {venture.capabilities?.canReopen && <button onClick={() => setReopenOpen(true)}>案件を再開</button>}
      </section>}
      <PageHero
        eyebrow={`${venture.currentPhaseId} / 規模 ${venture.scale} / ${venture.riskTier}`}
        title={venture.name}
        lead={venture.summary || "概要は未入力です。"}
        theme="company"
        actions={<><button className="ghost-button" onClick={() => setShowSettings(true)}>案件設定</button><button className="ghost-button" onClick={() => setShowMembers(true)}>メンバー管理</button></>}
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

      <Feedback message={error} error /><Feedback message={notice} />

      {(undecidedTotal > 0 || summary.skillGapCount > 0) && <div className="page-actions" aria-label="要対応事項">
        {undecidedTotal > 0 && <Link className="ghost-button" href={`/ventures/${ventureId}/tasks?applicability=未判定`}>適用範囲を確認 · {undecidedTotal}件</Link>}
        {summary.skillGapCount > 0 && <Link className="ghost-button" href={`/ventures/${ventureId}/skills`}>不足スキルを確認 · {summary.skillGapCount}件</Link>}
      </div>}
      <DecisionPanel ventureId={ventureId} decisions={summary.decisions} />
      <Section
        title="工程の進捗"
        meta="適用が確定したタスクの進捗です。"
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
                  <Link
                    href={`/ventures/${ventureId}/tasks?phaseId=${phase.phaseId}`}
                    className={styles.phaseOpenLink}
                    aria-label={`${phase.name}のタスクを開く`}
                    title={`${phase.name}のタスクを開く`}
                  >
                    <AppIcon name="arrowRight" size={18} />
                  </Link>
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
              </div>
            );
          })}
        </div>
      </Section>

      <Section
        title="ゲート"
        meta="各段階の承認状況を確認できます。"
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
                    <GateDecisionPill value={gate.effective ? gate.decision : "未審査"} /><small>{gate.validity}</small>
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
        meta="必要な記録を選んで開きます。"
        theme="company"
      >
        <LedgerDirectory ventureId={ventureId} ledgers={summary.ledgers} />
      </Section>

      {summary.topSkillGaps.length > 0 ? (
        <Section
          title="不足しているスキル"
          meta="必要なレベルに達していないスキルです。"
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

      <Drawer open={showSettings} title="案件設定" onClose={() => { setShowSettings(false); setRiskEvidence(""); }} busy={saving} dirty={!!riskEvidence}>
      <Section
        title="前提条件"
        meta="変更は自動保存されます。適用範囲の確定はタスク画面で行います。"
        theme="company"
      >
        <Feedback message={error} error />
        <Feedback message={notice} />
        <div className={styles.formGrid}>
          <label className={styles.field}>
            状態
            <select
              value={venture.status}
              disabled={saving || !canManage}
              onChange={(event) => patchVenture({ status: event.target.value as never })}
            >
              {VENTURE_STATUS.filter(value => value !== "アーカイブ" || venture.status === "アーカイブ").map((value) => (
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
            リスク区分
            <select
              value={venture.riskTier}
              disabled={saving || !canManage}
              onChange={(event) => patchVenture({ riskTier: event.target.value })}
            >
              <option value="未判定">未判定</option>
              {(master?.riskTiers ?? []).map((tier) => (
                <option key={tier.tierId} value={tier.tierId}>
                  {tier.tierId} {tier.name}
                </option>
              ))}
            </select>
          </label>
        </div>

        <p>リスク確認：{venture.governance?.riskState || "未確認"}</p>
        <label className={styles.field}>リスク判定の根拠
          <textarea defaultValue={venture.riskTierRationale} disabled={!canManage || saving}
            onBlur={e => patchVenture({ riskTierRationale: e.target.value })} />
        </label>
        <label className={styles.field}>判定根拠のリンク<input value={riskEvidence} onChange={e => setRiskEvidence(e.target.value)} /></label>
        <button disabled={venture.status === "アーカイブ" || saving || !venture.capabilities?.roleIds.includes("R19") || !riskEvidence}
          onClick={() => patchVenture({ confirmRisk: true, riskEvidenceUri: riskEvidence }).then(saved => { if (saved) setRiskEvidence(""); })}>リスク判定を確認</button>
        {master && master.conditionKeys.length > 0 ? (
          <Disclosure title="機能・条件の設定">
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
          </Disclosure>
        ) : null}
      </Section>

        {canManage && <Disclosure title="案件の保管"><p>履歴を保持して案件をアーカイブします。</p><button className="danger-button" onClick={() => setArchiveConfirm(true)}>案件をアーカイブ</button></Disclosure>}
      </Drawer>
      <Drawer open={showMembers} title="メンバー管理" onClose={() => { setShowMembers(false); setMemberUserId(""); setMemberRoleId(""); setMemberNote(""); }} busy={saving} dirty={!!memberUserId || !!memberRoleId || !!memberNote}>
      <Section
        title="担当メンバー"
        meta="独立確認者は管理者が任命します。実施・管理担当との兼務はできません。"
        theme="company"
      >
        <Feedback message={error} error />
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
                        onClick={() => setRemoveTarget(member.id)}
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

      </Drawer>
      <Modal open={reopenOpen} title="案件を再開" onClose={() => { setReopenOpen(false); setReopenReason(""); }} dirty={!!reopenReason} busy={saving}>
        <p>状態を進行中に戻します。リスク前提は再確認が必要です。</p><Feedback message={error} error />
        <label>再開理由<textarea value={reopenReason} onChange={e => setReopenReason(e.target.value)} maxLength={2000} /></label>
        <button className="primary-button" disabled={saving || !reopenReason.trim()} onClick={async () => { if (await patchVenture({status: "進行中", reopenReason})) { setReopenOpen(false); setReopenReason(""); } }}>理由を記録して再開</button>
      </Modal>
      <Modal open={archiveConfirm} title="案件をアーカイブしますか？" onClose={() => setArchiveConfirm(false)} busy={saving}>
        <p>タスク・台帳・評価が閲覧専用になります。保管時の記録は保持され、再開には理由が必要です。</p><Feedback message={error} error />
        <button className="danger-button" disabled={saving} onClick={async () => { if (await patchVenture({ status: "アーカイブ" })) { setArchiveConfirm(false); setShowSettings(false); } }}>アーカイブする</button>
      </Modal>
      <Modal open={removeTarget !== null} title="メンバーを外しますか？" onClose={() => setRemoveTarget(null)} busy={saving}>
        <p>この案件の担当から外れます。担当タスクとスキルの充足状況を再確認してください。</p><Feedback message={error} error />
        <button className="danger-button" disabled={saving} onClick={async () => {
          if (!removeTarget) return; setSaving(true); setError(null);
          try { await removeVentureMember(ventureId, removeTarget); setRemoveTarget(null); refresh(); }
          catch (err) { setError(err instanceof Error ? err.message : "メンバーを外せませんでした。"); }
          finally { setSaving(false); }
        }}>メンバーを外す</button>
      </Modal>
    </>
  );
}
