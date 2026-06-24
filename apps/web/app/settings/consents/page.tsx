"use client";

import { useState } from "react";
import { createConsent, getMyConsents } from "@/lib/api";
import { ConsentCard } from "@/app/components/product/ConsentCard";
import { EmptyState } from "@/app/components/product/EmptyState";
import { VisibilityBadge } from "@/app/components/product/VisibilityBadge";
import type { ConsentRecord } from "@newfan/contracts";

type ConsentOption = {
  id: "career_profile" | "talent_search";
  title: string;
  purpose: string;
  scope: string;
  dataTarget: string;
};

const CONSENT_OPTIONS: ConsentOption[] = [
  {
    id: "career_profile",
    title: "企業にプロフィールを表示",
    purpose: "社内育成担当者に成果物と進捗を確認してもらうため",
    scope: "育成担当者・DX推進責任者",
    dataTarget: "プロフィール、育成成果物、スキル進捗"
  },
  {
    id: "talent_search",
    title: "キャリア機会の推薦に学習データを利用",
    purpose: "育成成果物に基づき適切な社内・外部キャリア機会を提案するため",
    scope: "レコメンドエンジン、許可済み担当者",
    dataTarget: "学習履歴、進捗、目標情報"
  }
];

export default function ConsentSettingsPage() {
  const [records, setRecords] = useState<ConsentRecord[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function saveConsent(type: ConsentOption["id"]) {
    try {
      setError(null);
      const created = await createConsent({ consentType: type, granted: true });
      setRecords((prev) => [created, ...prev]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "同意保存に失敗しました");
    }
  }

  async function refresh() {
    try {
      setError(null);
      setRecords(await getMyConsents());
    } catch (e) {
      setError(e instanceof Error ? e.message : "同意履歴の取得に失敗しました");
    }
  }

  return (
    <main>
      <div className="page-header">
        <h1>キャリア公開同意画面</h1>
        <p className="muted">
          公開範囲、利用目的、対象データを確認して明示同意を管理します。
        </p>
      </div>
      {error && <p className="error">{error}</p>}

      <section>
        <h2>現在の公開状態</h2>
        <p className="muted">
          プロフィール: <VisibilityBadge mode="limited" /> / 学習データ:{" "}
          <VisibilityBadge mode="non_public" />
        </p>
        <button type="button" onClick={refresh}>
          同意済み項目を更新
        </button>
      </section>

      <section>
        <h2>Consent Cards</h2>
        {CONSENT_OPTIONS.map((option) => (
          <ConsentCard
            key={option.id}
            title={option.title}
            purpose={option.purpose}
            scope={option.scope}
            dataTarget={option.dataTarget}
            onAccept={() => saveConsent(option.id)}
          />
        ))}
      </section>

      <section>
        <h2>同意履歴</h2>
        <ul className="card-list">
          {records.map((record) => (
            <li key={record.id}>
              <strong>{record.consentType}</strong>
              <p className="muted">
                granted: {String(record.granted)} / at: {record.grantedAt}
              </p>
            </li>
          ))}
        </ul>
        {records.length === 0 && (
          <EmptyState
            title="同意履歴なし"
            message="まだ同意履歴がありません。必要な同意を有効化するとここに表示されます。"
          />
        )}
      </section>
    </main>
  );
}
