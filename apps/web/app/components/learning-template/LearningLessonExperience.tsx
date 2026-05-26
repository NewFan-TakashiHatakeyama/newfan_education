import Link from "next/link";
import styles from "./LearningTemplate.module.css";

export function LearningLessonExperience({
  curriculumSlug,
  lessonSlug
}: {
  curriculumSlug: string;
  lessonSlug: string;
}) {
  return (
    <div className={styles.learningShell}>
      <section className={styles.sectionCard}>
        <div className={styles.sectionHeader}>
          <h1 className={styles.sectionTitle}>Lesson Experience</h1>
          <p className={styles.muted}>
            curriculum: {curriculumSlug} / lesson: {lessonSlug}
          </p>
        </div>
        <div className={styles.lessonLayout}>
          <aside className={styles.panel}>
            <h2 className={styles.sectionTitle}>Lesson TOC</h2>
            <ol className={styles.tocList}>
              <li>Overview and prerequisites</li>
              <li>Concept walkthrough</li>
              <li>Code example</li>
              <li>Knowledge check</li>
              <li>Exercise handoff</li>
            </ol>
          </aside>

          <section className={styles.panel}>
            <h2 className={styles.sectionTitle}>Main lesson content</h2>
            <div className={styles.contentBody}>
              <p>
                テンプレートの講座コンテンツカードに寄せて、本文表示領域を中央パネルとして再設計しました。導入、
                実装、演習への遷移を一連の流れで表示します。
              </p>
              <pre>{`def greet(name: str) -> str:
    return f"Hello {name}"

print(greet("Newfan Learner"))`}</pre>
            </div>
            <div className={styles.actionRow}>
              <Link
                href={`/learn/${curriculumSlug}/${lessonSlug}/exercise`}
                className={styles.actionButton}
              >
                Start exercise
              </Link>
              <Link href="/learn" className={`${styles.actionButton} ${styles.actionSecondary}`}>
                Back to courses
              </Link>
            </div>
          </section>

          <aside className={styles.panel}>
            <h2 className={styles.sectionTitle}>AI Guide</h2>
            <ul className={styles.tocList}>
              <li>質問: 型ヒントの目的は？</li>
              <li>ヒント: 契約と保守性の向上</li>
              <li>演習前チェック: 返り値型の明示</li>
              <li>根拠: lesson-section-2</li>
            </ul>
          </aside>
        </div>
      </section>
    </div>
  );
}

