"use client";

import { useEffect, useState } from "react";

import { getCompanySettings } from "@/lib/api";

type SettingsPayload = {
  tenantId: string;
  branding: { companyName: string; theme: string };
  notifications: { curriculumUpdate: boolean; reportExport: boolean };
  security: { sessionTtlMinutes: number };
};

export default function CompanySettingsPage() {
  const [settings, setSettings] = useState<SettingsPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getCompanySettings()
      .then((result) => setSettings(result))
      .catch((err) => setError(err instanceof Error ? err.message : "設定の取得に失敗しました"));
  }, []);

  return (
    <main>
      <div className="page-header">
        <h1>企業設定</h1>
        <p className="muted">テナント設定、通知設定、セキュリティ設定を確認します。</p>
      </div>
      {error ? <p className="error">{error}</p> : null}
      {!settings ? (
        <div className="skeleton" />
      ) : (
        <section>
          <ul className="card-list">
            <li>
              <strong>Tenant</strong>
              <p className="muted">{settings.tenantId}</p>
            </li>
            <li>
              <strong>Branding</strong>
              <p className="muted">{settings.branding.companyName}</p>
              <p className="muted">Theme: {settings.branding.theme}</p>
            </li>
            <li>
              <strong>Notifications</strong>
              <p className="muted">Curriculum Update: {settings.notifications.curriculumUpdate ? "ON" : "OFF"}</p>
              <p className="muted">Report Export: {settings.notifications.reportExport ? "ON" : "OFF"}</p>
            </li>
            <li>
              <strong>Security</strong>
              <p className="muted">Session TTL: {settings.security.sessionTtlMinutes} minutes</p>
            </li>
          </ul>
        </section>
      )}
    </main>
  );
}
