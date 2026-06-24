"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

import type { ReviewResult, Submission } from "@newfan/contracts";

import {
  getSubmission,
  requestAiReview,
  submitMentorReview
} from "@/lib/api";

import { PageHero } from "@/app/components/ui/PageHero";
import { Section } from "@/app/components/ui/Section";
import { EmptyState } from "@/app/components/ui/EmptyState";
import { HeroSkeleton } from "@/app/components/ui/Skeleton";
import { StatusPill } from "@/app/components/ui/StatusPill";
import { ReviewPill } from "@/app/components/ui/ReviewPill";
import { AppIcon, IconText } from "@/app/components/ui/Icon";

import styles from "@/app/components/ui/ui.module.css";

type DecisionStatus = "approved" | "needs_resubmit";

const FALLBACK_RUBRIC: Array<{ label: string; score: number; max: number }> = [
  { label: "正確性", score: 0, max: 4 },
  { label: "可読性", score: 0, max: 4 },
  { label: "業務理解", score: 0, max: 4 },
  { label: "改善提案", score: 0, max: 4 }
];

function deriveRubric(review: ReviewResult | null) {
  if (!review) return FALLBACK_RUBRIC;
  const base = Math.min(4, Math.round(review.score / 25));
  const strong = Math.min(4, Math.max(0, base + 1));
  const passed = review.status.includes("pass");
  return [
    { label: "正確性", score: passed ? strong : base, max: 4 },
    { label: "可読性", score: base, max: 4 },
    { label: "業務理解", score: passed ? base : Math.max(0, base - 1), max: 4 },
    { label: "改善提案", score: base, max: 4 }
  ];
}

function statusToBadge(status: string) {
  if (status === "reviewed") return "passed" as const;
  if (status === "needs_resubmit") return "resubmit" as const;
  if (status === "approved") return "approved" as const;
  return "submitted" as const;
}

export default function MentorReviewDetailPage() {
  const params = useParams<{ submissionId: string }>();
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [review, setReview] = useState<ReviewResult | null>(null);
  const [mentorReview, setMentorReview] = useState<ReviewResult | null>(null);
  const [comments, setComments] = useState(
    "RAG評価の改善点を整理してください。指標 (MRR / Hit@K) の数値と、改善前後の比較を加えるとレビュー合格になります。"
  );
  const [reviewing, setReviewing] = useState(false);
  const [submittingMentor, setSubmittingMentor] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!params.submissionId) return;
    let active = true;
    getSubmission(params.submissionId)
      .then((value) => {
        if (!active) return;
        setSubmission(value);
        setError(null);
      })
      .catch((err: unknown) => {
        if (active) {
          setError(
            err instanceof Error
              ? err.message
              : "提出物の取得に失敗しました。mentor / admin ロールでサインインしてください。"
          );
        }
      });
    return () => {
      active = false;
    };
  }, [params.submissionId]);

  const handleAiReview = async () => {
    if (!submission) return;
    setReviewing(true);
    try {
      const result = await requestAiReview(submission.id);
      setReview(result);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "AIレビューの実行に失敗しました。");
    } finally {
      setReviewing(false);
    }
  };

  const handleMentorDecision = async (status: DecisionStatus) => {
    if (!submission) return;
    setSubmittingMentor(true);
    try {
      const result = await submitMentorReview(submission.id, { status, comments });
      setMentorReview(result);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "メンター評価の登録に失敗しました。");
    } finally {
      setSubmittingMentor(false);
    }
  };

  const rubric = useMemo(() => deriveRubric(review), [review]);

  if (error && !submission) {
    return (
      <main className={styles.page}>
        <EmptyState
          icon={<AppIcon name="circleAlert" size={24} />}
          title="提出物を読み込めません"
          message={error}
          action={
            <Link href="/auth/sign-in" className={styles.actionPrimary}>
              <IconText icon="userRound">サインインを開く</IconText>
            </Link>
          }
        />
      </main>
    );
  }

  if (!submission) {
    return (
      <main className={styles.page}>
        <HeroSkeleton />
      </main>
    );
  }

  return (
    <main className={styles.page}>
      <PageHero
        theme="mentor"
        ariaLabel="メンター詳細レビュー"
        eyebrow="メンター詳細レビュー"
        title={`提出 ${submission.id}`}
        lead={
          <>
            AIレビュー結果・ルーブリックスコア・再提出履歴を確認し、承認 / 再提出 / 要面談を判断します。
            承認するとPoC判断・部門提案に使える成果物として記録されます。
          </>
        }
        metrics={[
          {
            label: "受講者",
            value: submission.learnerId,
            hint: `演習: ${submission.exerciseId}`
          },
          {
            label: "現在の状態",
            value: <StatusPill status={statusToBadge(submission.status)} />,
            hint: review ? `AIスコア ${review.score}` : "AIレビュー未実行"
          },
          {
            label: "メンター評価",
            value: mentorReview ? mentorReview.status : "未登録",
            hint: mentorReview?.comments?.slice(0, 32) ?? "承認 / 再提出を選択"
          }
        ]}
        actions={
          <>
            <Link href="/mentor/reviews" className={styles.actionGhost}>
              <IconText icon="listFilter">キューに戻る</IconText>
            </Link>
            <button
              type="button"
              className={styles.actionPrimary}
              onClick={handleAiReview}
              disabled={reviewing}
            >
              {reviewing ? "AIレビュー実行中…" : <IconText icon="bot">AIレビューを実行</IconText>}
            </button>
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

      <div className={styles.reviewGrid}>
        <Section
          title="AIレビュー結果"
          meta="正確性 / 可読性 / 業務理解 / 改善提案の4観点 (各4点)。"
          theme="mentor"
          icon="bot"
        >
          {review ? (
            <>
              <div className={styles.rubricGrid}>
                {rubric.map((item) => (
                  <div key={item.label} className={styles.rubricItem}>
                    <p className={styles.rubricLabel}>{item.label}</p>
                    <div className={styles.rubricValue}>
                      {item.score} / {item.max}
                    </div>
                    <div className={styles.rubricBar}>
                      <div
                        className={styles.rubricBarFill}
                        style={{
                          width: `${(item.score / item.max) * 100}%`,
                          background: "linear-gradient(90deg, #14b8a6, #0d9488)"
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
              <p className={styles.evidenceRubric} style={{ marginTop: "0.85rem" }}>
                <strong>総評:</strong> {review.comments}
              </p>
              <div className={styles.actionRow}>
                <ReviewPill reviewType="ai" />
                <span className={styles.evidenceMetaLabel}>スコア {review.score}</span>
              </div>
            </>
          ) : (
            <EmptyState
              icon={<AppIcon name="circleDashed" size={24} />}
              title="AIレビュー未実行"
              message="『AIレビューを実行』を押すと、ルーブリック評価と総評が返ります。"
              action={
                <button
                  type="button"
                  className={styles.actionPrimary}
                  onClick={handleAiReview}
                  disabled={reviewing}
                >
                  <IconText icon="bot">AIレビューを実行</IconText>
                </button>
              }
            />
          )}
        </Section>

        <Section
          title="メンター判断"
          meta="承認 / 再提出 / 要面談 を選択。承認はレビュー合格成果物になります。"
          theme="mentor"
          icon="shieldCheck"
        >
          <div className={styles.field}>
            <label htmlFor="mentor-comment" className={styles.fieldLabel}>
              コメント (受講者へ)
            </label>
            <textarea
              id="mentor-comment"
              className={styles.fieldTextarea}
              value={comments}
              onChange={(e) => setComments(e.target.value)}
              rows={6}
            />
          </div>
          <div className={styles.actionRow}>
            <button
              type="button"
              className={styles.actionPrimary}
              onClick={() => handleMentorDecision("approved")}
              disabled={submittingMentor}
            >
              {submittingMentor ? "登録中…" : <IconText icon="checkCircle2">承認 (レビュー合格)</IconText>}
            </button>
            <button
              type="button"
              className={styles.actionDanger}
              onClick={() => handleMentorDecision("needs_resubmit")}
              disabled={submittingMentor}
            >
              再提出を依頼
            </button>
            <button type="button" className={styles.actionGhost} disabled>
              要面談 (準備中)
            </button>
          </div>
          {mentorReview ? (
            <div
              style={{
                marginTop: "0.7rem",
                border: "1px solid #5eead4",
                borderRadius: 16,
                padding: "0.85rem 1rem",
                background: "#ecfeff"
              }}
            >
              <strong style={{ color: "#0f766e", fontSize: 14 }}>
                登録完了: {mentorReview.status === "approved" ? "承認" : "再提出依頼"}
              </strong>
              <p
                style={{ margin: "0.35rem 0 0", fontSize: 12.5, color: "#0f172a", lineHeight: 1.6 }}
              >
                {mentorReview.comments}
              </p>
              <span className={styles.evidenceMetaLabel}>スコア {mentorReview.score}</span>
            </div>
          ) : null}
        </Section>
      </div>

      <Section
        title="提出コード"
        meta="参照のみ。修正は受講者の演習画面で行います。"
        theme="mentor"
        icon="fileCode2"
      >
        <pre className={styles.consoleOutput} style={{ fontSize: 12.5 }}>
          {submission.code || "// 提出コードはありません"}
        </pre>
      </Section>

      <Section
        title="改善履歴 / 再提出履歴"
        meta="同じ演習に対する以前の提出と AI 評価は、将来ここに時系列で表示します。"
        theme="mentor"
        icon="calendarDays"
      >
        <EmptyState
          icon={<AppIcon name="circleDashed" size={24} />}
          title="履歴は準備中"
          message="本MVPでは同一受講者・同一演習の過去提出履歴を順次対応します。"
        />
      </Section>
    </main>
  );
}
