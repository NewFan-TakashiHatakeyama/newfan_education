"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";

import type { Venture, VentureApplicability, VentureMaster } from "@newfan/contracts";

import { createVenture, fetchVentureMaster, fetchVentures } from "@/lib/api";

import { useVentureRole } from "./useVentureRole";

import { PageHero } from "@/app/components/ui/PageHero";
import { Section } from "@/app/components/ui/Section";
import { EmptyState } from "@/app/components/ui/EmptyState";
import { SkeletonRow } from "@/app/components/ui/Skeleton";

import styles from "./ventures.module.css";

const OFFERING_TYPES = ["社内事業", "B2B", "B2C", "複合"];
const APPLICABILITY: VentureApplicability[] = ["未判定", "適用", "対象外"];

export default function VenturesPage() {
  const [items, setItems] = useState<Venture[] | null>(null);
  const [master, setMaster] = useState<VentureMaster | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [showForm, setShowForm] = useState(false);
  // 案件の作成・更新は admin と recruiter だけ。それ以外は要員として登録された
  // 案件しか見えないので、押せない操作を出さず、何をすれば見えるかを案内する。
  const { role, canManage } = useVentureRole();

  const [name, setName] = useState("");
  const [summary, setSummary] = useState("");
  const [offeringType, setOfferingType] = useState("社内事業");
  const [industry, setIndustry] = useState("");
  const [scale, setScale] = useState("S");
  const [riskTier, setRiskTier] = useState("未判定");
  const [conditions, setConditions] = useState<Record<string, VentureApplicability>>({});

  const refresh = () => {
    fetchVentures()
      .then((res) => setItems(res.items))
      .catch((err: unknown) => {
        setItems([]);
        setError(err instanceof Error ? err.message : "案件一覧を取得できませんでした。");
      });
  };

  useEffect(() => {
    refresh();
    fetchVentureMaster()
      .then(setMaster)
      .catch(() => setMaster(null));
  }, []);

  const handleCreate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setCreating(true);
    setError(null);
    try {
      const venture = await createVenture({
        name,
        summary,
        offeringType,
        industry,
        scale: scale as "S" | "M" | "L",
        riskTier,
        conditions
      });
      setShowForm(false);
      setName("");
      setSummary("");
      setIndustry("");
      setConditions({});
      setItems((current) => (current ? [venture, ...current] : [venture]));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "案件を作成できませんでした。");
    } finally {
      setCreating(false);
    }
  };

  const totalApplied = (items ?? []).reduce((sum, item) => sum + item.taskApplied, 0);
  const totalUndecided = (items ?? []).reduce((sum, item) => sum + item.taskUndecided, 0);

  return (
    <>
      <PageHero
        eyebrow="事業PJ台帳"
        title="自社事業のAIプロジェクトを工程で管理する"
        lead={
          canManage || role === null ? (
            <>
              「AIシステム自社事業PJ工程管理」の標準工程を台帳にしています。案件を作ると
              {master ? `${master.taskCount}件` : "132件"}
              の工程タスクと6つのゲートが展開され、適用判定・担当・証拠・承認を記録できます。
            </>
          ) : (
            <>
              「AIシステム自社事業PJ工程管理」の標準工程を台帳にしています。要員として登録された
              案件で、担当する工程タスクの進捗・証拠を記録し、必要なスキルの充足を確認できます。
            </>
          )
        }
        theme="company"
        metrics={[
          { label: "案件数", value: items?.length ?? "—", icon: "rocket" },
          { label: "適用タスク", value: totalApplied, icon: "clipboardCheck" },
          { label: "適用判定待ち", value: totalUndecided, icon: "circleAlert" }
        ]}
        actions={
          <>
            <Link href="/ventures/standards" className="ghost-button">
              工程の標準を読む
            </Link>
            {canManage ? (
              <button type="button" className="primary-button" onClick={() => setShowForm((v) => !v)}>
                {showForm ? "入力を閉じる" : "案件を追加"}
              </button>
            ) : null}
          </>
        }
      />

      {error ? <p className={styles.error}>{error}</p> : null}

      {showForm && canManage ? (
        <Section
          title="案件を追加"
          meta="規模とRisk Tier、機能の条件を先に決めると、工程タスクの適用判定が自動で提案されます。"
          theme="company"
        >
          <form onSubmit={handleCreate}>
            <div className={styles.formGrid}>
              <label className={styles.field}>
                事業・サービス名
                <input
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  required
                  maxLength={200}
                  placeholder="例: 現場報告要約AI"
                />
              </label>
              <label className={styles.field}>
                提供形態
                <select value={offeringType} onChange={(event) => setOfferingType(event.target.value)}>
                  {OFFERING_TYPES.map((value) => (
                    <option key={value} value={value}>
                      {value}
                    </option>
                  ))}
                </select>
              </label>
              <label className={styles.field}>
                対象業界・用途
                <input
                  value={industry}
                  onChange={(event) => setIndustry(event.target.value)}
                  placeholder="例: 建設・現場管理"
                />
              </label>
              <label className={styles.field}>
                規模
                <select value={scale} onChange={(event) => setScale(event.target.value)}>
                  <option value="S">S（小規模）</option>
                  <option value="M">M（中規模）</option>
                  <option value="L">L（大規模）</option>
                </select>
              </label>
              <label className={styles.field}>
                Risk Tier
                <select value={riskTier} onChange={(event) => setRiskTier(event.target.value)}>
                  <option value="未判定">未判定</option>
                  {(master?.riskTiers ?? []).map((tier) => (
                    <option key={tier.tierId} value={tier.tierId}>
                      {tier.tierId} {tier.name}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <label className={styles.field} style={{ marginTop: 12 }}>
              概要
              <textarea
                value={summary}
                onChange={(event) => setSummary(event.target.value)}
                placeholder="誰のどの業務を、どう変えるのか"
              />
            </label>

            {master && master.conditionKeys.length > 0 ? (
              <div style={{ marginTop: 16 }}>
                <p className={styles.muted} style={{ marginBottom: 8 }}>
                  機能・条件の判定（条件付きタスクの適用提案に使います。あとから変更できます）
                </p>
                <div className={styles.conditionGrid}>
                  {master.conditionKeys.map((key) => (
                    <label key={key} className={styles.field}>
                      {key}
                      <select
                        value={conditions[key] ?? "未判定"}
                        onChange={(event) =>
                          setConditions((current) => ({
                            ...current,
                            [key]: event.target.value as VentureApplicability
                          }))
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

            <div className={styles.actionRow}>
              <button type="submit" className="primary-button" disabled={creating}>
                {creating ? "作成中…" : "この内容で作成"}
              </button>
            </div>
          </form>
        </Section>
      ) : null}

      <Section
        title={canManage ? "案件一覧" : "担当している案件"}
        meta={
          items
            ? canManage
              ? `${items.length}件`
              : `${items.length}件（要員として登録された案件のみ表示しています）`
            : undefined
        }
        theme="company"
      >
        {items === null || role === null ? (
          <SkeletonRow />
        ) : items.length === 0 ? (
          <EmptyState
            title={canManage ? "まだ案件がありません" : "担当している案件がありません"}
            message={
              canManage
                ? "「案件を追加」から、標準工程を展開した台帳を作成できます。"
                : "案件台帳にはデータの個人情報区分や要員のスキル評価が入るため、要員として登録された案件だけが表示されます。担当する案件がある場合は、事業責任者に要員への登録を依頼してください。"
            }
          />
        ) : (
          <div className={styles.cardGrid}>
            {items.map((venture) => (
              <Link key={venture.id} href={`/ventures/${venture.id}`} className={styles.card}>
                <p className={styles.cardTitle}>{venture.name}</p>
                {venture.summary ? <p className={styles.cardSummary}>{venture.summary}</p> : null}
                <div className={styles.cardMeta}>
                  <span className={`${styles.pill} ${styles.pillNeutral}`}>{venture.status}</span>
                  <span className={`${styles.pill} ${styles.pillNeutral}`}>規模 {venture.scale}</span>
                  <span className={`${styles.pill} ${styles.pillTier}`}>{venture.riskTier}</span>
                  <span className={`${styles.pill} ${styles.pillProgress}`}>
                    {venture.currentPhaseId}
                  </span>
                </div>
                <div className={styles.cardStats}>
                  <span>適用 {venture.taskApplied}</span>
                  <span>完了 {venture.taskCompleted}</span>
                  <span>判定待ち {venture.taskUndecided}</span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </Section>
    </>
  );
}
