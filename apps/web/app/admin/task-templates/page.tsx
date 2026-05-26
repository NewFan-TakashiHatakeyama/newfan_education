"use client";

import { useEffect, useState } from "react";

import { getAdminTaskTemplates } from "@/lib/api";

type TaskTemplate = {
  id: string;
  title: string;
  category: string;
  defaultDifficulty: number;
};

export default function AdminTaskTemplatesPage() {
  const [items, setItems] = useState<TaskTemplate[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAdminTaskTemplates()
      .then((result) => setItems(result.items))
      .catch((err) => setError(err instanceof Error ? err.message : "取得に失敗しました"));
  }, []);

  return (
    <main>
      <div className="page-header">
        <h1>タスクテンプレート管理</h1>
        <p className="muted">Notebook / SQL / RAG / OCR 演習のテンプレートを管理します。</p>
      </div>
      {error ? <p className="error">{error}</p> : null}
      <section>
        <ul className="card-list">
          {items.map((item) => (
            <li key={item.id}>
              <strong>{item.title}</strong>
              <p className="muted">{item.category}</p>
              <p className="muted">標準難易度: {item.defaultDifficulty}</p>
            </li>
          ))}
          {items.length === 0 ? <li>テンプレートがありません。</li> : null}
        </ul>
      </section>
    </main>
  );
}
