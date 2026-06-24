"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import type { AuthSession, Role } from "@newfan/contracts";

import { clearDemoAuthSession } from "@/lib/auth";
import { signOutSession } from "@/lib/api";

const SETTINGS_PATH_BY_ROLE: Partial<Record<Role, string>> = {
  recruiter: "/company/settings",
  admin: "/company/settings",
  learner: "/settings/consents",
  mentor: "/settings/consents",
  content_editor: "/company/settings"
};

function getSettingsPath(role: Role): string {
  return SETTINGS_PATH_BY_ROLE[role] ?? "/settings/consents";
}

type UserMenuProps = {
  session: AuthSession;
};

export function UserMenu({ session }: UserMenuProps) {
  const router = useRouter();
  const menuRef = useRef<HTMLDivElement>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [isSigningOut, setIsSigningOut] = useState(false);

  const displayLabel = session.displayName?.trim() || session.userId;
  const settingsPath = getSettingsPath(session.role);

  useEffect(() => {
    if (!isOpen) {
      return;
    }
    function handlePointerDown(event: MouseEvent) {
      if (!menuRef.current?.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [isOpen]);

  async function handleSignOut() {
    setIsSigningOut(true);
    setIsOpen(false);
    try {
      await signOutSession();
    } catch {
      // Clear local session even when the API call fails (e.g. expired token).
    } finally {
      clearDemoAuthSession();
      setIsSigningOut(false);
      router.replace("/auth/sign-in");
    }
  }

  return (
    <div className="user-menu" ref={menuRef}>
      <button
        type="button"
        className="ghost-button user-menu-trigger"
        aria-expanded={isOpen}
        aria-haspopup="menu"
        onClick={() => {
          setIsOpen((current) => !current);
        }}
        disabled={isSigningOut}
      >
        <span aria-hidden>👤</span>
        {`${displayLabel} · ${session.role}`}
      </button>
      {isOpen ? (
        <div className="user-menu-panel" role="menu" aria-label="ユーザーメニュー">
          <p className="user-menu-heading muted">
            {displayLabel}
            <span className="user-menu-role">{session.role}</span>
          </p>
          <Link
            href={settingsPath}
            className="user-menu-item"
            role="menuitem"
            onClick={() => {
              setIsOpen(false);
            }}
          >
            設定
          </Link>
          <Link
            href="/settings/consents"
            className="user-menu-item"
            role="menuitem"
            onClick={() => {
              setIsOpen(false);
            }}
          >
            同意管理
          </Link>
          <button
            type="button"
            className="user-menu-item user-menu-item-danger"
            role="menuitem"
            disabled={isSigningOut}
            onClick={() => {
              void handleSignOut();
            }}
          >
            {isSigningOut ? "サインアウト中..." : "サインアウト"}
          </button>
        </div>
      ) : null}
    </div>
  );
}
