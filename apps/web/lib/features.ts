"use client";

/**
 * テナント単位の機能フラグ。
 *
 * サーバ側 `VENTURE_LEDGER_TENANTS`（infrastructure/settings.py）と同じ値を持たせる。
 * 判定の正はAPI側で、ここは押せないメニューを出さないためのもの。
 */
const DEFAULT_VENTURE_LEDGER_TENANTS = "company-demo";

function ventureLedgerTenants(): string[] {
  const raw =
    process.env.NEXT_PUBLIC_VENTURE_LEDGER_TENANTS ?? DEFAULT_VENTURE_LEDGER_TENANTS;
  return raw
    .split(",")
    .map((tenant) => tenant.trim())
    .filter(Boolean);
}

/** 事業PJ台帳が使えるテナントか。工程マスタは自社の工程定義そのものなので限定する。 */
export function isVentureLedgerEnabled(tenantId: string): boolean {
  return ventureLedgerTenants().includes(tenantId);
}
