/** 12-week AI Field Ready Enterprise curriculum — slugs align with MDX frontmatter and dependencies.py */
export type EnterpriseCurriculumWeek = {
  week: number;
  curriculumSlug: string;
  title: string;
  phase: string;
  deliverable: string;
  estimatedMinutes?: number;
};

export type EnterpriseCommonModule = {
  moduleCode: string;
  curriculumSlug: string;
  title: string;
  deliverable: string;
  estimatedMinutes?: number;
};

export const ENTERPRISE_CURRICULUM_WEEKS: EnterpriseCurriculumWeek[] = [
  {
    week: 1,
    curriculumSlug: "afr-enterprise-ai-dx-foundation",
    title: "AI/DX全体像と業務活用パターン",
    phase: "AI/DX共通基礎",
    deliverable: "AI活用アイデアシート",
    estimatedMinutes: 60
  },
  {
    week: 2,
    curriculumSlug: "afr-enterprise-business-issue-definition",
    title: "業務課題定義",
    phase: "業務課題定義",
    deliverable: "業務課題定義書",
    estimatedMinutes: 90
  },
  {
    week: 3,
    curriculumSlug: "afr-enterprise-ai-theme-design",
    title: "AIテーマ化と優先度設計",
    phase: "AIテーマ化",
    deliverable: "AIテーマ候補リスト",
    estimatedMinutes: 90
  },
  {
    week: 4,
    curriculumSlug: "afr-enterprise-data-inventory",
    title: "データ/ナレッジ棚卸し",
    phase: "データ/ナレッジ整理",
    deliverable: "データ/文書棚卸し表",
    estimatedMinutes: 75
  },
  {
    week: 5,
    curriculumSlug: "afr-enterprise-rag-verification",
    title: "RAG/ナレッジ活用",
    phase: "ロール別実務演習",
    deliverable: "RAG検証計画",
    estimatedMinutes: 90
  },
  {
    week: 6,
    curriculumSlug: "afr-enterprise-data-analysis-report",
    title: "データ分析/BI",
    phase: "ロール別実務演習",
    deliverable: "分析レポート",
    estimatedMinutes: 90
  },
  {
    week: 7,
    curriculumSlug: "afr-enterprise-ocr-verification",
    title: "AI-OCR/文書処理",
    phase: "ロール別実務演習",
    deliverable: "OCR/文書処理検証レポート",
    estimatedMinutes: 90
  },
  {
    week: 8,
    curriculumSlug: "afr-enterprise-agent-automation",
    title: "AIエージェント/自動化",
    phase: "ロール別実務演習",
    deliverable: "自動化/エージェント設計書",
    estimatedMinutes: 90
  },
  {
    week: 9,
    curriculumSlug: "afr-enterprise-poc-planning",
    title: "PoC計画",
    phase: "PoC設計",
    deliverable: "PoC計画書",
    estimatedMinutes: 90
  },
  {
    week: 10,
    curriculumSlug: "afr-enterprise-prototype-validation",
    title: "プロトタイプ/検証",
    phase: "プロトタイプ/検証",
    deliverable: "プロトタイプ/検証ログ",
    estimatedMinutes: 120
  },
  {
    week: 11,
    curriculumSlug: "afr-enterprise-evaluation-report",
    title: "評価・リスク整理",
    phase: "評価・改善",
    deliverable: "評価レポート",
    estimatedMinutes: 90
  },
  {
    week: 12,
    curriculumSlug: "afr-enterprise-project-proposal",
    title: "成果発表とAIプロジェクト提案",
    phase: "成果発表/実装計画",
    deliverable: "AIプロジェクト提案書",
    estimatedMinutes: 120
  }
];

/** M05 — common foundation module (design doc §4) */
export const ENTERPRISE_COMMON_MODULES: EnterpriseCommonModule[] = [
  {
    moduleCode: "M05",
    curriculumSlug: "afr-enterprise-ai-governance-foundation",
    title: "AIガバナンス基礎",
    deliverable: "AI利用リスクチェックリスト",
    estimatedMinutes: 75
  }
];

export function enterpriseLessonHref(curriculumSlug: string, lessonSlug = "main"): string {
  return `/learn/${curriculumSlug}/${lessonSlug}`;
}
