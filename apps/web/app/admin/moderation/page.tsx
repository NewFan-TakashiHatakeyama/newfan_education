"use client";

import { useEffect, useState } from "react";
import type { ModerationCase, ModerationCaseStatus } from "@newfan/contracts";
import { getAdminModerationCases, patchAdminModerationBulkClose, patchAdminModerationCase } from "@/lib/api";

const STATUS_OPTIONS: ModerationCaseStatus[] = ["accepted", "investigating", "acted", "closed"];
const STATUS_LABEL: Record<ModerationCaseStatus, string> = {
  accepted: "受付",
  investigating: "調査",
  acted: "対応",
  closed: "クローズ"
};
type CaseFilter = "all" | "pending" | "overdue";

export default function AdminModerationPage() {
  const [items, setItems] = useState<ModerationCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<string | null>(null);
  const [filter, setFilter] = useState<CaseFilter>("all");
  const [selectedCaseIds, setSelectedCaseIds] = useState<string[]>([]);

  async function load(showLoading = true, filterValue = filter) {
    if (showLoading) {
      setLoading(true);
    }
    setError(null);
    try {
      const summary = await getAdminModerationCases({
        pendingOnly: filterValue === "pending",
        overdueOnly: filterValue === "overdue"
      });
      setItems(summary.items);
      setSelectedCaseIds((prev) => prev.filter((id) => summary.items.some((item) => item.id === id)));
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "モデレーション一覧の取得に失敗しました");
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  }

  useEffect(() => {
    let active = true;
    getAdminModerationCases({
      pendingOnly: filter === "pending",
      overdueOnly: filter === "overdue"
    })
      .then((summary) => {
        if (active) {
          setItems(summary.items);
        }
      })
      .catch((loadError) => {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : "モデレーション一覧の取得に失敗しました");
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, [filter]);

  async function updateStatus(item: ModerationCase, status: ModerationCaseStatus) {
    setUpdatingId(item.id);
    setError(null);
    try {
      await patchAdminModerationCase(item.id, {
        status,
        assignedAdmin: item.assignedAdmin ?? "admin-user"
      });
      await load(false);
    } catch (updateError) {
      setError(updateError instanceof Error ? updateError.message : "ケース更新に失敗しました");
    } finally {
      setUpdatingId(null);
    }
  }

  async function closeSelectedCases() {
    if (selectedCaseIds.length === 0) {
      return;
    }
    setUpdatingId("bulk-close");
    setError(null);
    try {
      await patchAdminModerationBulkClose({
        caseIds: selectedCaseIds,
        assignedAdmin: "admin-user"
      });
      await load(false);
    } catch (updateError) {
      setError(updateError instanceof Error ? updateError.message : "一括クローズに失敗しました");
    } finally {
      setUpdatingId(null);
    }
  }

  const allSelected = items.length > 0 && selectedCaseIds.length === items.length;

  return (
    <main>
      <header className="page-header">
        <h1>通報/モデレーション</h1>
        <p className="muted">通報ケースの状態を管理し、対応履歴を追跡します。</p>
      </header>
      {error ? <p className="error">{error}</p> : null}
      <section>
        <div className="inline-actions">
          <button type="button" onClick={() => { setLoading(true); setFilter("all"); }} disabled={filter === "all"}>
            すべて
          </button>
          <button type="button" onClick={() => { setLoading(true); setFilter("pending"); }} disabled={filter === "pending"}>
            未対応
          </button>
          <button type="button" onClick={() => { setLoading(true); setFilter("overdue"); }} disabled={filter === "overdue"}>
            期限超過
          </button>
          <button
            type="button"
            disabled={updatingId === "bulk-close" || selectedCaseIds.length === 0}
            onClick={() => void closeSelectedCases()}
          >
            {`選択中 ${selectedCaseIds.length} 件をクローズ`}
          </button>
          <label>
            <input
              type="checkbox"
              checked={allSelected}
              onChange={(event) => {
                if (event.target.checked) {
                  setSelectedCaseIds(items.map((item) => item.id));
                } else {
                  setSelectedCaseIds([]);
                }
              }}
            />
            全選択
          </label>
        </div>
        {loading ? (
          <>
            <div className="skeleton" />
            <div className="skeleton" />
            <div className="skeleton" />
          </>
        ) : (
          <ul className="card-list">
            {items.map((item) => (
              <li key={item.id}>
                <div className="opportunity-head">
                  <strong>{`${item.targetType}:${item.targetId}`}</strong>
                  <span className="status-pill">{STATUS_LABEL[item.status]}</span>
                </div>
                <label>
                  <input
                    type="checkbox"
                    checked={selectedCaseIds.includes(item.id)}
                    onChange={(event) => {
                      setSelectedCaseIds((prev) =>
                        event.target.checked
                          ? (prev.includes(item.id) ? prev : [...prev, item.id])
                          : prev.filter((value) => value !== item.id)
                      );
                    }}
                  />
                  一括クローズ対象に追加
                </label>
                <p className="muted">{`理由: ${item.reason}`}</p>
                <p className="muted">{`通報者: ${item.reportedBy}`}</p>
                <p className="muted">{`担当: ${item.assignedAdmin ?? "未割当"}`}</p>
                <p className="muted">{`対応期限: ${new Date(item.dueAt).toLocaleString("ja-JP")}`}</p>
                <p className="muted">{`期限状態: ${item.isOverdue ? "期限超過" : "期限内"}`}</p>
                <p className="muted">{`更新日時: ${new Date(item.updatedAt).toLocaleString("ja-JP")}`}</p>
                <div className="inline-actions">
                  <select
                    value={item.status}
                    onChange={(event) => void updateStatus(item, event.target.value as ModerationCaseStatus)}
                    disabled={updatingId === item.id}
                  >
                    {STATUS_OPTIONS.map((status) => (
                      <option key={status} value={status}>
                        {STATUS_LABEL[status]}
                      </option>
                    ))}
                  </select>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
