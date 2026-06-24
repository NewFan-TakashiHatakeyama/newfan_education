"use client";

import type { AuthSession, Role } from "@newfan/contracts";

const FALLBACK_SESSION: AuthSession = {
  accessToken: "",
  tokenType: "bearer",
  expiresIn: 0,
  userId: "anonymous",
  displayName: "Anonymous",
  role: (process.env.NEXT_PUBLIC_DEMO_USER_ROLE as Role | undefined) ?? "learner",
  state: "invited",
  tenantId: "company-demo"
};

export function getAuthHeaders(): Record<string, string> {
  const session = getDemoAuthSession();
  if (!isDemoAuthenticated(session)) {
    return {};
  }
  return {
    Authorization: `${session.tokenType} ${session.accessToken}`
  };
}

let unauthorizedHandling = false;

/** Clears local session after API 401. Safe to call multiple times. */
export function handleUnauthorizedSession() {
  if (!canUseStorage() || unauthorizedHandling) {
    return;
  }
  const session = getDemoAuthSession();
  if (!isDemoAuthenticated(session)) {
    return;
  }
  unauthorizedHandling = true;
  try {
    clearDemoAuthSession();
  } finally {
    unauthorizedHandling = false;
  }
}

export function getDemoCompanyId(): string {
  const session = getDemoAuthSession();
  return session.tenantId;
}

const ROLE_HOME_PATH: Record<Role, string> = {
  learner: "/learner/learn",
  recruiter: "/company/dashboard",
  admin: "/admin",
  content_editor: "/admin/curriculum",
  mentor: "/mentor/reviews"
};

export function getRoleHomePath(role: Role): string {
  return ROLE_HOME_PATH[role] ?? "/learner/learn";
}

function canUseStorage() {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

export function getDemoAuthSession(): AuthSession {
  if (!canUseStorage()) {
    return FALLBACK_SESSION;
  }
  const raw = window.localStorage.getItem("newfan.auth.session-cache");
  if (!raw) {
    return FALLBACK_SESSION;
  }
  try {
    const parsed = JSON.parse(raw) as AuthSession;
    if (!parsed.userId || !parsed.role || !parsed.tenantId) {
      return FALLBACK_SESSION;
    }
    return parsed;
  } catch {
    return FALLBACK_SESSION;
  }
}

export function isDemoAuthenticated(session: AuthSession): boolean {
  return session.userId !== "anonymous" && session.accessToken.trim().length > 0;
}

const PUBLIC_AUTH_PATHS = ["/auth/sign-in", "/auth/sign-up"] as const;

export function isPublicAuthPath(pathname: string): boolean {
  return PUBLIC_AUTH_PATHS.some((path) => pathname === path || pathname.startsWith(`${path}/`));
}

export function setDemoAuthSession(session: AuthSession) {
  if (!canUseStorage()) {
    return;
  }
  window.localStorage.setItem("newfan.auth.session-cache", JSON.stringify(session));
  window.dispatchEvent(new Event("newfan-auth-changed"));
}

export function clearDemoAuthSession() {
  if (!canUseStorage()) {
    return;
  }
  window.localStorage.removeItem("newfan.auth.session-cache");
  window.dispatchEvent(new Event("newfan-auth-changed"));
}
