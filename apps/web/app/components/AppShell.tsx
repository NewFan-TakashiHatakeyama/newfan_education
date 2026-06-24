"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import type { AuthSession, Role } from "@newfan/contracts";

import { AppIcon, type AppIconName } from "@/app/components/ui";
import { UserMenu } from "@/app/components/UserMenu";
import { getDemoAuthSession, isDemoAuthenticated, isPublicAuthPath } from "@/lib/auth";
import { getNotifications } from "@/lib/api";
import { buildNotificationCenterLink } from "@/lib/notificationLinks";

type NavSection = "company" | "learner" | "mentor" | "common";

type NavLeaf = {
  href: string;
  label: string;
  icon: AppIconName;
};

// A top-level nav entry is either a direct link (leaf) or a collapsible group
// of related links. Grouping keeps each section to a few top-level menus.
type NavEntry =
  | ({ kind: "leaf" } & NavLeaf)
  | { kind: "group"; key: string; label: string; icon: AppIconName; children: NavLeaf[] };

const SIDEBAR_COLLAPSE_STORAGE_KEY = "newfan.sidebar.collapsed";

const NAV_SECTIONS: { section: NavSection; entries: NavEntry[] }[] = [
  {
    section: "learner",
    entries: [
      { kind: "leaf", href: "/learner/learn", label: "学習ホーム", icon: "bookOpen" },
      { kind: "leaf", href: "/courses", label: "コースを探す", icon: "search" },
      { kind: "leaf", href: "/learner/evidence", label: "自分の成果物", icon: "fileSearch" }
    ]
  },
  {
    // 企業向けは9メニューを4つ（ダッシュボード＋3グループ）に集約。
    section: "company",
    entries: [
      { kind: "leaf", href: "/company/dashboard", label: "ダッシュボード", icon: "layoutDashboard" },
      {
        kind: "group",
        key: "company-develop",
        label: "育成管理",
        icon: "graduationCap",
        children: [
          { href: "/company/learners", label: "受講者進捗", icon: "users" },
          { href: "/company/roadmaps", label: "育成ロードマップ", icon: "map" },
          { href: "/company/evidence", label: "成果物一覧", icon: "fileCheck2" }
        ]
      },
      {
        kind: "group",
        key: "company-projects",
        label: "AIプロジェクト",
        icon: "rocket",
        children: [
          { href: "/company/requirements", label: "業務課題", icon: "clipboardList" },
          { href: "/company/fit-assessments", label: "AIテーマ診断", icon: "chart" },
          { href: "/company/reports", label: "AIプロジェクト候補", icon: "barChart3" }
        ]
      },
      {
        kind: "group",
        key: "company-org",
        label: "組織・設定",
        icon: "building2",
        children: [
          { href: "/company/teams", label: "部門管理", icon: "userRound" },
          { href: "/company/settings", label: "企業設定", icon: "building2" }
        ]
      }
    ]
  },
  {
    section: "mentor",
    entries: [
      { kind: "leaf", href: "/mentor/reviews", label: "レビュー承認 (メンター)", icon: "shieldCheck" }
    ]
  },
  {
    section: "common",
    entries: [
      { kind: "leaf", href: "/notifications", label: "通知一覧", icon: "messageSquare" },
      { kind: "leaf", href: "/admin", label: "管理者ダッシュボード", icon: "gauge" },
      { kind: "leaf", href: "/admin/task-templates", label: "課題テンプレート管理", icon: "clipboardCheck" }
    ]
  }
];

const SECTION_LABEL: Record<NavSection, string> = {
  company: "企業向け",
  learner: "学習者向け",
  mentor: "メンターメニュー",
  common: "共通機能"
};

const ROLE_HOME_PATH: Record<Role, string> = {
  learner: "/learner/learn",
  recruiter: "/company/dashboard",
  admin: "/admin",
  content_editor: "/admin/curriculum",
  mentor: "/mentor/reviews"
};

function getDefaultHomePath(session: AuthSession): string {
  return ROLE_HOME_PATH[session.role] ?? "/learner/learn";
}

export function AppShell({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [importantUnreadCount, setImportantUnreadCount] = useState<number>(0);
  const [notificationHref, setNotificationHref] = useState<string>("/notifications");
  const [importantNotificationHref, setImportantNotificationHref] = useState<string>("/notifications?unread=true");
  const [authSession, setAuthSession] = useState<AuthSession>(() => getDemoAuthSession());
  const [isAuthResolved, setIsAuthResolved] = useState<boolean>(false);
  const [isSideNavCollapsed, setIsSideNavCollapsed] = useState<boolean>(() => {
    if (typeof window === "undefined") {
      return false;
    }
    try {
      const savedValue = localStorage.getItem(SIDEBAR_COLLAPSE_STORAGE_KEY);
      return savedValue === "true";
    } catch {
      return false;
    }
  });
  const [openNavGroups, setOpenNavGroups] = useState<Set<string>>(new Set());

  function toggleNavGroup(key: string) {
    setOpenNavGroups((current) => {
      const next = new Set(current);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }

  useEffect(() => {
    try {
      localStorage.setItem(SIDEBAR_COLLAPSE_STORAGE_KEY, String(isSideNavCollapsed));
    } catch {
      // Ignore storage access failures to keep navigation usable.
    }
  }, [isSideNavCollapsed]);

  useEffect(() => {
    const updateAuthState = () => {
      const session = getDemoAuthSession();
      setAuthSession(session);
      setIsAuthResolved(true);
    };
    updateAuthState();
    window.addEventListener("newfan-auth-changed", updateAuthState);
    return () => {
      window.removeEventListener("newfan-auth-changed", updateAuthState);
    };
  }, []);

  const isAuthenticated = isDemoAuthenticated(authSession);
  const isPublicAuthRoute = isPublicAuthPath(pathname);
  const isRootRoute = pathname === "/";
  const shouldRedirectToSignIn = isAuthResolved && !isAuthenticated && !isPublicAuthRoute && !isRootRoute;
  const shouldRedirectToHome = isAuthResolved && isAuthenticated && isPublicAuthRoute;
  const shouldRenderShellChrome = isAuthResolved && isAuthenticated && !isPublicAuthRoute && !isRootRoute;

  useEffect(() => {
    if (!shouldRedirectToHome) {
      return;
    }
    router.replace(getDefaultHomePath(authSession));
  }, [authSession, router, shouldRedirectToHome]);

  useEffect(() => {
    if (!shouldRedirectToSignIn) {
      return;
    }
    router.replace("/auth/sign-in");
  }, [router, shouldRedirectToSignIn]);

  useEffect(() => {
    if (!shouldRenderShellChrome || !isAuthenticated || !isAuthResolved) {
      return;
    }
    let active = true;
    Promise.all([getNotifications({ unread: true })])
      .then(([notificationResult]) => {
        if (active) {
          setUnreadCount(notificationResult.unreadCount);
          setImportantUnreadCount(
            notificationResult.items.filter((item) => item.isImportant).length
          );
          const firstUnread = notificationResult.items[0];
          const firstImportantUnread = notificationResult.items.find((item) => item.isImportant);
          if (firstUnread) {
            setNotificationHref(buildNotificationCenterLink({
              category: firstUnread.category,
              selectedId: firstUnread.id,
              unreadOnly: true
            }));
          } else {
            setNotificationHref("/notifications");
          }
          if (firstImportantUnread) {
            setImportantNotificationHref(buildNotificationCenterLink({
              category: firstImportantUnread.category,
              selectedId: firstImportantUnread.id,
              unreadOnly: true
            }));
          } else {
            setImportantNotificationHref("/notifications?unread=true");
          }
        }
      })
      .catch(() => {
        if (active) {
          setUnreadCount(0);
          setImportantUnreadCount(0);
          setNotificationHref("/notifications");
          setImportantNotificationHref("/notifications?unread=true");
        }
      });
    return () => {
      active = false;
    };
  }, [isAuthResolved, isAuthenticated, pathname, shouldRenderShellChrome]);

  const isLeafActive = (href: string) =>
    pathname === href || (href !== "/" && pathname.startsWith(`${href}/`));

  const visibleUnreadCount = shouldRenderShellChrome ? unreadCount : 0;
  const visibleImportantUnreadCount = shouldRenderShellChrome ? importantUnreadCount : 0;
  const visibleNotificationHref = shouldRenderShellChrome ? notificationHref : "/notifications";
  const visibleImportantNotificationHref = shouldRenderShellChrome
    ? importantNotificationHref
    : "/notifications?unread=true";

  if (!isAuthResolved || shouldRedirectToSignIn || shouldRedirectToHome) {
    return (
      <div className="content-area" style={{ minHeight: "100vh", display: "grid", placeItems: "center" }}>
        <p className="muted">読み込み中...</p>
      </div>
    );
  }

  if (!shouldRenderShellChrome) {
    return <div className="content-area">{children}</div>;
  }

  return (
    <div className="app-shell">
      <header className="top-bar top-bar-glass">
        <div className="top-bar-left">
          <Link href="/" className="brand-link">
            <span className="brand-mark" aria-hidden>
              ▲
            </span>
            <strong>Newfan Education</strong>
            <span className="brand-tag">AI Field Ready Enterprise</span>
          </Link>
          <input
            aria-label="横断検索"
            placeholder="受講者・教材・成果物・AIテーマを検索"
            className="top-search"
          />
        </div>
        <div className="top-bar-right">
          <Link href={visibleNotificationHref} className="ghost-button">
            <span aria-hidden>🔔</span>
            通知
            <span className="badge">{visibleUnreadCount}</span>
          </Link>
          {visibleImportantUnreadCount > 0 ? (
            <Link href={visibleImportantNotificationHref} className="status-pill pill-warm">
              {`重要 ${visibleImportantUnreadCount}`}
            </Link>
          ) : null}
          {isAuthenticated ? (
            <UserMenu session={authSession} />
          ) : (
            <Link href="/auth/sign-in" className="ghost-button">
              <span aria-hidden>👤</span>
              ログイン
            </Link>
          )}
        </div>
      </header>

      <div
        className={`shell-body ${isSideNavCollapsed ? "shell-body-collapsed" : ""}`}
      >
        <aside className={`side-nav ${isSideNavCollapsed ? "side-nav-collapsed" : ""}`}>
          <div className="side-nav-header">
            <button
              type="button"
              className="side-nav-toggle"
              onClick={() => {
                setIsSideNavCollapsed((current) => !current);
              }}
              aria-expanded={!isSideNavCollapsed}
              aria-controls="primary-side-nav"
              aria-label={isSideNavCollapsed ? "サイドバーを展開" : "サイドバーを折りたたむ"}
            >
              <AppIcon name={isSideNavCollapsed ? "arrowRight" : "listFilter"} size={16} />
              <span className="side-nav-toggle-text">{isSideNavCollapsed ? "展開" : "折りたたみ"}</span>
            </button>
          </div>
          <nav id="primary-side-nav" aria-label="メインナビゲーション" className="side-nav-nav">
            {NAV_SECTIONS.map(({ section, entries }) => (
              <div key={section} className="nav-section">
                <p className="nav-section-label">{SECTION_LABEL[section]}</p>
                <ul>
                  {entries.map((entry) => {
                    if (entry.kind === "leaf") {
                      const active = isLeafActive(entry.href);
                      return (
                        <li key={entry.href}>
                          <Link
                            href={entry.href}
                            className={active ? "active-link" : ""}
                            aria-label={isSideNavCollapsed ? entry.label : undefined}
                            title={isSideNavCollapsed ? entry.label : undefined}
                          >
                            <span className="nav-link-icon" aria-hidden>
                              <AppIcon name={entry.icon} size={16} />
                            </span>
                            <span className="nav-link-text">{entry.label}</span>
                          </Link>
                        </li>
                      );
                    }

                    const groupActive = entry.children.some((child) => isLeafActive(child.href));

                    // Collapsed rail: render the group as a single icon linking
                    // to its first child so the rail stays compact.
                    if (isSideNavCollapsed) {
                      const target = entry.children[0]?.href ?? "#";
                      return (
                        <li key={entry.key}>
                          <Link
                            href={target}
                            className={groupActive ? "active-link" : ""}
                            aria-label={entry.label}
                            title={entry.label}
                          >
                            <span className="nav-link-icon" aria-hidden>
                              <AppIcon name={entry.icon} size={16} />
                            </span>
                            <span className="nav-link-text">{entry.label}</span>
                          </Link>
                        </li>
                      );
                    }

                    const open = openNavGroups.has(entry.key) || groupActive;
                    return (
                      <li key={entry.key}>
                        <button
                          type="button"
                          className={`nav-group-toggle ${groupActive ? "nav-group-active" : ""}`}
                          aria-expanded={open}
                          onClick={() => toggleNavGroup(entry.key)}
                        >
                          <span className="nav-link-icon" aria-hidden>
                            <AppIcon name={entry.icon} size={16} />
                          </span>
                          <span className="nav-link-text">{entry.label}</span>
                          <span className={`nav-group-chevron ${open ? "open" : ""}`} aria-hidden>
                            <AppIcon name="arrowRight" size={14} />
                          </span>
                        </button>
                        {open ? (
                          <ul className="nav-group-children">
                            {entry.children.map((child) => {
                              const childActive = isLeafActive(child.href);
                              return (
                                <li key={child.href}>
                                  <Link
                                    href={child.href}
                                    className={`nav-subitem ${childActive ? "active-link" : ""}`}
                                  >
                                    <span className="nav-link-icon" aria-hidden>
                                      <AppIcon name={child.icon} size={15} />
                                    </span>
                                    <span className="nav-link-text">{child.label}</span>
                                  </Link>
                                </li>
                              );
                            })}
                          </ul>
                        ) : null}
                      </li>
                    );
                  })}
                </ul>
              </div>
            ))}
          </nav>
        </aside>
        <div className="content-area">{children}</div>
      </div>
    </div>
  );
}
