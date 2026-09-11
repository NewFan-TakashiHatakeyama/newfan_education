"use client";
import { use, useEffect, useState } from "react";
import Link from "next/link";
import type { VentureGate } from "@newfan/contracts";
import { fetchVentureGates } from "@/lib/api";
import { Section } from "@/app/components/ui/Section";
import { Disclosure } from "@/app/components/ui/Disclosure";
import { SkeletonRow } from "@/app/components/ui/Skeleton";
import { GateDecisionPill, VentureNav } from "../../VentureNav";
import styles from "../../ventures.module.css";

export default function VentureGatesPage({ params }: { params: Promise<{ ventureId: string }> }) {
  const { ventureId } = use(params);
  const [gates, setGates] = useState<VentureGate[] | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { fetchVentureGates(ventureId).then(r => setGates(r.items)).catch(e => setError(String(e))); }, [ventureId]);
  return <><VentureNav ventureId={ventureId} />
    <Section title="ゲート承認" meta="条件と証拠を満たし、独立確認が済むと承認が有効になります。" theme="company"
      actions={<Link href={`/ventures/${ventureId}/ledgers/gate_run`} className="primary-button">承認記録を開く</Link>}>
      {error && <p role="alert">{error}</p>}
      {!gates && !error ? <SkeletonRow /> : <div className={styles.phaseGrid}>{gates?.map(g => <article className={styles.phaseCard} key={g.gateId}>
        <h3>{g.subject} <small className={styles.muted}>{g.gateId}</small></h3>
        <GateDecisionPill value={g.effective ? g.decision : "未審査"} />
        <p><strong>{g.effective ? "確認済み" : g.validity || "確認が必要です"}</strong></p>
        <p>完了タスク {g.completedTaskCount} / {g.appliedTaskCount}</p>
        <Disclosure title="判断内容・必要な証拠">
          <p>記録された判断：{g.recordedDecision}</p>
          <p>対象：{g.scope || "未入力"}</p><p>判断記録：{g.gateRunId || "未作成"}</p>
          <p>承認ロール：{g.approverRoleId}</p><p>{g.requiredEvidence}</p>
        </Disclosure>
        <Link href={`/ventures/${ventureId}/ledgers/gate_run`}>判断内容を確認</Link>
      </article>)}</div>}
    </Section></>;
}
