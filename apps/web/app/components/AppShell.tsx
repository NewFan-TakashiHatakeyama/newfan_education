"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import type { AuthSession, Role } from "@newfan/contracts";

import { AppIcon, type AppIconName } from "@/app/components/ui";
import { getDemoAuthSession, isDemoAuthenticated, isPublicAuthPath } from "@/lib/auth";
import { getMessageThreads, getNotifications } from "@/lib/api";
import { buildMessagesLink } from "@/lib/messageLinks";
import { buildNotificationCenterLink } from "@/lib/notificationLinks";

type NavSection = "company" | "learner" | "mentor" | "common";

type NavItem = {
  href: string;
  label: string;
  section: NavSection;
  icon: AppIconName;
};

const SIDEBAR_COLLAPSE_STORAGE_KEY = "newfan.sidebar.collapsed";

const NAV_ITEMS: NavItem[] = [
  { href: "/company/dashboard", label: "企業サマリー", section: "company", icon: "layoutDashboard" },
  { href: "/company/learners", label: "受講者進捗", section: "company", icon: "users" },
  { href: "/company/roadmaps", label: "育成計画", section: "company", icon: "map" },
  { href: "/company/requirements", label: "案件要件", section: "company", icon: "clipboardList" },
  { href: "/company/fit-assessments", label: "案件適合度の履歴", section: "company", icon: "chart" },
  { href: "/company/evidence", label: "証跡一覧", section: "company", icon: "fileCheck2" },
  { href: "/company/reports", label: "営業提案サマリー", section: "company", icon: "barChart3" },
  { href: "/company/teams", label: "チーム管理", section: "company", icon: "userRound" },
  { href: "/company/settings", label: "企業設定", section: "company", icon: "building2" },
  { href: "/learner/learn", label: "学習ホーム", section: "learner", icon: "bookOpen" },
  { href: "/learner/evidence", label: "自分の証跡", section: "learner", icon: "fileSearch" },
  { href: "/mentor/reviews", label: "レビュー承認 (メンター)", section: "mentor", icon: "shieldCheck" },
  { href: "/notifications", label: "通知一覧", section: "common", icon: "messageSquare" },
  { href: "/admin", label: "管理者ダッシュボード", section: "common", icon: "gauge" },
  { href: "/admin/task-templates", label: "課題テンプレート管理", section: "common", icon: "clipboardCheck" }
];

const SECTION_LABEL: Record<NavSection, string> = {
  company: "企業向け",
  learner: "学習者向け",
  mentor: "メンターメニュー",
  common: "共通機能"
};

const SECTION_ORDER: NavSection[] = ["learner", "company", "mentor", "common"];

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
  const [unreadThreadCount, setUnreadThreadCount] = useState<number>(0);
  const [notificationHref, setNotificationHref] = useState<string>("/notifications");
  const [importantNotificationHref, setImportantNotificationHref] = useState<string>("/notifications?unread=true");
  const [, setMessagesHref] = useState<string>("/messages");
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
    if (!isAuthenticated || !isAuthResolved) {
      return;
    }
    let active = true;
    Promise.all([
      getNotifications({ unread: true }),
      getMessageThreads({ unread: true })
    ])
      .then(([notificationResult, threadResult]) => {
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
          const firstUnreadThread = threadResult.threads[0];
          setUnreadThreadCount(threadResult.threads.length);
          if (firstUnreadThread) {
            setMessagesHref(buildMessagesLink({
              tab: firstUnreadThread.channel,
              unreadOnly: true,
              threadId: firstUnreadThread.id
            }));
          } else {
            setMessagesHref("/messages");
          }
        }
      })
      .catch(() => {
        if (active) {
          setUnreadCount(0);
          setImportantUnreadCount(0);
          setUnreadThreadCount(0);
          setNotificationHref("/notifications");
          setImportantNotificationHref("/notifications?unread=true");
          setMessagesHref("/messages");
        }
      });
    return () => {
      active = false;
    };
  }, [isAuthResolved, isAuthenticated, pathname]);

  const groupedNav: Record<NavSection, NavItem[]> = {
    company: [],
    learner: [],
    mentor: [],
    common: []
  };
  for (const item of NAV_ITEMS) {
    groupedNav[item.section].push(item);
  }

  const visibleUnreadCount = shouldRenderShellChrome ? unreadCount : 0;
  const visibleImportantUnreadCount = shouldRenderShellChrome ? importantUnreadCount : 0;
  const visibleUnreadThreadCount = shouldRenderShellChrome ? unreadThreadCount : 0;
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
            <span className="brand-tag">AI Field Ready</span>
          </Link>
          <input
            aria-label="横断検索"
            placeholder="受講者・教材・証跡・レポートを検索"
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
          {visibleUnreadThreadCount > 0 ? (
            <span className="status-pill status-info" aria-label={`未読スレッド ${visibleUnreadThreadCount} 件`}>
              {`スレッド ${visibleUnreadThreadCount}`}
            </span>
          ) : null}
          <Link href="/auth/sign-in" className="ghost-button">
            <span aria-hidden>👤</span>
            {isAuthenticated ? `${authSession.userId} · ${authSession.role}` : "ログイン"}
          </Link>
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
            {SECTION_ORDER.map((section) => {
              const items = groupedNav[section];
              if (items.length === 0) return null;
              return (
                <div key={section} className="nav-section">
                  <p className="nav-section-label">{SECTION_LABEL[section]}</p>
                  <ul>
                    {items.map((item) => {
                      const active =
                        pathname === item.href ||
                        (item.href !== "/" && pathname.startsWith(`${item.href}/`));
                      return (
                        <li key={item.href}>
                          <Link
                            href={item.href}
                            className={active ? "active-link" : ""}
                            aria-label={isSideNavCollapsed ? item.label : undefined}
                            title={isSideNavCollapsed ? item.label : undefined}
                          >
                            <span className="nav-link-icon" aria-hidden>
                              <AppIcon name={item.icon} size={16} />
                            </span>
                            <span className="nav-link-text">{item.label}</span>
                          </Link>
                        </li>
                      );
                    })}
                  </ul>
                  </div>
              );
            })}
          </nav>
        </aside>
        <div className="content-area">{children}</div>
      </div>
    </div>
  );
}
