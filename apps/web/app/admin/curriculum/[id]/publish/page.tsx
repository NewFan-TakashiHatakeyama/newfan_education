"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import {
  getCurriculumImpact,
  publishCurriculum,
  listCurriculumVersions
} from "@/lib/api";
import { CurriculumDiffViewer } from "@/app/components/admin/CurriculumDiffViewer";
import type { CurriculumImpactSummary, CurriculumVersion } from "@newfan/contracts";

type UpdateType = "minor" | "major" | "breaking";

export default function AdminCurriculumPublishPage() {
  const params = useParams<{ id: string }>();
  const [current, setCurrent] = useState<CurriculumVersion | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [publishedMessage, setPublishedMessage] = useState<string | null>(null);
  const [impact, setImpact] = useState<CurriculumImpactSummary | null>(null);
  const [impactLoading, setImpactLoading] = useState(false);

  const [title, setTitle] = useState("");
  const [version, setVersion] = useState("1.0.1");
  const [mdxPath, setMdxPath] = useState("");
  const [difficulty, setDifficulty] = useState(2);
  const [estimatedMinutes, setEstimatedMinutes] = useState(30);
  const [skillTagsText, setSkillTagsText] = useState("python.api.fastapi");
  const [updateType, setUpdateType] = useState<UpdateType>("minor");

  useEffect(() => {
    async function load() {
      try {
        setError(null);
        setLoading(true);
        const values = await listCurriculumVersions();
        const found = values.find((value) => value.id === params.id) ?? null;
        setCurrent(found);
        if (found) {
          setTitle(found.title);
          setMdxPath(found.mdxPath);
          setImpactLoading(true);
          try {
            setImpact(await getCurriculumImpact(found.id));
          } finally {
            setImpactLoading(false);
          }
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : "教材情報の取得に失敗しました");
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, [params.id]);

  const diffRows = useMemo(() => {
    if (!current) {
      return [];
    }
    const rows = [
      { field: "title", before: current.title, after: title },
      { field: "version", before: current.version, after: version },
      { field: "mdxPath", before: current.mdxPath, after: mdxPath }
    ];
    return rows.filter((row) => row.before !== row.after);
  }, [current, mdxPath, title, version]);

  async function onPublish() {
    if (!current) {
      return;
    }
    try {
      setError(null);
      const created = await publishCurriculum({
        curriculumSlug: current.curriculumSlug,
        version,
        title,
        mdxPath,
        skillTags: skillTagsText
          .split(",")
          .map((v) => v.trim())
          .filter(Boolean),
        difficulty,
        estimatedMinutes
      });
      setPublishedMessage(`公開完了: ${created.curriculumSlug} v${created.version}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "公開に失敗しました");
    }
  }

  return (
    <main>
      <div className="page-header">
        <h1>教材公開/差分確認</h1>
        <p className="muted">差分確認と影響分析（最小）を経て新バージョンを公開します。</p>
      </div>
      {error && <p className="error">{error}</p>}
      {publishedMessage && <p>{publishedMessage}</p>}

      {loading ? (
        <section>
          <div className="skeleton" />
          <div className="skeleton" />
          <div className="skeleton" />
        </section>
      ) : null}

      {!loading && !current ? (
        <section>
          <p className="muted">指定教材が見つかりませんでした。</p>
        </section>
      ) : null}

      {!loading && current ? (
        <>
          <section>
            <h2>公開ドラフト</h2>
            <label htmlFor="title">タイトル</label>
            <input id="title" value={title} onChange={(e) => setTitle(e.target.value)} />
            <label htmlFor="version">version</label>
            <input id="version" value={version} onChange={(e) => setVersion(e.target.value)} />
            <label htmlFor="mdxPath">mdxPath</label>
            <input id="mdxPath" value={mdxPath} onChange={(e) => setMdxPath(e.target.value)} />
            <label htmlFor="updateType">更新種別</label>
            <select
              id="updateType"
              value={updateType}
              onChange={(e) => setUpdateType(e.target.value as UpdateType)}
            >
              <option value="minor">minor</option>
              <option value="major">major</option>
              <option value="breaking">breaking</option>
            </select>
            <label htmlFor="difficulty">difficulty</label>
            <input
              id="difficulty"
              type="number"
              min={1}
              max={5}
              value={difficulty}
              onChange={(e) => setDifficulty(Number(e.target.value))}
            />
            <label htmlFor="estimatedMinutes">estimatedMinutes</label>
            <input
              id="estimatedMinutes"
              type="number"
              min={5}
              value={estimatedMinutes}
              onChange={(e) => setEstimatedMinutes(Number(e.target.value))}
            />
            <label htmlFor="skillTags">skillTags（カンマ区切り）</label>
            <input
              id="skillTags"
              value={skillTagsText}
              onChange={(e) => setSkillTagsText(e.target.value)}
            />
          </section>

          <CurriculumDiffViewer rows={diffRows} updateType={updateType} />

          <section>
            <h2>影響分析（API連携）</h2>
            {impactLoading ? (
              <div>
                <div className="skeleton" />
                <div className="skeleton" />
              </div>
            ) : null}
            {!impactLoading && impact ? (
              <>
                <p className="muted">対象ロードマップ数: {impact.affectedRoadmapCount}</p>
                <p className="muted">通知対象ユーザー数: {impact.notificationTargetCount}</p>
                <details>
                  <summary>対象ユーザーIDを表示</summary>
                  <pre>{JSON.stringify(impact.affectedUserIds, null, 2)}</pre>
                </details>
                <details>
                  <summary>対象ロードマップIDを表示</summary>
                  <pre>{JSON.stringify(impact.affectedRoadmapIds, null, 2)}</pre>
                </details>
              </>
            ) : null}
            {!impactLoading && !impact ? (
              <p className="muted">影響分析データを取得できませんでした。</p>
            ) : null}
            <div className="inline-actions">
              <button type="button" onClick={onPublish}>
                公開承認して version 発行
              </button>
            </div>
          </section>
        </>
      ) : null}
    </main>
  );
}
