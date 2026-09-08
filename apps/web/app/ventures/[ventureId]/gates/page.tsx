"use client";

import { use, useCallback, useEffect, useState } from "react";

import type { VentureGate } from "@newfan/contracts";

import { fetchVentureGates, updateVentureGate } from "@/lib/api";

import { Section } from "@/app/components/ui/Section";
import { SkeletonRow } from "@/app/components/ui/Skeleton";

import { GateDecisionPill, VentureNav } from "../../VentureNav";
import { useVentureRole } from "../../useVentureRole";
import styles from "../../ventures.module.css";

export default function VentureGatesPage({
  params
}: {
  params: Promise<{ ventureId: string }>;
}) {
  const { ventureId } = use(params);
  const [gates, setGates] = useState<VentureGate[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [openGateId, setOpenGateId] = useState<string | null>(null);
  const { canManage } = useVentureRole();

  const refresh = useCallback(() => {
    fetchVentureGates(ventureId)
      .then((res) => setGates(res.items))
      .catch((err: unknown) => {
        setGates([]);
        setError(err instanceof Error ? err.message : "ゲートを取得できませんでした。");
      });
  }, [ventureId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const patch = async (gate: VentureGate, payload: Parameters<typeof updateVentureGate>[2]) => {
    setSaving(true);
    setError(null);
    try {
      const updated = await updateVentureGate(ventureId, gate.id, payload);
      setGates((current) =>
        current ? current.map((item) => (item.id === updated.id ? updated : item)) : current
      );
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "更新できませんでした。");
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <VentureNav ventureId={ventureId} />

      <Section
        title="ゲート承認記録"
        meta="判断できる選択肢は工程マスタの定義に従います。事業判断で品質・法令の不合格を上書きしません。"
        theme="company"
      >
        {error ? <p className={styles.error}>{error}</p> : null}

        {gates === null ? (
          <SkeletonRow />
        ) : (
          <div style={{ display: "grid", gap: 12 }}>
            {gates.map((gate) => {
              const open = openGateId === gate.id;
              return (
                <div key={gate.id} className={styles.phaseCard}>
                  <div className={styles.phaseHead}>
                    <span className={styles.phaseId}>{gate.gateId}</span>
                    <span className={styles.phaseName}>{gate.subject}</span>
                    <span style={{ marginLeft: "auto" }}>
                      <GateDecisionPill value={gate.decision} />
                    </span>
                  </div>

                  <p className={styles.muted}>
                    最終承認ロール {gate.approverRoleId} / 標準タスク {gate.standardTaskId} / 適用
                    {gate.appliedTaskCount}件中 完了{gate.completedTaskCount}件・未承認
                    {gate.unapprovedTaskCount}件
                  </p>
                  <p className={styles.note}>必要証拠: {gate.requiredEvidence}</p>

                  {gate.decidedAt ? (
                    <p className={styles.muted}>
                      承認者 {gate.decidedByName || gate.decidedBy}
                      {gate.recordedByName && gate.recordedByName !== gate.decidedByName
                        ? `（記録 ${gate.recordedByName}）`
                        : ""}{" "}
                      / {new Date(gate.decidedAt).toLocaleString("ja-JP")} に判断
                      {gate.conditions ? ` / 条件: ${gate.conditions}` : ""}
                      {gate.conditionDue ? `（期限 ${gate.conditionDue}）` : ""}
                    </p>
                  ) : null}

                  {canManage ? (
                    <button
                      type="button"
                      className={styles.rowButton}
                      onClick={() => setOpenGateId(open ? null : gate.id)}
                    >
                      {open ? "入力を閉じる" : "判断を記録する"}
                    </button>
                  ) : (
                    <p className={styles.muted}>判断の記録は事業責任者・PdMが行います。</p>
                  )}

                  {open && canManage ? (
                    <div>
                      <div className={styles.formGrid}>
                        <label className={styles.field}>
                          判断
                          <select
                            value={gate.decision}
                            disabled={saving}
                            onChange={(event) => patch(gate, { decision: event.target.value })}
                          >
                            {gate.allowedDecisions.map((value) => (
                              <option key={value} value={value}>
                                {value}
                              </option>
                            ))}
                          </select>
                        </label>
                        <label className={styles.field}>
                          対象範囲・版
                          <input
                            defaultValue={gate.scope}
                            disabled={saving}
                            onBlur={(event) => patch(gate, { scope: event.target.value })}
                          />
                        </label>
                        <label className={styles.field}>
                          条件の期限
                          <input
                            type="date"
                            defaultValue={gate.conditionDue}
                            disabled={saving}
                            onBlur={(event) => patch(gate, { conditionDue: event.target.value })}
                          />
                        </label>
                        <label className={styles.field}>
                          承認者（実名）
                          <input
                            defaultValue={gate.decidedByName}
                            disabled={saving}
                            onBlur={(event) => patch(gate, { decidedByName: event.target.value })}
                          />
                        </label>
                      </div>
                      <label className={styles.field} style={{ marginTop: 10 }}>
                        証拠パッケージのURI
                        <input
                          defaultValue={gate.evidencePackageUri}
                          disabled={saving}
                          onBlur={(event) =>
                            patch(gate, { evidencePackageUri: event.target.value })
                          }
                        />
                      </label>
                      <label className={styles.field}>
                        条件・制約
                        <textarea
                          defaultValue={gate.conditions}
                          disabled={saving}
                          placeholder="条件付承認にする場合は、条件・所有者・期限・期限切れ時の扱いを書く"
                          onBlur={(event) => patch(gate, { conditions: event.target.value })}
                        />
                      </label>
                      <label className={styles.field}>
                        次のアクション
                        <textarea
                          defaultValue={gate.nextAction}
                          disabled={saving}
                          onBlur={(event) => patch(gate, { nextAction: event.target.value })}
                        />
                      </label>
                      <label className={styles.field}>
                        再審査のトリガー
                        <input
                          defaultValue={gate.reviewTrigger}
                          disabled={saving}
                          onBlur={(event) => patch(gate, { reviewTrigger: event.target.value })}
                        />
                      </label>
                    </div>
                  ) : null}
                </div>
              );
            })}
          </div>
        )}
      </Section>
    </>
  );
}
