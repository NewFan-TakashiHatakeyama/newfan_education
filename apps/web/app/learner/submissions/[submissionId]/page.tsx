"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

import type { Submission } from "@newfan/contracts";

import { getSubmission } from "@/lib/api";

import { Disclosure } from "@/app/components/ui/Disclosure";
import { LearnerHero } from "@/app/components/learner/LearnerHero";
import { LearnerSection } from "@/app/components/learner/Section";
import { LearnerEmptyState } from "@/app/components/learner/EmptyState";
import { StatusPill } from "@/app/components/learner/StatusPill";

import styles from "@/app/components/ui/ui.module.css";

function statusToBadge(submissionStatus: string) {
  if (submissionStatus === "reviewed") return "passed" as const;
  if (submissionStatus === "needs_resubmit") return "resubmit" as const;
  return "submitted" as const;
}

export default function LearnerSubmissionPage() {
  const params = useParams<{ submissionId: string }>();
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [error, setError] = useState<string | null>(null);

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

  const submissionBadge = statusToBadge(submission.status);

  return (
    <main className={styles.page}>
      <LearnerHero
        eyebrow="レビュー結果"
        title={`提出 ${submission.id}`}
        lead="提出内容とメンターの評価を確認できます。"
        metrics={[
          {
            label: "提出ID",
            value: submission.id,
            hint: submission.exerciseId
          },
          {
            label: "現在の状態",
            value: <StatusPill status={submissionBadge} />,
          }
        ]}
        actions={
          <>

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

      <LearnerSection title="レビュー状況">
        <p>提出状態：{submission.status === "reviewed" ? "レビュー済み" : submission.status === "needs_resubmit" ? "再提出が必要です" : "確認待ち"}</p>
        <Link href="/learner/evidence">成果物・評価を確認</Link>
        <Disclosure title="評価について"><p>AI採点は現在未提供です。評価はメンターが行います。</p></Disclosure>
      </LearnerSection>

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
