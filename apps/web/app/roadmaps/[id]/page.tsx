"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getRoadmap } from "@/lib/api";
import { EmptyState } from "@/app/components/product/EmptyState";
import { RoadmapTimeline } from "@/app/components/product/RoadmapTimeline";
import type { Roadmap } from "@newfan/contracts";

export default function RoadmapDetailPage() {
  const params = useParams<{ id: string }>();
  const [roadmap, setRoadmap] = useState<Roadmap | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchRoadmap() {
      try {
        setError(null);
        setLoading(true);
        if (!params.id) {
          return;
        }
        setRoadmap(await getRoadmap(params.id));
      } catch (e) {
        setError(e instanceof Error ? e.message : "ロードマップの取得に失敗しました");
      } finally {
        setLoading(false);
      }
    }
    void fetchRoadmap();
  }, [params.id]);

  return (
    <main>
      <div className="page-header">
        <h1>ロードマップ生成結果</h1>
        <p className="muted">何を、なぜ、その順番で学ぶかを明確に表示します。</p>
      </div>
      {error && <p className="error">{error}</p>}

      <div className="split">
        <section>
          <h2>Summary Card</h2>
          <p>目標ID: {roadmap?.goalId ?? "-"}</p>
          <p>期間: 12週間（初期推定）</p>
          <p>週学習時間: 8時間</p>
          <p className="muted">生成根拠: 目標との差分、前提関係、現在スキル</p>
        </section>

        <section className="right-panel">
          <h2>Right Panel</h2>
          <ul>
            <li>AI説明: 今週は API 基礎を優先するのが効果的です</li>
            <li>調整: 期間を短くする / 演習多めにする</li>
            <li>公開設定: 同意画面から変更可能</li>
          </ul>
        </section>
      </div>

      <section>
        <h2>Timeline</h2>
        {loading ? (
          <div>
            <div className="skeleton" />
            <div className="skeleton" />
            <div className="skeleton" />
          </div>
        ) : null}
        {!loading && !roadmap && (
          <EmptyState
            title="ロードマップなし"
            message="目標設定後にロードマップ生成を実行してください。"
          />
        )}
        <RoadmapTimeline roadmap={roadmap} />
      </section>
    </main>
  );
}
