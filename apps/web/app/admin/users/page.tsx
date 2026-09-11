"use client";

import { useEffect, useState } from "react";

import type { Role, UserAccount } from "@newfan/contracts";
import { getAdminUsers, patchAdminUser } from "@/lib/api";

type UserState = "active" | "invited" | "suspended";

const roleLabel: Record<string, string> = {learner: "受講者", mentor: "メンター", recruiter: "企業担当者", admin: "管理者", content_editor: "教材編集者"};
const stateLabel: Record<string, string> = {active: "利用中", invited: "招待中", suspended: "停止中"};

export default function AdminUsersPage() {
  const [items, setItems] = useState<UserAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [savingUserId, setSavingUserId] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [roleFilter, setRoleFilter] = useState<"" | Role>("");
  const [stateFilter, setStateFilter] = useState<"" | UserState>("");
  const [error, setError] = useState<string | null>(null);

  async function load(showLoading = true) {
    if (showLoading) {
      setLoading(true);
    }
    setError(null);
    try {
      const response = await getAdminUsers({
        q: query || undefined,
        role: roleFilter || undefined,
        state: stateFilter || undefined
      });
      setItems(response.items);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "ユーザー一覧取得に失敗しました");
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  }

  useEffect(() => {
    let active = true;
    getAdminUsers()
      .then((response) => {
        if (active) {
          setItems(response.items);
        }
      })
      .catch((loadError) => {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : "ユーザー一覧取得に失敗しました");
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

  async function updateUser(user: UserAccount, next: { role?: Role; state?: UserState }) {
    setSavingUserId(user.userId);
    setError(null);
    try {
      await patchAdminUser(user.userId, next);
      await load(false);
    } catch (updateError) {
      setError(updateError instanceof Error ? updateError.message : "ユーザー更新に失敗しました");
    } finally {
      setSavingUserId(null);
    }
  }

  return (
    <main>
      <header className="page-header">
        <h1>ユーザー管理</h1>
        <p className="muted">ユーザーの権限と利用状態を管理します。</p>
      </header>
      {error ? <p className="error">{error}</p> : null}

      <section>
        <h2>検索・フィルタ</h2>
        <div className="inline-actions">
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="氏名・ユーザーID"
          />
          <select value={roleFilter} onChange={(event) => setRoleFilter(event.target.value as "" | Role)}>
            <option value="">all roles</option>
            <option value="learner">受講者</option>
            <option value="recruiter">企業担当者</option>
            <option value="admin">管理者</option>
            <option value="content_editor">教材編集者</option>
          </select>
          <select
            value={stateFilter}
            onChange={(event) => setStateFilter(event.target.value as "" | UserState)}
          >
            <option value="">all states</option>
            <option value="active">利用中</option>
            <option value="invited">招待中</option>
            <option value="suspended">停止中</option>
          </select>
          <button type="button" onClick={() => void load()}>
            再検索
          </button>
        </div>
      </section>

      <section>
        <h2>ユーザー一覧</h2>
        {loading ? (
          <>
            <div className="skeleton" />
            <div className="skeleton" />
            <div className="skeleton" />
          </>
        ) : items.length === 0 ? (
          <p className="muted">対象ユーザーが見つかりません。</p>
        ) : (
          <ul className="card-list">
            {items.map((item) => (
              <li key={item.userId}>
                <div className="opportunity-head">
                  <strong>{item.displayName}</strong>
                  <span className="status-pill">{item.userId}</span>
                </div>
                <p className="muted">{`権限: ${roleLabel[item.role] ?? item.role} / 状態: ${stateLabel[item.state] ?? item.state}`}</p>
                <p className="muted">{`更新: ${new Date(item.updatedAt).toLocaleString("ja-JP")}`}</p>
                <div className="inline-actions">
                  <select
                    aria-label={`${item.displayName}の権限`}
                    value={item.role}
                    onChange={(event) =>
                      void updateUser(item, { role: event.target.value as Role })
                    }
                    disabled={savingUserId === item.userId}
                  >
                    <option value="learner">受講者</option>
                    <option value="mentor">メンター</option>
                    <option value="recruiter">企業担当者</option>
                    <option value="admin">管理者</option>
                    <option value="content_editor">教材編集者</option>
                  </select>
                  <select
                    aria-label={`${item.displayName}の利用状態`}
                    value={item.state}
                    onChange={(event) =>
                      void updateUser(item, { state: event.target.value as UserState })
                    }
                    disabled={savingUserId === item.userId}
                  >
                    <option value="active">利用中</option>
                    <option value="invited">招待中</option>
                    <option value="suspended">停止中</option>
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
