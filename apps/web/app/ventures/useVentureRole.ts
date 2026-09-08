"use client";

import { useSyncExternalStore } from "react";

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
  /** 案件の作成・前提の更新・ゲート判断・要員の増減（admin / recruiter） */
  canManage: boolean;
  /** 台帳の記入・適用判定・担当割当・完了承認（admin / recruiter / content_editor） */
  canEdit: boolean;
  /** 到達Lvの記録（admin / recruiter / mentor） */
  canAssess: boolean;
};

function subscribeAuthSession(onChange: () => void) {
  window.addEventListener("newfan-auth-changed", onChange);
  window.addEventListener("storage", onChange);
  return () => {
    window.removeEventListener("newfan-auth-changed", onChange);
    window.removeEventListener("storage", onChange);
  };
}

export function useVentureRole(): VentureCapabilities {
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
  return {
    role,
    userId,
    canManage: role === "admin" || role === "recruiter",
    canEdit: role === "admin" || role === "recruiter" || role === "content_editor",
    canAssess: role === "admin" || role === "recruiter" || role === "mentor"
  };
}
