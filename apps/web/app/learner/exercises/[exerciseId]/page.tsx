"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

import type { Exercise } from "@newfan/contracts";

import { getExercise, runExercise, submitExercise } from "@/lib/api";

import { LearnerHero } from "@/app/components/learner/LearnerHero";
import { LearnerSection } from "@/app/components/learner/Section";
import { SkillChipList } from "@/app/components/learner/SkillChip";
import { LearnerEmptyState } from "@/app/components/learner/EmptyState";

import styles from "@/app/components/ui/ui.module.css";

type RunState = "idle" | "running" | "passed" | "failed";

const HINT_LINES = [
  "業務での再利用を意識して、関数の入出力契約を明確にする。",
  "境界条件 (空配列, None, 不正な型) を 1 ケースずつテストする。",
  "AI レビューでは「再現性」と「ドキュメント分析」も評価対象になる。"
];

const RUBRIC_TAGS = ["実装", "設計", "テスト", "再現性"];

export default function LearnerExercisePage() {
  const params = useParams<{ exerciseId: string }>();
  const [exercise, setExercise] = useState<Exercise | null>(null);
  const [loading, setLoading] = useState(true);
  const [code, setCode] = useState("");
  const [runState, setRunState] = useState<RunState>("idle");
  const [runOutput, setRunOutput] = useState<string>("");
  const [runErrorOutput, setRunErrorOutput] = useState<string>("");
  const [runEngineLabel, setRunEngineLabel] = useState<string>("-");
  const [submissionId, setSubmissionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!params.exerciseId) {
      return;
    }
    let active = true;
    const load = async () => {
      try {
        const value = await getExercise(params.exerciseId);
        if (!active) return;
        setExercise(value);
        setCode(value.starterCode);
        setError(null);
      } catch (err: unknown) {
        if (!active) return;
        setError(err instanceof Error ? err.message : "演習の読み込みに失敗しました。");
      } finally {
        if (active) setLoading(false);
      }
    };
    void load();
    return () => {
      active = false;
    };
  }, [params.exerciseId]);

  const handleRun = async () => {
    if (!exercise) return;
    setRunState("running");
    setRunOutput("");
    setRunErrorOutput("");
    try {
      const result = await runExercise(exercise.id, { code });
      setRunOutput(result.stdout);
      setRunErrorOutput(result.stderr || "");
      setRunEngineLabel(`${result.engine} / ${result.pipeline}`);
      setRunState(result.status === "passed" ? "passed" : "failed");
    } catch (err) {
      setRunState("failed");
      setRunOutput(err instanceof Error ? err.message : "実行に失敗しました。");
      setRunErrorOutput("");
      setRunEngineLabel("-");
    }
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!exercise) return;
    try {
      const result = await submitExercise(exercise.id, { code });
      setSubmissionId(result.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "提出に失敗しました。");
    }
  };

  const runBadgeClass = useMemo(() => {
    if (runState === "running") return "exec-badge exec-running";
    if (runState === "passed") return "exec-badge exec-success";
    if (runState === "failed") return "exec-badge exec-error";
    return "exec-badge exec-idle";
  }, [runState]);

  const runBadgeLabel = useMemo(() => {
    if (runState === "running") return "実行中…";
    if (runState === "passed") return "実行成功";
    if (runState === "failed") return "実行失敗";
    return "未実行";
  }, [runState]);

  if (loading) {
    return (
      <main className={styles.page}>
        <div className={styles.skeletonBoxTall} />
        <div className={styles.skeletonBoxTall} />
      </main>
    );
  }

  if (!exercise) {
    return (
      <main className={styles.page}>
        <LearnerEmptyState
          icon="!"
          title="演習が見つかりません"
          message={error ?? "URL を確認するか、ホームから演習を選び直してください。"}
          action={
            <Link href="/learner/learn" className={styles.actionPrimary}>
              受講者ホームへ
            </Link>
          }
        />
      </main>
    );
  }

  return (
    <main className={styles.page}>
      <LearnerHero
        eyebrow="演習"
        title={exercise.title}
        lead={
          <>
            <strong>{exercise.prompt}</strong>
            <br />
            実行と提出を繰り返し、AI レビュー合格を目指します。失敗は減点ではなく改善履歴として証跡化されます。
          </>
        }
        metrics={[
          {
            label: "演習ID",
            value: exercise.id,
            hint: `type: ${exercise.kind}`
          },
          {
            label: "推定所要時間",
            value: "45",
            suffix: "分",
            hint: "1タスク30〜90分を基本単位"
          },
          {
            label: "実行状態",
            value: runBadgeLabel,
            hint: submissionId ? `提出ID: ${submissionId}` : `engine: ${runEngineLabel}`
          }
        ]}
        actions={
          <>
            <Link href="/learner/learn" className={styles.actionGhost}>
              受講者ホームへ戻る
            </Link>
            {submissionId ? (
              <Link href={`/learner/submissions/${submissionId}`} className={styles.actionPrimary}>
                AIレビューを確認
              </Link>
            ) : null}
          </>
        }
      />

      {error ? (
        <div className={styles.section} role="alert">
          <p className="muted" style={{ margin: 0 }}>
            操作中にエラーが発生しました: {error}
          </p>
        </div>
      ) : null}

      <form onSubmit={handleSubmit} className={styles.workspaceShell}>
        <LearnerSection
          title="課題プロンプト"
          meta="評価ルーブリックに紐づく観点を意識して実装します。"
        >
          <p
            style={{
              margin: 0,
              fontSize: 14,
              lineHeight: 1.7,
              color: "#334466"
            }}
          >
            {exercise.prompt}
          </p>
          <div className={styles.evidenceUseCase}>
            <span className={styles.evidenceUseCaseIcon} aria-hidden>
              ▸
            </span>
            <span>
              <strong>現場での使いどころ:</strong>{" "}
              業務システムのバックエンドAPIを実装する場面で同等のロジックが頻出します。
            </span>
          </div>
          <div>
            <p className={styles.evidenceMetaLabel} style={{ margin: "0 0 0.4rem" }}>
              評価観点
            </p>
            <SkillChipList skills={RUBRIC_TAGS} />
          </div>

          <p
            className={styles.evidenceRubric}
            style={{ marginTop: "0.4rem" }}
          >
            <strong>合格条件:</strong> AI レビューが <code>pass_with_comment</code> 以上を返すこと。境界条件で
            破綻しないこと。
          </p>
        </LearnerSection>

        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "1rem"
          }}
        >
          <div className={styles.workspaceEditorCard}>
            <div className={styles.workspaceEditorHeader}>
              <span className={styles.workspaceEditorTitle}>
                <span className={`${styles.editorDot} ${styles.editorDotR}`} />
                <span className={`${styles.editorDot} ${styles.editorDotY}`} />
                <span className={`${styles.editorDot} ${styles.editorDotG}`} />
                solution.py
              </span>
              <span className={runBadgeClass}>{runBadgeLabel}</span>
            </div>
            <textarea
              className={styles.editorTextarea}
              value={code}
              onChange={(event) => setCode(event.target.value)}
              spellCheck={false}
              aria-label="コードエディタ"
            />
            <div className={styles.actionRow} style={{ justifyContent: "flex-end" }}>
              <button
                type="button"
                onClick={handleRun}
                className={styles.actionGhost}
                style={{
                  background: "rgba(101, 86, 255, 0.18)",
                  color: "#e2e8f0",
                  borderColor: "rgba(101, 86, 255, 0.5)"
                }}
              >
                ▶ 実行
              </button>
              <button type="submit" className={styles.actionPrimary}>
                提出する
              </button>
            </div>
          </div>

          <div className={styles.workspaceConsoleCard}>
            <div className={styles.workspaceEditorTitle} style={{ color: "#5d667d" }}>
              実行コンソール
            </div>
            <pre
              className={`${styles.consoleOutput} ${
                runState === "failed" ? styles.consoleError : ""
              } ${runOutput ? "" : styles.consoleOutputEmpty}`}
            >
              {runOutput || "Run ボタンを押すと、ここに stdout が表示されます。"}
            </pre>
            {runErrorOutput ? (
              <pre className={`${styles.consoleOutput} ${styles.consoleError}`}>{runErrorOutput}</pre>
            ) : null}
          </div>
        </div>
      </form>

      <LearnerSection
        title="AIヒント"
        meta="現場での再利用を念頭に、最低限おさえたいポイント。"
      >
        <div className={styles.workspaceHintCard} style={{ boxShadow: "none", border: "none", padding: 0 }}>
          <span className={styles.hintHeader}>
            💡 進めるためのヒント
          </span>
          <ol className={styles.hintList}>
            {HINT_LINES.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ol>
        </div>
      </LearnerSection>
    </main>
  );
}
