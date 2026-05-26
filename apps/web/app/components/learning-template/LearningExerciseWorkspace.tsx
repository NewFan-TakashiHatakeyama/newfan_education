"use client";

import { useMemo, useRef, useState } from "react";
import Link from "next/link";
import styles from "./LearningTemplate.module.css";

const INITIAL_CODE = `def solve(a: int, b: int) -> int:
    return a + b

print(solve(2, 3))
`;

type RunStatus = "idle" | "running" | "success" | "error";

export function LearningExerciseWorkspace({
  curriculumSlug,
  lessonSlug
}: {
  curriculumSlug: string;
  lessonSlug: string;
}) {
  const [code, setCode] = useState(INITIAL_CODE);
  const [status, setStatus] = useState<RunStatus>("idle");
  const [stdout, setStdout] = useState("");
  const [stderr, setStderr] = useState("");
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const statusLabel = useMemo(() => {
    if (status === "running") {
      return "Running";
    }
    if (status === "success") {
      return "Passed";
    }
    if (status === "error") {
      return "Needs fix";
    }
    return "Ready";
  }, [status]);

  function clearTimer() {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }

  function runCode() {
    clearTimer();
    setStatus("running");
    setStdout("");
    setStderr("");
    timerRef.current = setTimeout(() => {
      if (code.includes("raise") || code.includes("/ 0")) {
        setStatus("error");
        setStderr("Traceback: ZeroDivisionError (simulated)");
        return;
      }
      setStatus("success");
      setStdout("5\n");
    }, 900);
  }

  function resetCode() {
    clearTimer();
    setCode(INITIAL_CODE);
    setStatus("idle");
    setStdout("");
    setStderr("");
  }

  return (
    <div className={styles.learningShell}>
      <section className={styles.sectionCard}>
        <div className={styles.statusRow}>
          <h1 className={styles.sectionTitle}>Exercise Workspace</h1>
          <span className={styles.statusBadge}>{statusLabel}</span>
        </div>
        <p className={styles.muted}>
          curriculum: {curriculumSlug} / lesson: {lessonSlug}
        </p>
      </section>

      <section className={styles.sectionCard}>
        <div className={styles.exerciseLayout}>
          <article className={styles.panel}>
            <h2 className={styles.sectionTitle}>Problem statement</h2>
            <ul className={styles.tocList}>
              <li>2つの整数を受け取り、和を返す `solve(a, b)` を実装</li>
              <li>入力例: `2, 3` / 出力例: `5`</li>
              <li>評価: 正しい返り値と関数定義の有無</li>
            </ul>
            <div className={styles.actionRow}>
              <Link
                href={`/learn/${curriculumSlug}/${lessonSlug}`}
                className={`${styles.actionButton} ${styles.actionSecondary}`}
              >
                Back to lesson
              </Link>
            </div>
          </article>

          <article className={styles.panel}>
            <h2 className={styles.sectionTitle}>Code editor</h2>
            <textarea
              value={code}
              onChange={(event) => setCode(event.target.value)}
              className={styles.searchInput}
              style={{ borderRadius: 12, minHeight: 240, fontFamily: "Consolas, monospace" }}
              spellCheck={false}
            />
            <div className={styles.actionRow}>
              <button
                type="button"
                className={styles.actionButton}
                onClick={runCode}
                disabled={status === "running"}
              >
                Run
              </button>
              <button
                type="button"
                className={`${styles.actionButton} ${styles.actionSecondary}`}
                onClick={resetCode}
              >
                Reset
              </button>
            </div>
          </article>
        </div>
      </section>

      <section className={styles.sectionCard}>
        <h2 className={styles.sectionTitle}>Console</h2>
        <div className={styles.exerciseConsole}>
          {stdout ? <p>{stdout}</p> : null}
          {stderr ? <p>{stderr}</p> : null}
          {!stdout && !stderr ? <p>Run the code to view output.</p> : null}
        </div>
      </section>
    </div>
  );
}

