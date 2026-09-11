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
import { Feedback } from "@/app/components/ui/Feedback";
import { Drawer } from "@/app/components/ui/Drawer";
import { SkillChip, SkillChipList } from "@/app/components/ui/SkillChip";
import { SkeletonRow } from "@/app/components/ui/Skeleton";
import { AppIcon, IconText } from "@/app/components/ui/Icon";

import styles from "@/app/components/ui/ui.module.css";

const STARTER_TEMPLATE = {
  title: "問い合わせ回答支援AI（カスタマーサポート）",
  description:
    "カスタマーサポートの製品問い合わせ一次回答を短縮するため、FAQ・操作マニュアル・過去履歴を根拠にした回答ドラフト生成（RAG）のPoCを企画する業務課題。個人情報・補償判断は対象外とし、担当者の最終確認を必須とする。",
  requiredSkills: "RAG, 業務課題定義, 検索評価",
  optionalSkills: "LangChain, Bedrock, OpenSearch, プロンプト設計",
  expectedTasks: "一次回答フロー整理、FAQ棚卸し、PoC計画書、評価指標設計",
  engagementLevel: "担当",
  salesNote:
    "月間約1,200件のうちFAQ完結可能な問い合わせを対象。DX推進・情シスと連携し、2か月PoCの着手候補として整理中。"
};

export default function CompanyRequirementsPage() {
  const [items, setItems] = useState<Requirement[] | null>(null);
  const [learners, setLearners] = useState<LearnerSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [requiredSkills, setRequiredSkills] = useState("");

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
      refresh(); setShowCreate(false); setTitle(""); setDescription(""); setRequiredSkills("");
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
      setError(err instanceof Error ? err.message : "スキル適合度の評価に失敗しました。");
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
        title="業務課題"
        lead="業務課題と必要なスキルを登録します。"
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
            hint: "スキル適合度の評価対象"
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
            <button className="primary-button" onClick={() => { setError(null); setShowCreate(true); }}>業務課題を登録</button>
            <Link href="/company/reports" className={styles.actionPrimary}>
              <IconText icon="barChart3">プロジェクト提案を生成</IconText>
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

      <Drawer open={showCreate} title="業務課題を登録" onClose={() => { setShowCreate(false); setTitle(""); setDescription(""); setRequiredSkills(""); }} busy={submitting} dirty={!!title || !!description || !!requiredSkills}>
        <Feedback message={error} error />
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

          </div>

          <div className="dialog-actions">
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
              }}
            >
              入力例を使う
            </button>
          </div>
        </form>
      </Drawer>

      <Section
        title={`登録済み業務課題 (${items?.length ?? 0} 件)`}
        meta="『スキルの一致を確認』から、受講者とのマッチング結果を確認できます。"
        theme="company"
        icon="notebookText"
      >
        {isLoading ? (
          <SkeletonRow widths={["70%", "55%", "65%"]} />
        ) : (items ?? []).length === 0 ? (
          <EmptyState
            icon={<AppIcon name="circleDashed" size={24} />}
            title="業務課題がまだ登録されていません"
            message="「業務課題を登録」から始めてください。"
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
                    <IconText icon="scanSearch">スキルの一致を確認</IconText>
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </Section>

      <Drawer
        open={drawerRequirement !== null}
        title={drawerRequirement ? `スキル適合度: ${drawerRequirement.title}` : ""}
        onClose={() => setDrawerRequirement(null)}
        busy={assessing}
      >
        {drawerRequirement ? (
          <>
            <Feedback message={error} error />
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
                    <IconText icon="barChart3">プロジェクト提案を生成</IconText>
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
                  {assessing ? "評価中…" : <IconText icon="scanSearch">スキルの一致を確認する</IconText>}
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
