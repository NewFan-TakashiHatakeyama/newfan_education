"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import Link from "next/link";

import type {
  FitAssessment,
  LearnerSummary,
  Requirement
} from "@newfan/contracts";

import {
  assessRequirement,
  createRequirement,
  getLearners,
  getRequirements
} from "@/lib/api";

import { PageHero } from "@/app/components/ui/PageHero";
import { Section } from "@/app/components/ui/Section";
import { EmptyState } from "@/app/components/ui/EmptyState";
import { Drawer } from "@/app/components/ui/Drawer";
import { SkillChip, SkillChipList } from "@/app/components/ui/SkillChip";
import { SkeletonRow } from "@/app/components/ui/Skeleton";
import { AppIcon, IconText } from "@/app/components/ui/Icon";

import styles from "@/app/components/ui/ui.module.css";

const STARTER_TEMPLATE = {
  title: "社内FAQ RAG検証",
  description: "カスタマーサポート部門の問い合わせ対応を改善するため、社内FAQ文書を対象にRAG検証を行う業務課題。",
  requiredSkills: "Python, RAG, 検索評価",
  optionalSkills: "LangChain, Bedrock, OpenSearch",
  expectedTasks: "文書棚卸し、検索評価、改善レポート作成",
  engagementLevel: "担当",
  salesNote: "Bedrock環境を利用予定。DX推進チームと情シスが連携し、PoC着手候補として整理中。"
};

export default function CompanyRequirementsPage() {
  const [items, setItems] = useState<Requirement[] | null>(null);
  const [learners, setLearners] = useState<LearnerSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [title, setTitle] = useState(STARTER_TEMPLATE.title);
  const [description, setDescription] = useState(STARTER_TEMPLATE.description);
  const [requiredSkills, setRequiredSkills] = useState(STARTER_TEMPLATE.requiredSkills);
  const [optionalSkills, setOptionalSkills] = useState(STARTER_TEMPLATE.optionalSkills);
  const [expectedTasks, setExpectedTasks] = useState(STARTER_TEMPLATE.expectedTasks);
  const [engagementLevel, setEngagementLevel] = useState(STARTER_TEMPLATE.engagementLevel);
  const [salesNote, setSalesNote] = useState(STARTER_TEMPLATE.salesNote);

  const [drawerRequirement, setDrawerRequirement] = useState<Requirement | null>(null);
  const [assessment, setAssessment] = useState<FitAssessment | null>(null);
  const [assessing, setAssessing] = useState(false);

  const refresh = () => {
    getRequirements()
      .then((res) => setItems(res.items))
      .catch((err: unknown) => {
        setItems([]);
        setError(
          err instanceof Error
            ? err.message
            : "登録済み業務課題の取得に失敗しました。必要な権限を持つアカウントでサインインして、再読み込みしてください。"
        );
      });
  };

  useEffect(() => {
    refresh();
    getLearners()
      .then((res) => setLearners(res.items))
      .catch(() => setLearners([]));
  }, []);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await createRequirement({
        title,
        description,
        requiredSkills: requiredSkills
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean)
      });
      refresh();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "業務課題の登録に失敗しました。必要な権限を持つアカウントでサインインしてください。"
      );
    } finally {
      setSubmitting(false);
    }
  };

  const openDrawer = (req: Requirement) => {
    setDrawerRequirement(req);
    setAssessment(null);
  };

  const handleAssess = async () => {
    if (!drawerRequirement) return;
    setAssessing(true);
    setAssessment(null);
    try {
      const result = await assessRequirement(drawerRequirement.id);
      setAssessment(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "AIテーマ適合度の評価に失敗しました。");
    } finally {
      setAssessing(false);
    }
  };

  const learnerNameById = useMemo(() => {
    const map = new Map<string, string>();
    learners.forEach((l) => map.set(l.id, l.name));
    return map;
  }, [learners]);

  const isLoading = items === null;

  return (
    <main className={styles.page}>
      <PageHero
        theme="company"
        ariaLabel="業務課題管理"
        eyebrow="業務課題"
        title="社内の業務課題を登録し、AIテーマ化と育成計画に活かす"
        lead={
          <>
            部門ごとの業務課題・必須/歓迎スキル・業務内容を登録し、受講者とのAIテーマ適合度を即時評価します。
            一致スキル・不足スキル・推奨受講者を把握し、育成計画の逆算とAIプロジェクト候補の選定につなげます。
          </>
        }
        metrics={[
          {
            label: "登録済み業務課題",
            value: items?.length ?? 0,
            suffix: "件",
            hint: "社内業務課題の登録数"
          },
          {
            label: "受講者",
            value: learners.length,
            suffix: "名",
            hint: "AIテーマ適合度の評価対象"
          },
          {
            label: "PoC推進候補",
            value: learners.filter((l) => l.readiness === "Ready" || l.readiness === "Almost").length,
            suffix: "名",
            hint: "PoC着手可 / メンター伴走"
          }
        ]}
        actions={
          <>
            <Link href="/company/reports" className={styles.actionPrimary}>
              <IconText icon="barChart3">AIプロジェクト候補を生成</IconText>
            </Link>
            <Link href="/company/fit-assessments" className={styles.actionGhost}>
              <IconText icon="scanSearch">診断履歴を表示</IconText>
            </Link>
            <Link href="/company/learners" className={styles.actionGhost}>
              <IconText icon="users">受講者一覧へ</IconText>
            </Link>
          </>
        }
      />

      {error ? (
        <div className={styles.section} role="alert">
          <p className="muted" style={{ margin: 0 }}>
            {error}
          </p>
        </div>
      ) : null}

      <Section
        title="業務課題を登録"
        meta="必須/歓迎スキル・業務内容・担当レベルを入力。部門メモはチーム内の整理用として利用できます。"
        theme="company"
        icon="clipboardList"
      >
        <form onSubmit={handleSubmit} className={styles.formGrid}>
          <div className={styles.formGridTwo}>
            <div className={styles.field}>
              <label htmlFor="req-title" className={styles.fieldLabel}>
                課題名
              </label>
              <input
                id="req-title"
                className={styles.fieldInput}
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
              />
            </div>
            <div className={styles.field}>
              <label htmlFor="req-level" className={styles.fieldLabel}>
                担当レベル（補助 / 担当 / リード）
              </label>
              <select
                id="req-level"
                className={styles.fieldSelect}
                value={engagementLevel}
                onChange={(e) => setEngagementLevel(e.target.value)}
              >
                <option value="補助">補助</option>
                <option value="担当">担当</option>
                <option value="リード">リード</option>
              </select>
            </div>
          </div>
          <div className={styles.field}>
            <label htmlFor="req-desc" className={styles.fieldLabel}>
              業務内容
            </label>
            <textarea
              id="req-desc"
              className={styles.fieldTextarea}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
            />
          </div>
          <div className={styles.formGridTwo}>
            <div className={styles.field}>
              <label htmlFor="req-required" className={styles.fieldLabel}>
                必須スキル (カンマ区切り)
              </label>
              <input
                id="req-required"
                className={styles.fieldInput}
                value={requiredSkills}
                onChange={(e) => setRequiredSkills(e.target.value)}
              />
            </div>
            <div className={styles.field}>
              <label htmlFor="req-optional" className={styles.fieldLabel}>
                歓迎スキル (カンマ区切り)
              </label>
              <input
                id="req-optional"
                className={styles.fieldInput}
                value={optionalSkills}
                onChange={(e) => setOptionalSkills(e.target.value)}
              />
            </div>
          </div>
          <div className={styles.formGridTwo}>
            <div className={styles.field}>
              <label htmlFor="req-tasks" className={styles.fieldLabel}>
                想定タスク / 担当事項
              </label>
              <input
                id="req-tasks"
                className={styles.fieldInput}
                value={expectedTasks}
                onChange={(e) => setExpectedTasks(e.target.value)}
              />
            </div>
            <div className={styles.field}>
              <label htmlFor="req-sales" className={styles.fieldLabel}>
                部門メモ（背景・優先度・連携先）
              </label>
              <input
                id="req-sales"
                className={styles.fieldInput}
                value={salesNote}
                onChange={(e) => setSalesNote(e.target.value)}
              />
            </div>
          </div>
          <div className={styles.actionRow}>
            <button type="submit" className={styles.actionPrimary} disabled={submitting}>
              {submitting ? "登録中…" : <IconText icon="send">業務課題を登録する</IconText>}
            </button>
            <button
              type="button"
              className={styles.actionGhost}
              onClick={() => {
                setTitle(STARTER_TEMPLATE.title);
                setDescription(STARTER_TEMPLATE.description);
                setRequiredSkills(STARTER_TEMPLATE.requiredSkills);
                setOptionalSkills(STARTER_TEMPLATE.optionalSkills);
                setExpectedTasks(STARTER_TEMPLATE.expectedTasks);
                setEngagementLevel(STARTER_TEMPLATE.engagementLevel);
                setSalesNote(STARTER_TEMPLATE.salesNote);
              }}
            >
              サンプル入力に戻す
            </button>
          </div>
        </form>
      </Section>

      <Section
        title={`登録済み業務課題 (${items?.length ?? 0} 件)`}
        meta="『AIテーマ適合度を評価』から、受講者とのマッチング結果を確認できます。"
        theme="company"
        icon="notebookText"
      >
        {isLoading ? (
          <SkeletonRow widths={["70%", "55%", "65%"]} />
        ) : (items ?? []).length === 0 ? (
          <EmptyState
            icon={<AppIcon name="circleDashed" size={24} />}
            title="業務課題がまだ登録されていません"
            message="上のフォームから業務課題を登録すると、AIテーマ適合度評価とAIプロジェクト候補の準備ができます。"
          />
        ) : (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
              gap: "0.95rem"
            }}
          >
            {(items ?? []).map((req) => (
              <article
                key={req.id}
                style={{
                  border: "1px solid var(--border)",
                  borderRadius: 20,
                  background: "linear-gradient(180deg, #ffffff, #f8f9ff)",
                  padding: "1rem 1.15rem",
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.55rem",
                  boxShadow: "0 12px 28px -22px rgba(79, 70, 229, 0.3)"
                }}
              >
                <strong style={{ fontSize: 15, color: "#0f172a" }}>{req.title}</strong>
                <p style={{ margin: 0, fontSize: 12.5, color: "#475569", lineHeight: 1.65 }}>
                  {req.description}
                </p>
                <SkillChipList skills={req.requiredSkills} />
                <div className={styles.actionRow}>
                  <button
                    type="button"
                    className={styles.actionPrimary}
                    onClick={() => openDrawer(req)}
                    style={{ fontSize: 12 }}
                  >
                    <IconText icon="scanSearch">AIテーマ適合度を評価</IconText>
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </Section>

      <Drawer
        open={drawerRequirement !== null}
        title={drawerRequirement ? `AIテーマ適合度: ${drawerRequirement.title}` : ""}
        onClose={() => setDrawerRequirement(null)}
      >
        {drawerRequirement ? (
          <>
            <div className={styles.field}>
              <p className={styles.fieldLabel}>業務内容</p>
              <p style={{ margin: 0, fontSize: 13, color: "#334466", lineHeight: 1.6 }}>
                {drawerRequirement.description}
              </p>
            </div>
            <div className={styles.field}>
              <p className={styles.fieldLabel}>必須スキル</p>
              <SkillChipList skills={drawerRequirement.requiredSkills} />
            </div>

            {assessment ? (
              <div style={{ display: "grid", gap: "0.7rem" }}>
                <div className={`${styles.kpiTile} ${styles.kpiTileAccent}`}>
                  <p className={styles.kpiLabel}>AIテーマ適合スコア</p>
                  <p className={styles.kpiValue}>
                    {assessment.fitScore}
                    <span className={styles.kpiValueSuffix}>/ 100</span>
                  </p>
                  <p className={styles.kpiHint}>
                    推奨受講者: {learnerNameById.get(assessment.recommendedLearnerId) ?? assessment.recommendedLearnerId}
                  </p>
                </div>
                <div className={styles.field}>
                  <p className={styles.fieldLabel}>一致スキル</p>
                  {assessment.matchedSkills.length === 0 ? (
                    <p className="muted" style={{ margin: 0, fontSize: 12 }}>
                      —
                    </p>
                  ) : (
                    <SkillChipList skills={assessment.matchedSkills} tone="strong" />
                  )}
                </div>
                <div className={styles.field}>
                  <p className={styles.fieldLabel}>不足スキル / 追加育成項目</p>
                  {assessment.gapSkills.length === 0 ? (
                    <p className="muted" style={{ margin: 0, fontSize: 12 }}>
                      —
                    </p>
                  ) : (
                    <SkillChipList skills={assessment.gapSkills} tone="gap" />
                  )}
                </div>
                <div className={styles.actionRow}>
                  <Link
                    href="/company/reports"
                    className={styles.actionPrimary}
                    style={{ fontSize: 12 }}
                  >
                    <IconText icon="barChart3">AIプロジェクト候補を生成</IconText>
                  </Link>
                  <button
                    type="button"
                    className={styles.actionGhost}
                    onClick={handleAssess}
                    disabled={assessing}
                  >
                    再評価
                  </button>
                </div>
              </div>
            ) : (
              <div className={styles.actionRow}>
                <button
                  type="button"
                  className={styles.actionPrimary}
                  onClick={handleAssess}
                  disabled={assessing}
                >
                  {assessing ? "評価中…" : <IconText icon="scanSearch">AIテーマ適合度を評価する</IconText>}
                </button>
              </div>
            )}

            <div style={{ marginTop: "0.5rem" }}>
              <SkillChip label={`業務課題ID: ${drawerRequirement.id}`} />
            </div>
          </>
        ) : null}
      </Drawer>
    </main>
  );
}
