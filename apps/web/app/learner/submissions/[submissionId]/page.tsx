"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

import type { ReviewResult, Submission } from "@newfan/contracts";

import { getSubmission, requestAiReview } from "@/lib/api";

import { LearnerHero } from "@/app/components/learner/LearnerHero";
import { LearnerSection } from "@/app/components/learner/Section";
import { LearnerEmptyState } from "@/app/components/learner/EmptyState";
import { StatusPill } from "@/app/components/learner/StatusPill";
import { ReviewPill } from "@/app/components/learner/ReviewPill";

import styles from "@/app/components/ui/ui.module.css";

const FALLBACK_RUBRIC: Array<{ label: string; score: number; max: number }> = [
  { label: "実装", score: 0, max: 4 },
  { label: "設計", score: 0, max: 4 },
  { label: "テスト", score: 0, max: 4 },
  { label: "再現性", score: 0, max: 4 }
];

const STRENGTH_HINTS = [
  "業務要件の入出力契約を明確にして実装している点。",
  "境界条件と例外ケースを最低1ケース以上カバーしている点。"
];

const IMPROVEMENT_HINTS = [
  "テスト分割と命名で意図がより伝わる余地あり。",
  "ドキュメント (docstring) を追加すると現場転用しやすい。"
];

function deriveRubric(review: ReviewResult | null) {
  if (!review) return FALLBACK_RUBRIC;
  const base = Math.min(4, Math.round(review.score / 25));
  const strong = Math.min(4, Math.max(0, base + 1));
  const passed = review.status.includes("pass");
  return [
    { label: "実装", score: passed ? strong : base, max: 4 },
    { label: "設計", score: base, max: 4 },
    { label: "テスト", score: passed ? base : Math.max(0, base - 1), max: 4 },
    { label: "再現性", score: base, max: 4 }
  ];
}

function statusToBadge(submissionStatus: string) {
  if (submissionStatus === "reviewed") return "passed" as const;
  if (submissionStatus === "needs_resubmit") return "resubmit" as const;
  return "submitted" as const;
}

export default function LearnerSubmissionPage() {
  const params = useParams<{ submissionId: string }>();
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [review, setReview] = useState<ReviewResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reviewing, setReviewing] = useState(false);

  useEffect(() => {
    if (!params.submissionId) return;
    let active = true;
    getSubmission(params.submissionId)
      .then((value) => {
        if (active) {
          setSubmission(value);
          setError(null);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setError(err instanceof Error ? err.message : "提出内容の取得に失敗しました。");
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

  if (!submission && !error) {
    return (
      <main className={styles.page}>
        <div className={styles.skeletonBoxTall} />
      </main>
    );
  }

  if (!submission) {
    return (
      <main className={styles.page}>
        <LearnerEmptyState
          icon="!"
          title="提出が見つかりません"
          message={error ?? "URLを確認するか、ホームから戻ってください。"}
          action={
            <Link href="/learner/learn" className={styles.actionPrimary}>
              受講者ホームへ
            </Link>
          }
        />
      </main>
    );
  }

  const rubric = deriveRubric(review);
  const submissionBadge = statusToBadge(submission.status);

  return (
    <main className={styles.page}>
      <LearnerHero
        eyebrow="レビュー結果"
        title={`提出 ${submission.id}`}
        lead={
          <>
            AI レビュー → メンター承認の二段階で品質を担保します。失敗は減点ではなく改善履歴として
            成果物化されるため、再提出で大きく前進できます。
          </>
        }
        metrics={[
          {
            label: "提出ID",
            value: submission.id,
            hint: submission.exerciseId
          },
          {
            label: "現在の状態",
            value: <StatusPill status={submissionBadge} />,
            hint: review
              ? `AI スコア: ${review.score}`
              : "AI レビューを実行して品質を確認します"
          },
          {
            label: "レビュー種別",
            value: <ReviewPill reviewType={review ? (review.reviewerType === "ai" ? "ai" : "mentor") : null} />,
            hint: review?.status ?? "未実行"
          }
        ]}
        actions={
          <>
            <button
              type="button"
              className={styles.actionPrimary}
              onClick={handleAiReview}
              disabled={reviewing}
            >
              {reviewing ? "AIレビュー実行中…" : "AIレビューを実行"}
            </button>
            <Link href="/learner/evidence" className={styles.actionGhost}>
              自分の成果物を見る
            </Link>
          </>
        }
      />

      {error ? (
        <div className={styles.section} role="alert">
          <p className="muted" style={{ margin: 0 }}>{error}</p>
        </div>
      ) : null}

      <div className={styles.reviewGrid}>
        <LearnerSection
          title="AIレビュー結果"
          meta="評価ルーブリックは観点別に 4 段階で表示します。"
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
                        style={{ width: `${(item.score / item.max) * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
              <p className={styles.evidenceRubric} style={{ marginTop: "0.85rem" }}>
                <strong>総評:</strong> {review.comments}
              </p>
              <div className={styles.actionRow}>
                <Link
                  href={`/learner/exercises/${submission.exerciseId}`}
                  className={styles.actionGhost}
                >
                  演習に戻る / 再提出
                </Link>
              </div>
            </>
          ) : (
            <LearnerEmptyState
              icon="◌"
              title="AIレビュー未実行"
              message="「AIレビューを実行」を押すと、ルーブリックに沿った評価とコメントが返ります。"
              action={
                <button
                  type="button"
                  className={styles.actionPrimary}
                  onClick={handleAiReview}
                  disabled={reviewing}
                >
                  AIレビューを実行
                </button>
              }
            />
          )}
        </LearnerSection>

        <LearnerSection title="メンター評価フック" meta="AI評価の上位レビューとして、メンター承認が成果物化のキーになります。">
          <div style={{ display: "grid", gap: "0.7rem" }}>
            <div>
              <p className={styles.evidenceMetaLabel} style={{ margin: "0 0 0.35rem" }}>
                強み (AI抽出)
              </p>
              <ul className={styles.hintList}>
                {STRENGTH_HINTS.map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
            </div>
            <div>
              <p className={styles.evidenceMetaLabel} style={{ margin: "0 0 0.35rem" }}>
                改善余地
              </p>
              <ul className={styles.hintList}>
                {IMPROVEMENT_HINTS.map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
            </div>
            <p className="muted" style={{ margin: 0, fontSize: 12 }}>
              メンター承認は <strong>/mentor/reviews</strong> から行われ、承認後に経営・部門提案に使える
              成果物として記録されます。
            </p>
          </div>
        </LearnerSection>
      </div>

      <LearnerSection
        title="提出コード"
        meta="参照のみ。修正は演習画面から行います。"
      >
        <pre className={styles.consoleOutput} style={{ fontSize: 12.5 }}>
          {submission.code || "// 提出コードはありません"}
        </pre>
      </LearnerSection>
    </main>
  );
}
