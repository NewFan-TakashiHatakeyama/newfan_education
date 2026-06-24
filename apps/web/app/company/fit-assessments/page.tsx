"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";

import type {
  FitAssessmentListItem,
  LearnerSummary,
  Requirement
} from "@newfan/contracts";

import { getLearners, getRequirements, listFitAssessments } from "@/lib/api";

import { PageHero } from "@/app/components/ui/PageHero";
import { Section } from "@/app/components/ui/Section";
import { EmptyState } from "@/app/components/ui/EmptyState";
import { SkeletonRow } from "@/app/components/ui/Skeleton";
import { SkillChipList } from "@/app/components/ui/SkillChip";
import { AppIcon, IconText } from "@/app/components/ui/Icon";

import styles from "@/app/components/ui/ui.module.css";

export default function FitAssessmentsPage() {
  const [items, setItems] = useState<FitAssessmentListItem[] | null>(null);
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [learners, setLearners] = useState<LearnerSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    Promise.allSettled([listFitAssessments(), getRequirements(), getLearners()]).then((results) => {
      if (!active) return;
      const [assessments, reqs, learnerRes] = results;
      if (assessments.status === "fulfilled") setItems(assessments.value.items);
      else {
        setItems([]);
        setError(
          assessments.reason instanceof Error
            ? assessments.reason.message
            : "AIテーマ診断履歴の取得に失敗しました。"
        );
      }
      if (reqs.status === "fulfilled") setRequirements(reqs.value.items);
      if (learnerRes.status === "fulfilled") setLearners(learnerRes.value.items);
    });
    return () => {
      active = false;
    };
  }, []);

  const requirementTitleById = useMemo(() => {
    const map = new Map<string, string>();
    requirements.forEach((r) => map.set(r.id, r.title));
    return map;
  }, [requirements]);

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
        ariaLabel="AIテーマ診断履歴"
        eyebrow="AIテーマ診断"
        title="業務課題に対するAIテーマ適合度の評価履歴"
        lead={
          <>
            登録済み業務課題と受講者のスキル・成果物をもとに、AI活用テーマへの適合度を記録します。
            推奨受講者と不足スキルを確認し、育成計画とAIプロジェクト候補の選定に活用できます。
          </>
        }
        metrics={[
          { label: "診断履歴", value: items?.length ?? 0, suffix: "件", hint: "本画面で表示される評価" },
          {
            label: "登録業務課題",
            value: requirements.length,
            suffix: "件",
            hint: "診断対象の業務課題"
          },
          {
            label: "受講者",
            value: learners.length,
            suffix: "名",
            hint: "推奨候補の参照対象"
          }
        ]}
        actions={
          <>
            <Link href="/company/requirements" className={styles.actionPrimary}>
              <IconText icon="clipboardList">業務課題を登録</IconText>
            </Link>
            <Link href="/company/reports" className={styles.actionGhost}>
              <IconText icon="barChart3">AIプロジェクト候補を生成</IconText>
            </Link>
          </>
        }
      />

      {error ? (
        <div className={styles.section} role="alert">
          <p className="muted" style={{ margin: 0 }}>{error}</p>
        </div>
      ) : null}

      <Section
        title={`診断履歴 (${items?.length ?? 0} 件)`}
        meta="業務課題ごとの適合スコア、一致スキル、不足スキル、推奨受講者を確認できます。"
        theme="company"
        icon="scanSearch"
      >
        {isLoading ? (
          <SkeletonRow widths={["70%", "55%", "60%"]} />
        ) : (items ?? []).length === 0 ? (
          <EmptyState
            icon={<AppIcon name="circleDashed" size={24} />}
            title="診断履歴はまだありません"
            message="業務課題画面から『AIテーマ適合度を評価』を実行すると、ここに履歴が表示されます。"
            action={
              <Link href="/company/requirements" className={styles.actionPrimary}>
                <IconText icon="clipboardList">業務課題画面へ</IconText>
              </Link>
            }
          />
        ) : (
          <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gap: "0.75rem" }}>
            {(items ?? []).map((item) => (
              <li
                key={item.id}
                style={{
                  border: "1px solid var(--border)",
                  borderRadius: 16,
                  padding: "1rem 1.1rem",
                  background: "var(--surface)",
                  display: "grid",
                  gap: "0.45rem"
                }}
              >
                <strong style={{ fontSize: 14 }}>
                  {requirementTitleById.get(item.requirementId) ?? item.requirementId}
                </strong>
                <p className="muted" style={{ margin: 0, fontSize: 13 }}>
                  適合スコア: {item.fitScore} / 100 · 推奨受講者:{" "}
                  {learnerNameById.get(item.recommendedLearnerId) ?? item.recommendedLearnerId}
                </p>
                <p className="muted" style={{ margin: 0, fontSize: 12 }}>
                  一致スキル: {item.matchedSkills.join(", ") || "—"}
                </p>
                <p className="muted" style={{ margin: 0, fontSize: 12 }}>
                  不足スキル: {item.gapSkills.join(", ") || "なし"}
                </p>
              </li>
            ))}
          </ul>
        )}
      </Section>
    </main>
  );
}
