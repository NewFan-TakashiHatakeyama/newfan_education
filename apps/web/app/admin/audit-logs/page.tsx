"use client";

import Link from "next/link";
import { Suspense, useCallback, useEffect, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import type { AuditLogEvent } from "@newfan/contracts";
import { getAdminAuditLogs } from "@/lib/api";

const EVENT_TYPE_OPTIONS = [
  "",
  "admin.company.updated",
  "admin.moderation.updated",
  "application.state.updated",
  "admin.user.updated",
  "public_profile_setting.updated",
  "admin.message_template.create",
  "admin.message_template.update",
  "admin.message_template.delete"
] as const;

function AdminAuditLogsPageContent() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [items, setItems] = useState<AuditLogEvent[]>([]);
  const [limit, setLimit] = useState(Number(searchParams.get("limit") ?? "100"));
  const [eventType, setEventType] = useState(searchParams.get("eventType") ?? "");
  const [actorUserId, setActorUserId] = useState(searchParams.get("actorUserId") ?? "");
  const [resourceType, setResourceType] = useState(searchParams.get("resourceType") ?? "");
  const [resourceId, setResourceId] = useState(searchParams.get("resourceId") ?? "");
  const [occurredFrom, setOccurredFrom] = useState(searchParams.get("occurredFrom") ?? "");
  const [occurredTo, setOccurredTo] = useState(searchParams.get("occurredTo") ?? "");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const syncQuery = useCallback(() => {
    const params = new URLSearchParams();
    params.set("limit", String(limit));
    if (eventType.trim()) {
      params.set("eventType", eventType.trim());
    }
    if (actorUserId.trim()) {
      params.set("actorUserId", actorUserId.trim());
    }
    if (resourceType.trim()) {
      params.set("resourceType", resourceType.trim());
    }
    if (resourceId.trim()) {
      params.set("resourceId", resourceId.trim());
    }
    if (occurredFrom) {
      params.set("occurredFrom", occurredFrom);
    }
    if (occurredTo) {
      params.set("occurredTo", occurredTo);
    }
    const query = params.toString();
    router.replace(`${pathname}${query ? `?${query}` : ""}`);
  }, [actorUserId, eventType, limit, occurredFrom, occurredTo, pathname, resourceId, resourceType, router]);

  async function load(showLoading = true) {
    if (showLoading) {
      setLoading(true);
    }
    setError(null);
    try {
      const response = await getAdminAuditLogs({
        limit,
        eventType: eventType || undefined,
        actorUserId: actorUserId || undefined,
        resourceType: resourceType || undefined,
        resourceId: resourceId || undefined,
        occurredFrom: occurredFrom || undefined,
        occurredTo: occurredTo || undefined
      });
      setItems(response.items);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "監査ログ取得に失敗しました");
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  }

  useEffect(() => {
    syncQuery();
    let active = true;
    getAdminAuditLogs({
      limit,
      eventType: eventType || undefined,
      actorUserId: actorUserId || undefined,
      resourceType: resourceType || undefined,
      resourceId: resourceId || undefined,
      occurredFrom: occurredFrom || undefined,
      occurredTo: occurredTo || undefined
    })
      .then((response) => {
        if (active) {
          setError(null);
          setItems(response.items);
        }
      })
      .catch((loadError) => {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : "監査ログ取得に失敗しました");
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
  }, [actorUserId, eventType, limit, occurredFrom, occurredTo, resourceId, resourceType, syncQuery]);

  return (
    <main>
      <header className="page-header">
        <h1>グローバル監査ログ</h1>
        <p className="muted">テンプレート更新・ユーザー管理・公開設定変更を横断で確認します。</p>
      </header>
      {error ? <p className="error">{error}</p> : null}

      <section>
        <div className="inline-actions">
          <label htmlFor="audit-event-type">イベント種別</label>
          <select
            id="audit-event-type"
            value={eventType}
            onChange={(event) => {
              setLoading(true);
              setEventType(event.target.value);
            }}
          >
            {EVENT_TYPE_OPTIONS.map((value) => (
              <option key={value || "all"} value={value}>
                {value || "すべて"}
              </option>
            ))}
          </select>
          <label htmlFor="audit-actor-user-id">実行ユーザーID</label>
          <input
            id="audit-actor-user-id"
            value={actorUserId}
            onChange={(event) => {
              setLoading(true);
              setActorUserId(event.target.value);
            }}
            placeholder="actor user id"
          />
          <label htmlFor="audit-occurred-from">開始日時</label>
          <input
            id="audit-occurred-from"
            type="datetime-local"
            value={occurredFrom}
            onChange={(event) => {
              setLoading(true);
              setOccurredFrom(event.target.value);
            }}
          />
          <label htmlFor="audit-occurred-to">終了日時</label>
          <input
            id="audit-occurred-to"
            type="datetime-local"
            value={occurredTo}
            onChange={(event) => {
              setLoading(true);
              setOccurredTo(event.target.value);
            }}
          />
          <label htmlFor="audit-resource-type">resource type</label>
          <input
            id="audit-resource-type"
            value={resourceType}
            onChange={(event) => {
              setLoading(true);
              setResourceType(event.target.value);
            }}
            placeholder="resource type"
          />
          <label htmlFor="audit-resource-id">resource id</label>
          <input
            id="audit-resource-id"
            value={resourceId}
            onChange={(event) => {
              setLoading(true);
              setResourceId(event.target.value);
            }}
            placeholder="resource id"
          />
          <label htmlFor="audit-limit">表示件数</label>
          <select id="audit-limit" value={limit} onChange={(event) => { setLoading(true); setLimit(Number(event.target.value)); }}>
            <option value={20}>20</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
            <option value={200}>200</option>
          </select>
          <button type="button" onClick={() => void load()}>再読み込み</button>
          <Link href="/admin/notification-templates/audit-logs">テンプレート監査ログへ</Link>
        </div>
      </section>

      <section>
        {loading ? (
          <>
            <div className="skeleton" />
            <div className="skeleton" />
            <div className="skeleton" />
          </>
        ) : items.length === 0 ? (
          <p className="muted">監査ログがありません。</p>
        ) : (
          <ul className="card-list">
            {items.map((item) => (
              <li key={item.id}>
                <div className="opportunity-head">
                  <strong>{item.summary}</strong>
                  <span className="status-pill">{item.action}</span>
                </div>
                <p className="muted">{`eventType: ${item.eventType}`}</p>
                <p className="muted">{`resource: ${item.resourceType}/${item.resourceId}`}</p>
                <p className="muted">{`actor: ${item.actorUserId} (${item.actorRole})`}</p>
                <p className="muted">{`metadata: ${JSON.stringify(item.metadata)}`}</p>
                <p className="muted">{`occurredAt: ${new Date(item.occurredAt).toLocaleString("ja-JP")}`}</p>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}

export default function AdminAuditLogsPage() {
  return (
    <Suspense fallback={<main><section><div className="skeleton" /></section></main>}>
      <AdminAuditLogsPageContent />
    </Suspense>
  );
}
