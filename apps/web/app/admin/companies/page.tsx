"use client";

import { useEffect, useState } from "react";
import type { Company } from "@newfan/contracts";
import { getAdminCompanies, patchAdminCompaniesBulkStatus, patchAdminCompany } from "@/lib/api";

export default function AdminCompaniesPage() {
  const [items, setItems] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<string | null>(null);
  const [contactDrafts, setContactDrafts] = useState<Record<string, { name: string; phone: string }>>({});
  const [selectedCompanyIds, setSelectedCompanyIds] = useState<string[]>([]);
  const [bulkStatus, setBulkStatus] = useState<"active" | "stopped">("active");

  async function load(showLoading = true) {
    if (showLoading) {
      setLoading(true);
    }
    try {
      setError(null);
      const summary = await getAdminCompanies();
      setItems(summary.items);
      setSelectedCompanyIds((prev) => prev.filter((id) => summary.items.some((item) => item.id === id)));
      setContactDrafts((prev) => {
        const next = { ...prev };
        for (const company of summary.items) {
          if (!next[company.id]) {
            next[company.id] = {
              name: company.contactPersonName,
              phone: company.contactPersonPhone
            };
          }
        }
        return next;
      });
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "企業一覧の取得に失敗しました");
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  }

  useEffect(() => {
    let active = true;
    getAdminCompanies()
      .then((summary) => {
        if (!active) {
          return;
        }
        setItems(summary.items);
        setContactDrafts((prev) => {
          const next = { ...prev };
          for (const company of summary.items) {
            if (!next[company.id]) {
              next[company.id] = {
                name: company.contactPersonName,
                phone: company.contactPersonPhone
              };
            }
          }
          return next;
        });
      })
      .catch((loadError) => {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : "企業一覧の取得に失敗しました");
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
  }, []);

  async function updateStatus(companyId: string, status: "active" | "stopped") {
    setUpdatingId(companyId);
    try {
      setError(null);
      await patchAdminCompany(companyId, { status });
      await load(false);
    } catch (updateError) {
      setError(updateError instanceof Error ? updateError.message : "企業ステータスの更新に失敗しました");
    } finally {
      setUpdatingId(null);
    }
  }

  async function saveContact(companyId: string) {
    const draft = contactDrafts[companyId];
    if (!draft) {
      return;
    }
    setUpdatingId(companyId);
    try {
      setError(null);
      await patchAdminCompany(companyId, {
        contactPersonName: draft.name,
        contactPersonPhone: draft.phone
      });
      await load(false);
    } catch (updateError) {
      setError(updateError instanceof Error ? updateError.message : "担当者情報の更新に失敗しました");
    } finally {
      setUpdatingId(null);
    }
  }

  async function applyBulkStatus() {
    if (selectedCompanyIds.length === 0) {
      return;
    }
    setUpdatingId("bulk");
    try {
      setError(null);
      await patchAdminCompaniesBulkStatus({ companyIds: selectedCompanyIds, status: bulkStatus });
      await load(false);
    } catch (updateError) {
      setError(updateError instanceof Error ? updateError.message : "企業ステータスの一括更新に失敗しました");
    } finally {
      setUpdatingId(null);
    }
  }

  const allSelected = items.length > 0 && selectedCompanyIds.length === items.length;

  return (
    <main>
      <header className="page-header">
        <h1>企業管理</h1>
        <p className="muted">登録企業の状態と公開中の求人/案件数を管理者が確認します。</p>
      </header>
      {error ? <p className="error">{error}</p> : null}
      <section>
        <div className="inline-actions">
          <label htmlFor="bulk-company-status">一括ステータス更新</label>
          <select
            id="bulk-company-status"
            value={bulkStatus}
            onChange={(event) => setBulkStatus(event.target.value as "active" | "stopped")}
          >
            <option value="active">active</option>
            <option value="stopped">stopped</option>
          </select>
          <button type="button" disabled={updatingId === "bulk" || selectedCompanyIds.length === 0} onClick={() => void applyBulkStatus()}>
            {`選択中 ${selectedCompanyIds.length} 件を更新`}
          </button>
          <label>
            <input
              type="checkbox"
              checked={allSelected}
              onChange={(event) => {
                if (event.target.checked) {
                  setSelectedCompanyIds(items.map((item) => item.id));
                } else {
                  setSelectedCompanyIds([]);
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
                  <strong>{item.name}</strong>
                  <span className="status-pill">{item.status}</span>
                </div>
                <label>
                  <input
                    type="checkbox"
                    checked={selectedCompanyIds.includes(item.id)}
                    onChange={(event) => {
                      setSelectedCompanyIds((prev) =>
                        event.target.checked
                          ? (prev.includes(item.id) ? prev : [...prev, item.id])
                          : prev.filter((value) => value !== item.id)
                      );
                    }}
                  />
                  一括操作対象に追加
                </label>
                <p className="muted">{`業種: ${item.industry}`}</p>
                <p className="muted">{`公開中求人/案件: ${item.openOpportunityCount}`}</p>
                <p className="muted">{`連絡先: ${item.contactEmail}`}</p>
                <p className="muted">{`担当者: ${item.contactPersonName}`}</p>
                <p className="muted">{`電話: ${item.contactPersonPhone}`}</p>
                <p className="muted">{`更新日時: ${new Date(item.updatedAt).toLocaleString("ja-JP")}`}</p>
                <div className="inline-actions">
                  <button
                    type="button"
                    disabled={updatingId === item.id || item.status === "active"}
                    onClick={() => void updateStatus(item.id, "active")}
                  >
                    稼働中にする
                  </button>
                  <button
                    type="button"
                    className="ghost-button"
                    disabled={updatingId === item.id || item.status === "stopped"}
                    onClick={() => void updateStatus(item.id, "stopped")}
                  >
                    停止中にする
                  </button>
                </div>
                <div className="inline-actions">
                  <input
                    aria-label={`${item.name} 担当者名`}
                    value={contactDrafts[item.id]?.name ?? item.contactPersonName}
                    onChange={(event) =>
                      setContactDrafts((prev) => ({
                        ...prev,
                        [item.id]: {
                          name: event.target.value,
                          phone: prev[item.id]?.phone ?? item.contactPersonPhone
                        }
                      }))
                    }
                  />
                  <input
                    aria-label={`${item.name} 担当者電話`}
                    value={contactDrafts[item.id]?.phone ?? item.contactPersonPhone}
                    onChange={(event) =>
                      setContactDrafts((prev) => ({
                        ...prev,
                        [item.id]: {
                          name: prev[item.id]?.name ?? item.contactPersonName,
                          phone: event.target.value
                        }
                      }))
                    }
                  />
                  <button type="button" disabled={updatingId === item.id} onClick={() => void saveContact(item.id)}>
                    担当者情報を保存
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
