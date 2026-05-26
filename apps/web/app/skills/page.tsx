"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { getSkillsGap } from "@/lib/api";
import { EmptyState } from "@/app/components/product/EmptyState";
import { SkillGapCard } from "@/app/components/product/SkillGapCard";
import type { SkillGapItem, SkillsGapSummary } from "@newfan/contracts";

export default function SkillsPage() {
  const [showCareerVisibleOnly, setShowCareerVisibleOnly] = useState(false);
  const [audienceMode, setAudienceMode] = useState<"learner" | "business">("learner");
  const [skillsGap, setSkillsGap] = useState<SkillsGapSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        setError(null);
        setLoading(true);
        const data = await getSkillsGap();
        setSkillsGap(data);
      } catch (e) {
        setError(e instanceof Error ? e.message : "スキル差分の取得に失敗しました");
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, []);

  const shownSkills = useMemo(
    () =>
      (skillsGap?.items ?? []).filter((skill) => !showCareerVisibleOnly || skill.isCareerVisible),
    [showCareerVisibleOnly, skillsGap]
  );

  const totalTarget = shownSkills.reduce((acc, skill) => acc + skill.targetLevel, 0);
  const totalCurrent = shownSkills.reduce(
    (acc, skill) => acc + Math.min(skill.currentLevel, skill.targetLevel),
    0
  );
  const attainmentRate = totalTarget === 0 ? 0 : Math.round((totalCurrent / totalTarget) * 100);

  const reachedCount = shownSkills.filter((skill) => skill.currentLevel >= skill.targetLevel).length;
  const inProgressCount = shownSkills.filter(
    (skill) => skill.currentLevel > 0 && skill.currentLevel < skill.targetLevel
  ).length;
  const lackingCount = shownSkills.filter((skill) => skill.currentLevel === 0).length;

  const recommendedSkills: SkillGapItem[] = [...shownSkills]
    .sort((a, b) => b.gapScore - a.gapScore)
    .slice(0, 3);

  return (
    <main>
      <div className="page-header">
        <div className="page-title-row">
          <h1>スキル差分画面</h1>
          <span className="status-pill">最終更新: {skillsGap?.lastUpdatedAt ?? "-"}</span>
        </div>
        <p className="muted">
          目標職種: {skillsGap?.targetRole ?? "Backend Engineer"} / 到達率:{" "}
          {skillsGap?.attainmentRate ?? attainmentRate}%
        </p>
      </div>
      {error && <p className="error">{error}</p>}

      {loading ? (
        <section>
          <div className="skeleton" />
          <div className="skeleton" />
          <div className="skeleton" />
        </section>
      ) : null}
      {!loading && shownSkills.length === 0 ? (
        <section>
          <EmptyState
            title="スキル差分なし"
            message="学習データが不足しています。教材を完了して差分を計算してください。"
          />
        </section>
      ) : null}

      {!loading && shownSkills.length > 0 && (
        <>
      <section>
        <h2>表示モード</h2>
        <div className="inline-actions">
          <button type="button" onClick={() => setAudienceMode("learner")}>
            学習者向け詳細
          </button>
          <button type="button" className="ghost-button" onClick={() => setAudienceMode("business")}>
            企業向け抽象表示
          </button>
          <label style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
            <input
              type="checkbox"
              checked={showCareerVisibleOnly}
              onChange={(e) => setShowCareerVisibleOnly(e.target.checked)}
            />
            公開可能なスキルのみ表示
          </label>
        </div>
        <p className="muted">
          {audienceMode === "business"
            ? "企業向け表示では不足点を直接表示せず、到達済み/学習中/次に到達予定の抽象表現を優先します。"
            : "学習者本人には現在レベル、目標レベル、証跡数を表示します。"}
        </p>
      </section>

      <section>
        <h2>Skill Gap Summary</h2>
        <div className="kpi">
          <div>
            <strong>到達済み</strong>
            <p>{reachedCount}</p>
          </div>
          <div>
            <strong>学習中</strong>
            <p>{inProgressCount}</p>
          </div>
          <div>
            <strong>不足</strong>
            <p>{lackingCount}</p>
          </div>
        </div>
      </section>

      <section>
        <h2>Skill Matrix</h2>
        <ul className="card-list">
          {shownSkills.map((skill) =>
            audienceMode === "learner" ? (
              <SkillGapCard
                key={skill.id}
                skill={skill.name}
                current={skill.currentLevel}
                target={skill.targetLevel}
                evidenceCount={skill.evidenceCount}
              />
            ) : (
              <li key={skill.id}>
                <strong>{skill.name}</strong>
                <p className="muted">
                  {skill.currentLevel >= skill.targetLevel
                    ? "到達済み"
                    : skill.currentLevel > 0
                      ? "学習中"
                      : "次に到達予定"}
                </p>
                <p className="muted">gap_score: {skill.gapScore}</p>
              </li>
            )
          )}
        </ul>
      </section>

      {audienceMode === "learner" && (
        <section>
          <h2>証跡リンク</h2>
          <ul className="card-list">
            {shownSkills.map((skill) => (
              <li key={`evidence-${skill.id}`}>
                {skill.name}: <Link href={skill.evidenceLink}>完了教材/提出課題/レビューへ</Link>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section>
        <h2>Recommended Actions</h2>
        <ul className="card-list">
          <li>
            次に学ぶ教材:
            {" "}
            {recommendedSkills[0] ? (
              <Link href={recommendedSkills[0].evidenceLink}>
                {recommendedSkills[0].name} (gap_score: {recommendedSkills[0].gapScore})
              </Link>
            ) : (
              "候補なし"
            )}
          </li>
          <li>
            復習すべき教材:
            {" "}
            <Link href="/learn">FastAPI 入門を復習</Link>
          </li>
          <li>
            提出すべき課題:
            {" "}
            <Link href="/learn/python-basic/variables-v1/exercise">Python演習を再提出</Link>
          </li>
        </ul>
      </section>
      </>
      )}
    </main>
  );
}
