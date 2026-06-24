import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import {
  BarChart3,
  BookOpen,
  Bot,
  Briefcase,
  Building2,
  CalendarDays,
  ChartNoAxesCombined,
  CheckCircle2,
  CircleAlert,
  CircleDashed,
  ArrowRight,
  ClipboardCheck,
  ClipboardList,
  Clock3,
  FileCheck2,
  FileCode2,
  FileSearch,
  Flag,
  Funnel,
  Gauge,
  GraduationCap,
  LayoutDashboard,
  Lightbulb,
  ListFilter,
  Map,
  MessageSquare,
  NotebookText,
  Rocket,
  ScanSearch,
  Search,
  Send,
  ShieldCheck,
  Sparkles,
  Target,
  UserRound,
  Users
} from "lucide-react";

import styles from "./ui.module.css";

export type AppIconName =
  | "sparkles"
  | "target"
  | "fileSearch"
  | "building2"
  | "users"
  | "gauge"
  | "checkCircle2"
  | "clock3"
  | "circleAlert"
  | "listFilter"
  | "search"
  | "briefcase"
  | "graduationCap"
  | "layoutDashboard"
  | "map"
  | "clipboardList"
  | "barChart3"
  | "notebookText"
  | "bot"
  | "fileCheck2"
  | "send"
  | "shieldCheck"
  | "messageSquare"
  | "bookOpen"
  | "flag"
  | "funnel"
  | "userRound"
  | "chart"
  | "rocket"
  | "calendarDays"
  | "scanSearch"
  | "fileCode2"
  | "lightbulb"
  | "circleDashed"
  | "clipboardCheck"
  | "arrowRight";

const ICONS: Record<AppIconName, LucideIcon> = {
  sparkles: Sparkles,
  target: Target,
  fileSearch: FileSearch,
  building2: Building2,
  users: Users,
  gauge: Gauge,
  checkCircle2: CheckCircle2,
  clock3: Clock3,
  circleAlert: CircleAlert,
  listFilter: ListFilter,
  search: Search,
  briefcase: Briefcase,
  graduationCap: GraduationCap,
  layoutDashboard: LayoutDashboard,
  map: Map,
  clipboardList: ClipboardList,
  barChart3: BarChart3,
  notebookText: NotebookText,
  bot: Bot,
  fileCheck2: FileCheck2,
  send: Send,
  shieldCheck: ShieldCheck,
  messageSquare: MessageSquare,
  bookOpen: BookOpen,
  flag: Flag,
  funnel: Funnel,
  userRound: UserRound,
  chart: ChartNoAxesCombined,
  rocket: Rocket,
  calendarDays: CalendarDays,
  scanSearch: ScanSearch,
  fileCode2: FileCode2,
  lightbulb: Lightbulb,
  circleDashed: CircleDashed,
  clipboardCheck: ClipboardCheck,
  arrowRight: ArrowRight
};

export function AppIcon({
  name,
  className,
  size = 16
}: {
  name: AppIconName;
  className?: string;
  size?: number;
}) {
  const Icon = ICONS[name];
  return <Icon size={size} aria-hidden focusable={false} className={className} />;
}

export function IconText({
  icon,
  children,
  className
}: {
  icon: AppIconName;
  children: ReactNode;
  className?: string;
}) {
  return (
    <span className={`${styles.iconText} ${className ?? ""}`.trim()}>
      <AppIcon name={icon} className={styles.iconInline} />
      <span>{children}</span>
    </span>
  );
}

function includesAny(text: string, keywords: string[]): boolean {
  return keywords.some((keyword) => text.includes(keyword));
}

export function resolveIconByText(text: string): AppIconName {
  const normalized = text.toLowerCase();
  if (includesAny(normalized, ["ダッシュボード", "dashboard", "ホーム", "hero"])) return "layoutDashboard";
  if (includesAny(normalized, ["要件", "requirement", "課題"])) return "clipboardList";
  if (includesAny(normalized, ["社内人材", "受講者", "learner", "ユーザー"])) return "users";
  if (includesAny(normalized, ["進捗", "達成", "completion", "到達"])) return "gauge";
  if (includesAny(normalized, ["レビュー待ち", "pending"])) return "clock3";
  if (includesAny(normalized, ["レビュー", "review", "評価"])) return "checkCircle2";
  if (includesAny(normalized, ["成果物", "証跡", "evidence", "提出"])) return "fileCheck2";
  if (includesAny(normalized, ["ロール", "role"])) return "target";
  if (includesAny(normalized, ["フィルタ", "絞り込み", "filter"])) return "listFilter";
  if (includesAny(normalized, ["検索", "search", "キーワード"])) return "search";
  if (includesAny(normalized, ["経営", "部門", "提案", "report", "サマリー"])) return "barChart3";
  if (includesAny(normalized, ["ロードマップ", "roadmap"])) return "map";
  if (includesAny(normalized, ["学習", "演習", "教材", "learn"])) return "bookOpen";
  if (includesAny(normalized, ["企業", "company", "b2b"])) return "building2";
  if (includesAny(normalized, ["メンター", "mentor"])) return "shieldCheck";
  if (includesAny(normalized, ["通知", "notification"])) return "messageSquare";
  if (includesAny(normalized, ["ステータス", "状態", "status"])) return "flag";
  if (includesAny(normalized, ["コード", "exercise"])) return "fileCode2";
  if (includesAny(normalized, ["履歴", "history"])) return "calendarDays";
  if (includesAny(normalized, ["プラン", "plan"])) return "rocket";
  if (includesAny(normalized, ["スキル", "skill"])) return "scanSearch";
  if (includesAny(normalized, ["空", "なし", "未"])) return "circleDashed";
  return "sparkles";
}
