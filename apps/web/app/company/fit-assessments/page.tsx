"use client";

import { useEffect, useState } from "react";

import type { FitAssessmentListItem } from "@newfan/contracts";
import { listFitAssessments } from "@/lib/api";

export default function FitAssessmentsPage() {
  const [items, setItems] = useState<FitAssessmentListItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listFitAssessments()
      .then((result) => setItems(result.items))
      .catch((err) => setError(err instanceof Error ? err.message : "取得に失敗しました"));
  }, []);

  return (
    <main>
      <div className="page-header">
        <h1>案件適合度履歴</h1>
        <p className="muted">案件要件に対する適合度評価の履歴を確認します。</p>
      </div>
      {error ? <p className="error">{error}</p> : null}
      <section>
        <ul className="card-list">
          {items.map((item) => (
            <li key={item.id}>
              <strong>{item.requirementId}</strong>
              <p className="muted">Fit Score: {item.fitScore}</p>
              <p className="muted">Matched: {item.matchedSkills.join(", ")}</p>
              <p className="muted">Gap: {item.gapSkills.join(", ") || "なし"}</p>
              <p className="muted">Recommended Learner: {item.recommendedLearnerId}</p>
            </li>
          ))}
          {items.length === 0 ? <li>履歴がありません。</li> : null}
        </ul>
      </section>
    </main>
  );
}
