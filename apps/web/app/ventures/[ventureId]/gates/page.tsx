"use client";
import { use, useEffect, useState } from "react";
import Link from "next/link";
import type { VentureGate } from "@newfan/contracts";
import { fetchVentureGates } from "@/lib/api";
import { Section } from "@/app/components/ui/Section";
import { VentureNav } from "../../VentureNav";
import styles from "../../ventures.module.css";

export default function VentureGatesPage({ params }: { params: Promise<{ ventureId: string }> }) {
  const { ventureId } = use(params);
  const [gates, setGates] = useState<VentureGate[]>([]);
  const [error, setError] = useState("");
  useEffect(() => { fetchVentureGates(ventureId).then(r => setGates(r.items)).catch(e => setError(String(e))); }, [ventureId]);
  return <><VentureNav ventureId={ventureId} />
    <Section title="ゲート判断と正本確認" meta="正本確認が済んでも、評価・条件が未充足なら有効な承認にはなりません。" theme="company">
      {error && <p role="alert">{error}</p>}
      <Link href={`/ventures/${ventureId}/ledgers/gate_run`} className="primary-button">判断の作成・確認・取消・履歴</Link>
      <div className={styles.phaseGrid}>{gates.map(g => <article className={styles.phaseCard} key={g.gateId}>
        <h3>{g.gateId} {g.subject}</h3>
        <p>記録された判断：{g.recordedDecision}</p>
        <p><strong>{g.effective ? `有効な判断：${g.decision}` : `未確認・未充足：${g.validity}`}</strong></p>
        <p>対象：{g.scope || "未入力"} / 判断Run：{g.gateRunId || "未作成"}</p>
        <p>責任ロール：{g.approverRoleId} / 証拠・前提充足：{g.completedTaskCount} / {g.appliedTaskCount}</p>
        <p>{g.requiredEvidence}</p>
      </article>)}</div>
    </Section></>;
}
