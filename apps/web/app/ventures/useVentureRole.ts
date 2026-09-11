"use client";

import { useSyncExternalStore, useEffect, useState } from "react";
import { fetchVenture } from "@/lib/api";
import type { Venture } from "@newfan/contracts";

import type { Role } from "@newfan/contracts";

import { getDemoAuthSession } from "@/lib/auth";

/**
 * 事業PJ台帳の操作権限。サーバ側 `venture_services.py` の役割集合と対応させる。
 * 押せない操作を画面に出さないために使う。
 */
export type VentureCapabilities = {
  /** 役割が確定するまでは null。localStorage 由来なのでサーバ描画時は不明。 */
  role: Role | null;
  /** サインイン中の利用者ID。自己申告の評価を弾くなどに使う。 */
  userId: string;
  /** 案件前提・要員管理：管理者または案件の R01 / R02 / R18。 */
  archived: boolean;
  canManage: boolean;
  /** 案件台帳の記入。完了承認・正本確認には別途責任ロールが必要。 */
  canEdit: boolean;
  /** 到達Lvの記録：管理者または案件の R02 / R19。 */
  canAssess: boolean;
  canVerify: boolean;
  roleIds: string[];
};

function subscribeAuthSession(onChange: () => void) {
  window.addEventListener("newfan-auth-changed", onChange);
  window.addEventListener("storage", onChange);
  return () => {
    window.removeEventListener("newfan-auth-changed", onChange);
    window.removeEventListener("storage", onChange);
  };
}

export function useVentureRole(ventureId?: string): VentureCapabilities {
  const [permissions, setPermissions] = useState<Venture["capabilities"]>();
  // 文字列を返すこと。オブジェクトを返すと毎レンダーで参照が変わって再描画が止まらない。
  const role = useSyncExternalStore(
    subscribeAuthSession,
    () => getDemoAuthSession().role,
    () => null
  );
  const userId = useSyncExternalStore(
    subscribeAuthSession,
    () => getDemoAuthSession().userId,
    () => ""
  );
  useEffect(() => {
    let active = true;
    const refresh = () => {
      if (ventureId) fetchVenture(ventureId).then(v => { if (active) setPermissions(v.capabilities); }).catch(() => { if (active) setPermissions(undefined); });
    };
    refresh();
    window.addEventListener("focus", refresh);
    window.addEventListener("venture-updated", refresh);
    return () => { active = false; window.removeEventListener("focus", refresh); window.removeEventListener("venture-updated", refresh); };
  }, [ventureId, userId, role]);
  return {
    role,
    userId,
    canManage: ventureId ? !!permissions?.canManage : role === "admin" || role === "recruiter",
    canEdit: ventureId ? !!permissions?.canEdit : false,
    canAssess: ventureId ? !!permissions?.canAssess : false,
    canVerify: !!permissions?.canVerify,
    archived: !!permissions?.archived,
    roleIds: permissions?.archived ? [] : permissions?.roleIds ?? []
  };
}
