"use client";

import Link from "next/link";
import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import type { NotificationDeliverySetting, NotificationItem } from "@newfan/contracts";

import { EmptyState } from "@/app/components/product/EmptyState";
import {
  getNotifications,
  getNotificationDeliverySettings,
  markAllNotificationsRead,
  markNotificationRead,
  patchNotificationDeliverySetting
} from "@/lib/api";
import { buildNotificationCenterLink } from "@/lib/notificationLinks";

type NotificationTab = "all" | "learning" | "career" | "dm" | "admin";
type NotificationCategoryTab = Exclude<NotificationTab, "all">;
type CategoryCountMap = Record<NotificationCategoryTab, number>;
type CategoryFirstIdMap = Record<NotificationCategoryTab, string | null>;

const TABS: Array<{ value: NotificationTab; label: string }> = [
  { value: "all", label: "すべて" },
  { value: "learning", label: "学習" },
  { value: "career", label: "キャリア" },
  { value: "dm", label: "DM" },
  { value: "admin", label: "運営" }
];

const EMPTY_UNREAD_COUNTS: CategoryCountMap = {
  learning: 0,
  career: 0,
  dm: 0,
  admin: 0
};
const EMPTY_FIRST_UNREAD_IDS: CategoryFirstIdMap = {
  learning: null,
  career: null,
  dm: null,
  admin: null
};

function buildUnreadMeta(items: NotificationItem[]): {
  counts: CategoryCountMap;
  firstUnreadIds: CategoryFirstIdMap;
} {
  const counts = { ...EMPTY_UNREAD_COUNTS };
  const firstUnreadIds = { ...EMPTY_FIRST_UNREAD_IDS };
  for (const item of items) {
    if (item.readAt === null) {
      counts[item.category] += 1;
      if (firstUnreadIds[item.category] === null) {
        firstUnreadIds[item.category] = item.id;
      }
    }
  }
  return { counts, firstUnreadIds };
}

function NotificationsPageContent() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [settings, setSettings] = useState<NotificationDeliverySetting[]>([]);
  const [savingCategory, setSavingCategory] = useState<string | null>(null);
  const [shareFeedback, setShareFeedback] = useState<string | null>(null);
  const [unreadByCategory, setUnreadByCategory] = useState<CategoryCountMap>(EMPTY_UNREAD_COUNTS);
  const [firstUnreadIdByCategory, setFirstUnreadIdByCategory] = useState<CategoryFirstIdMap>(EMPTY_FIRST_UNREAD_IDS);
  const queryTab = searchParams.get("tab");
  const queryUnread = searchParams.get("unread");
  const querySelectedId = searchParams.get("selectedId");
  const hasValidTab = TABS.some((candidate) => candidate.value === queryTab);
  const hasValidUnread = queryUnread === null || queryUnread === "true";
  const tab: NotificationTab = hasValidTab ? (queryTab as NotificationTab) : "all";
  const unreadOnly = queryUnread === "true";

  const selectedItem = useMemo(
    () => items.find((item) => item.id === querySelectedId) ?? null,
    [items, querySelectedId]
  );
  const importantItems = useMemo(
    () => items.filter((item) => item.isImportant),
    [items]
  );
  const regularItems = useMemo(
    () => items.filter((item) => !item.isImportant),
    [items]
  );

  const syncQuery = useCallback(
    (nextValues: { tab?: NotificationTab; unread?: boolean; selectedId?: string | null }) => {
      const params = new URLSearchParams(searchParams.toString());
      const nextTab = nextValues.tab ?? tab;
      const nextUnread = nextValues.unread ?? unreadOnly;
      const nextSelectedId =
        nextValues.selectedId !== undefined ? nextValues.selectedId : querySelectedId;
      if (nextValues.selectedId !== undefined && nextValues.selectedId !== querySelectedId) {
        setShareFeedback(null);
      }

      if (nextTab === "all") {
        params.delete("tab");
      } else {
        params.set("tab", nextTab);
      }
      if (nextUnread) {
        params.set("unread", "true");
      } else {
        params.delete("unread");
      }
      if (nextSelectedId) {
        params.set("selectedId", nextSelectedId);
      } else {
        params.delete("selectedId");
      }

      const query = params.toString();
      router.replace(`${pathname}${query ? `?${query}` : ""}`);
    },
    [pathname, querySelectedId, router, searchParams, tab, unreadOnly]
  );

  useEffect(() => {
    if (hasValidTab && hasValidUnread) {
      return;
    }
    const params = new URLSearchParams(searchParams.toString());
    if (!hasValidTab || tab === "all") {
      params.delete("tab");
    } else {
      params.set("tab", tab);
    }
    if (!hasValidUnread || !unreadOnly) {
      params.delete("unread");
    } else {
      params.set("unread", "true");
    }
    const query = params.toString();
    router.replace(`${pathname}${query ? `?${query}` : ""}`);
  }, [hasValidTab, hasValidUnread, pathname, router, searchParams, tab, unreadOnly]);

  useEffect(() => {
    let active = true;
    Promise.all([getNotifications({ tab, unread: unreadOnly }), getNotifications()])
      .then(([summary, allSummary]) => {
        if (!active) {
          return;
        }
        setItems(summary.items);
        setUnreadCount(allSummary.unreadCount);
        const unreadMeta = buildUnreadMeta(allSummary.items);
        setUnreadByCategory(unreadMeta.counts);
        setFirstUnreadIdByCategory(unreadMeta.firstUnreadIds);
        const hasSelected = querySelectedId
          ? summary.items.some((item) => item.id === querySelectedId)
          : false;
        const nextSelectedId = hasSelected ? querySelectedId : (summary.items[0]?.id ?? null);
        if (nextSelectedId !== querySelectedId) {
          syncQuery({ selectedId: nextSelectedId });
        }
      })
      .catch((loadError) => {
        if (!active) {
          return;
        }
        setError(loadError instanceof Error ? loadError.message : "通知の読み込みに失敗しました");
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, [querySelectedId, syncQuery, tab, unreadOnly]);

  useEffect(() => {
    let active = true;
    getNotificationDeliverySettings()
      .then((summary) => {
        if (!active) {
          return;
        }
        setSettings(summary.items);
      })
      .catch((loadError) => {
        if (!active) {
          return;
        }
        setError(loadError instanceof Error ? loadError.message : "通知配信設定の取得に失敗しました");
      });
    return () => {
      active = false;
    };
  }, []);

  async function refreshData() {
    const [summary, allSummary] = await Promise.all([
      getNotifications({ tab, unread: unreadOnly }),
      getNotifications()
    ]);
    setItems(summary.items);
    setUnreadCount(allSummary.unreadCount);
    const unreadMeta = buildUnreadMeta(allSummary.items);
    setUnreadByCategory(unreadMeta.counts);
    setFirstUnreadIdByCategory(unreadMeta.firstUnreadIds);
    const hasSelected = querySelectedId
      ? summary.items.some((item) => item.id === querySelectedId)
      : false;
    const nextSelectedId = hasSelected ? querySelectedId : (summary.items[0]?.id ?? null);
    if (nextSelectedId !== querySelectedId) {
      syncQuery({ selectedId: nextSelectedId });
    }
  }

  async function onMarkRead(notificationId: string) {
    setBusy(true);
    setLoading(true);
    try {
      await markNotificationRead(notificationId);
      await refreshData();
    } catch (markError) {
      setError(markError instanceof Error ? markError.message : "既読更新に失敗しました");
    } finally {
      setLoading(false);
      setBusy(false);
    }
  }

  async function onMarkAllRead() {
    setBusy(true);
    setLoading(true);
    try {
      await markAllNotificationsRead();
      await refreshData();
    } catch (markError) {
      setError(markError instanceof Error ? markError.message : "全既読処理に失敗しました");
    } finally {
      setLoading(false);
      setBusy(false);
    }
  }

  async function onUpdateSetting(
    category: NotificationDeliverySetting["category"],
    patch: Partial<Pick<NotificationDeliverySetting, "emailEnabled" | "inAppEnabled" | "pushEnabled">>
  ) {
    const current = settings.find((item) => item.category === category);
    if (!current) {
      return;
    }
    const next = {
      emailEnabled: patch.emailEnabled ?? current.emailEnabled,
      inAppEnabled: patch.inAppEnabled ?? current.inAppEnabled,
      pushEnabled: patch.pushEnabled ?? current.pushEnabled
    };
    setSavingCategory(category);
    setError(null);
    try {
      const updated = await patchNotificationDeliverySetting(category, next);
      setSettings((prev) =>
        prev.map((item) =>
          item.category === category
            ? {
                category: updated.category,
                emailEnabled: updated.emailEnabled,
                inAppEnabled: updated.inAppEnabled,
                pushEnabled: updated.pushEnabled,
                updatedAt: updated.updatedAt
              }
            : item
        )
      );
    } catch (patchError) {
      setError(patchError instanceof Error ? patchError.message : "通知配信設定の更新に失敗しました");
    } finally {
      setSavingCategory(null);
    }
  }

  async function onCopySelectedNotificationLink() {
    if (!selectedItem) {
      return;
    }
    const path = buildNotificationCenterLink({
      category: selectedItem.category,
      selectedId: selectedItem.id
    });
    try {
      await navigator.clipboard.writeText(`${window.location.origin}${path}`);
      setShareFeedback("共有リンクをコピーしました");
    } catch {
      setShareFeedback("共有リンクのコピーに失敗しました");
    }
  }

  return (
    <main>
      <header className="page-header">
        <div className="page-title-row">
          <div>
            <h1>通知センター</h1>
            <p className="muted">学習・キャリア・DM・運営通知をカテゴリ別に確認できます。</p>
            <div className="inline-actions">
              <Link
                href={buildNotificationCenterLink({
                  category: "learning",
                  unreadOnly: true,
                  selectedId: firstUnreadIdByCategory.learning ?? undefined
                })}
                className="status-pill"
              >
                {`学習 未読 ${unreadByCategory.learning}`}
              </Link>
              <Link
                href={buildNotificationCenterLink({
                  category: "career",
                  unreadOnly: true,
                  selectedId: firstUnreadIdByCategory.career ?? undefined
                })}
                className="status-pill"
              >
                {`キャリア 未読 ${unreadByCategory.career}`}
              </Link>
              <Link
                href={buildNotificationCenterLink({
                  category: "dm",
                  unreadOnly: true,
                  selectedId: firstUnreadIdByCategory.dm ?? undefined
                })}
                className="status-pill"
              >
                {`DM 未読 ${unreadByCategory.dm}`}
              </Link>
              <Link
                href={buildNotificationCenterLink({
                  category: "admin",
                  unreadOnly: true,
                  selectedId: firstUnreadIdByCategory.admin ?? undefined
                })}
                className="status-pill"
              >
                {`運営 未読 ${unreadByCategory.admin}`}
              </Link>
            </div>
          </div>
          <div className="inline-actions">
            <span className="status-pill">{`未読 ${unreadCount} 件`}</span>
            <button type="button" onClick={onMarkAllRead} disabled={busy || unreadCount === 0}>
              すべて既読
            </button>
          </div>
        </div>
      </header>

      <section>
        <h2>配信設定</h2>
        {settings.length === 0 ? (
          <p className="muted">配信設定を読み込み中です。</p>
        ) : (
          <ul className="card-list">
            {settings.map((setting) => {
              const isSaving = savingCategory === setting.category;
              return (
                <li key={setting.category}>
                  <div className="opportunity-head">
                    <strong>{setting.category}</strong>
                    <span className="status-pill">{isSaving ? "保存中..." : "保存済み"}</span>
                  </div>
                  <div className="inline-actions">
                    <label>
                      <input
                        type="checkbox"
                        checked={setting.emailEnabled}
                        disabled={isSaving}
                        onChange={(event) => {
                          onUpdateSetting(setting.category, { emailEnabled: event.target.checked });
                        }}
                      />
                      Email
                    </label>
                    <label>
                      <input
                        type="checkbox"
                        checked={setting.inAppEnabled}
                        disabled={isSaving}
                        onChange={(event) => {
                          onUpdateSetting(setting.category, { inAppEnabled: event.target.checked });
                        }}
                      />
                      In-app
                    </label>
                    <label>
                      <input
                        type="checkbox"
                        checked={setting.pushEnabled}
                        disabled={isSaving}
                        onChange={(event) => {
                          onUpdateSetting(setting.category, { pushEnabled: event.target.checked });
                        }}
                      />
                      Push
                    </label>
                  </div>
                  <p className="muted">
                    {`最終更新: ${setting.updatedAt ? new Date(setting.updatedAt).toLocaleString("ja-JP") : "未設定"}`}
                  </p>
                </li>
              );
            })}
          </ul>
        )}
      </section>

      <section>
        <div className="inline-actions notifications-filter-row">
          {TABS.map((candidate) => (
            <button
              key={candidate.value}
              type="button"
              onClick={() => {
                setLoading(true);
                syncQuery({ tab: candidate.value, selectedId: null });
              }}
              className={tab === candidate.value ? "tab-button tab-button-active" : "tab-button"}
            >
              {candidate.label}
            </button>
          ))}
          <label className="notifications-unread-only">
            <input
              type="checkbox"
              checked={unreadOnly}
              onChange={(event) => {
                setLoading(true);
                syncQuery({ unread: event.target.checked, selectedId: null });
              }}
            />
            未読のみ表示
          </label>
        </div>
        {error ? <p className="error">{error}</p> : null}
      </section>

      <div className="career-layout">
        <section>
          {loading ? (
            <>
              <div className="skeleton" />
              <div className="skeleton" />
              <div className="skeleton" />
            </>
          ) : items.length === 0 ? (
            <EmptyState
              title="通知はありません"
              message="条件に合う通知が見つかりませんでした。カテゴリや未読フィルタを変更してください。"
            />
          ) : (
            <>
              {importantItems.length > 0 ? (
                <>
                  <h3>重要通知</h3>
                  <ul className="card-list">
                    {importantItems.map((item) => {
                      const isSelected = querySelectedId === item.id;
                      return (
                        <li key={item.id} className={isSelected ? "notification-item-selected" : ""}>
                          <div className="opportunity-head">
                            <strong>{item.title}</strong>
                            <span className={item.readAt ? "status-pill" : "status-pill pill-warm"}>
                              {item.readAt ? "既読" : "未読"}
                            </span>
                          </div>
                          <p className="muted">{item.body}</p>
                          <div className="inline-actions">
                            <span className="status-pill pill-warm">重要</span>
                            <button type="button" onClick={() => syncQuery({ selectedId: item.id })}>
                              詳細を見る
                            </button>
                            {!item.readAt ? (
                              <button type="button" onClick={() => onMarkRead(item.id)} disabled={busy}>
                                既読にする
                              </button>
                            ) : null}
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                </>
              ) : null}

              {regularItems.length > 0 ? <h3>通常通知</h3> : null}
              <ul className="card-list">
                {regularItems.map((item) => {
                  const isSelected = querySelectedId === item.id;
                  return (
                    <li key={item.id} className={isSelected ? "notification-item-selected" : ""}>
                      <div className="opportunity-head">
                        <strong>{item.title}</strong>
                        <span className={item.readAt ? "status-pill" : "status-pill pill-warm"}>
                          {item.readAt ? "既読" : "未読"}
                        </span>
                      </div>
                      <p className="muted">{item.body}</p>
                      <div className="inline-actions">
                        <button type="button" onClick={() => syncQuery({ selectedId: item.id })}>
                          詳細を見る
                        </button>
                        {!item.readAt ? (
                          <button type="button" onClick={() => onMarkRead(item.id)} disabled={busy}>
                            既読にする
                          </button>
                        ) : null}
                      </div>
                    </li>
                  );
                })}
              </ul>
            </>
          )}
        </section>

        <aside className="drawer-panel">
          {!selectedItem ? (
            <p className="muted">通知を選択すると詳細が表示されます。</p>
          ) : (
            <>
              <h2>{selectedItem.title}</h2>
              <p className="muted">{selectedItem.body}</p>
              <p className="muted">{`カテゴリ: ${selectedItem.category}`}</p>
              <p className="muted">{`受信: ${new Date(selectedItem.createdAt).toLocaleString("ja-JP")}`}</p>
              <div className="inline-actions">
                <Link href={selectedItem.targetUrl} className="ghost-button">
                  関連画面へ移動
                </Link>
                <button type="button" className="ghost-button" onClick={onCopySelectedNotificationLink}>
                  共有リンクをコピー
                </button>
                {!selectedItem.readAt ? (
                  <button type="button" onClick={() => onMarkRead(selectedItem.id)} disabled={busy}>
                    この通知を既読にする
                  </button>
                ) : null}
              </div>
              {shareFeedback ? <p className="muted">{shareFeedback}</p> : null}
            </>
          )}
        </aside>
      </div>
    </main>
  );
}

export default function NotificationsPage() {
  return (
    <Suspense fallback={<main><section><div className="skeleton" /></section></main>}>
      <NotificationsPageContent />
    </Suspense>
  );
}
