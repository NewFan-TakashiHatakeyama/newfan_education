"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

import type { Roadmap } from "@newfan/contracts";

import { getRoadmap } from "@/lib/api";

import { LearnerHero } from "@/app/components/learner/LearnerHero";
import { LearnerSection } from "@/app/components/learner/Section";
import { SkillChipList } from "@/app/components/learner/SkillChip";

import styles from "@/app/components/ui/ui.module.css";

type TimelineEntry = {
  id: string;
  phase: string;
  title: string;
  summary: string;
  estimatedMinutes: number;
  status: "done" | "current" | "pending";
  skillTags: string[];
};

const FALLBACK_TIMELINE: TimelineEntry[] = [
  {
    id: "stage-foundation",
    phase: "Phase 1 · 基礎",
    title: "AI/DX全体像と業務活用パターン",
    summary:
      "生成AI、RAG、AI-OCR、エージェント等の全体像を理解。教材完了で要改善レベルの成果物を確保。",
    estimatedMinutes: 180,
    status: "done",
    skillTags: ["AI基礎", "業務課題", "ガバナンス"]
  },
  {
    id: "stage-issue",
    phase: "Phase 2 · 業務課題",
    title: "業務課題定義とAIテーマ化",
    summary:
      "As-Is/To-Be、KPI、制約を整理。AI レビュー合格で PoC判断向け成果物が生成されます。",
    estimatedMinutes: 240,
    status: "current",
    skillTags: ["業務課題定義", "AIテーマ", "KPI"]
  },
  {
    id: "stage-rag",
    phase: "Phase 3 · RAG検証",
    title: "RAG/ナレッジ活用の検証設計",
    summary:
      "Hit@K / MRR を用いて検索精度を評価。改善履歴付き成果物としてレビュー合格になります。",
    estimatedMinutes: 200,
    status: "pending",
    skillTags: ["RAG", "検索評価", "ナレッジ"]
  },
  {
    id: "stage-poc",
    phase: "Phase 4 · PoC計画",
    title: "PoC計画と評価レポート",
    summary:
      "検証仮説・成功条件・リスクを整理。メンター承認で AIプロジェクト適合成果物に。",
    estimatedMinutes: 180,
    status: "pending",
    skillTags: ["PoC計画", "評価設計", "ガバナンス"]
  }
];

function getDotClass(status: TimelineEntry["status"]) {
  if (status === "done") return styles.timelineDotDone;
  if (status === "current") return "";
  return styles.timelineDotPending;
}

export default function LearnerRoadmapPage() {
  const params = useParams<{ roadmapId: string }>();
  const [roadmap, setRoadmap] = useState<Roadmap | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!params.roadmapId) return;
    let active = true;
    const load = async () => {
      try {
        const value = await getRoadmap(params.roadmapId);
        if (!active) return;
        setRoadmap(value);
        setError(null);
      } catch (err: unknown) {
        if (!active) return;
        setRoadmap(null);
        setError(
          err instanceof Error
            ? err.message
            : "ロードマップを取得できませんでした。フォールバック表示を行います。"
        );
      } finally {
        if (active) setLoading(false);
      }
    };
    void load();
    return () => {
      active = false;
    };
  }, [params.roadmapId]);

  const timeline = useMemo<TimelineEntry[]>(() => {
    if (!roadmap || roadmap.items.length === 0) {
      return FALLBACK_TIMELINE;
    }
    return roadmap.items.map<TimelineEntry>((item, index) => ({
      id: item.id,
      phase: `Phase ${index + 1}`,
      title: item.title,
      summary:
        item.prerequisiteSkillTags.length > 0
          ? `必要スキル: ${item.prerequisiteSkillTags.join(", ")}`
          : "現場での再利用を想定した実務タスク",
      estimatedMinutes: item.estimatedMinutes,
      status: index === 0 ? "current" : "pending",
      skillTags: item.prerequisiteSkillTags
    }));
  }, [roadmap]);

  const totalMinutes = timeline.reduce(
    (sum, entry) => sum + entry.estimatedMinutes,
    0
  );
  const doneCount = timeline.filter((entry) => entry.status === "done").length;
  const completion = timeline.length === 0 ? 0 : doneCount / timeline.length;

  return (
    <main className={styles.page}>
      <LearnerHero
        eyebrow="ロードマップ"
        title="目標ロールへのAIプロジェクト育成ロードマップ"
        lead={
          <>
            「学習」ではなく「業務課題→AIプロジェクト化」に近づく順序でフェーズを並べています。各フェーズで成果物を
            積み上げると、AIプロジェクト推進準備度のバッジが Ready に近づきます。
          </>
        }
        metrics={[
          {
            label: "ロードマップID",
            value: params.roadmapId ?? "—",
            hint: roadmap ? "API取得済み" : "デモプリセット表示中"
          },
          {
            label: "フェーズ数",
            value: timeline.length,
            suffix: "本",
            hint: `合計推定 ${Math.round(totalMinutes / 60)} 時間`
          },
          {
            label: "現在の完了率",
            value: Math.round(completion * 100),
            suffix: "%",
            progress: completion,
            hint: `完了 ${doneCount} / ${timeline.length}`
          }
        ]}
        actions={
          <>
            <Link href="/learner/learn" className={styles.actionPrimary}>
              受講者ホームへ
            </Link>
            <Link href="/learner/evidence" className={styles.actionGhost}>
              成果物を見る
            </Link>
          </>
        }
      />

      {loading ? (
        <div className={styles.skeletonBoxTall} />
      ) : null}

      {error ? (
        <div className={styles.section} role="status">
          <p className="muted" style={{ margin: 0 }}>
            ロードマップAPIから取得できませんでした ({error})。
            現場接続を意識したデモプリセットを表示しています。
          </p>
        </div>
      ) : null}

      <LearnerSection
        title="ロードマップ・タイムライン"
        meta="1フェーズ = 30〜90分のスモールタスクで構成。完了 / 進行中 / 未開始 が一目でわかります。"
      >
        <ol className={styles.timeline} style={{ listStyle: "none", padding: "0 0 0 1.5rem", margin: 0 }}>
          {timeline.map((entry) => (
            <li key={entry.id} className={styles.timelineItem}>
              <span
                className={`${styles.timelineDot} ${getDotClass(entry.status)}`}
                aria-hidden
              />
              <div className={styles.timelineHeader}>
                <span className={styles.evidenceMetaLabel}>{entry.phase}</span>
                <h3 className={styles.timelineTitle}>{entry.title}</h3>
                <span
                  className={`${styles.statusPill} ${
                    entry.status === "done"
                      ? styles.statusPassed
                      : entry.status === "current"
                      ? styles.statusSubmitted
                      : styles.statusUnknown
                  }`}
                >
                  {entry.status === "done"
                    ? "完了"
                    : entry.status === "current"
                    ? "進行中"
                    : "未開始"}
                </span>
                <span className={styles.timelineMeta}>
                  推定 {entry.estimatedMinutes} 分
                </span>
              </div>
              <p className={styles.timelineBody}>{entry.summary}</p>
              <div style={{ marginTop: "0.55rem" }}>
                <SkillChipList skills={entry.skillTags} />
              </div>
            </li>
          ))}
        </ol>
      </LearnerSection>
    </main>
  );
}
