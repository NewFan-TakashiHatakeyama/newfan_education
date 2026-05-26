"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listCurriculumVersions } from "@/lib/api";
import { EmptyState } from "@/app/components/product/EmptyState";
import type { CurriculumVersion } from "@newfan/contracts";

function semverToSortable(semver: string) {
  return semver
    .split(".")
    .map((v) => Number(v))
    .reduce((acc, cur, idx) => acc + cur * Math.pow(1000, 2 - idx), 0);
}

export default function AdminCurriculumPage() {
  const [rows, setRows] = useState<CurriculumVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        setError(null);
        setLoading(true);
        const values = await listCurriculumVersions();
        setRows(values);
      } catch (e) {
        setError(e instanceof Error ? e.message : "教材一覧の取得に失敗しました");
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, []);

  const sorted = [...rows].sort((a, b) => semverToSortable(b.version) - semverToSortable(a.version));

  return (
    <main>
      <div className="page-header">
        <h1>教材管理</h1>
        <p className="muted">教材の版管理、公開、差分確認、影響分析を行えます。</p>
      </div>
      {error && <p className="error">{error}</p>}

      <section>
        <h2>一覧</h2>
        {loading ? (
          <div>
            <div className="skeleton" />
            <div className="skeleton" />
            <div className="skeleton" />
          </div>
        ) : null}
        {!loading && sorted.length === 0 ? (
          <EmptyState
            title="教材なし"
            message="公開済み教材がありません。先に教材を追加してください。"
          />
        ) : null}
        {!loading && sorted.length > 0 ? (
          <ul className="card-list">
            {sorted.map((item) => (
              <li key={item.id}>
                <strong>{item.title}</strong>
                <p className="muted">教材名: {item.curriculumSlug}</p>
                <p className="muted">現行版: {item.version}</p>
                <p className="muted">状態: {item.published ? "公開中" : "非公開"}</p>
                <p className="muted">影響ユーザー: {Math.max(1, item.title.length % 7)} 人（デモ）</p>
                <p className="muted">更新種別: minor（デフォルト）</p>
                <div className="inline-actions">
                  <Link href={`/admin/curriculum/${item.id}/publish`}>公開/差分確認</Link>
                </div>
              </li>
            ))}
          </ul>
        ) : null}
      </section>
    </main>
  );
}
