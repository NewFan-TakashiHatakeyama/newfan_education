"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { AppIcon, type AppIconName } from "@/app/components/ui";

import { trackLpEvent } from "@/lib/lp-analytics";

import styles from "./aiFieldReadyLanding.module.css";

type DemoTabId = "requirements" | "roadmap" | "review" | "report" | "summary";

type DemoTab = {
  id: DemoTabId;
  label: string;
  icon: AppIconName;
  title: string;
  description: string;
};

const TABS: DemoTab[] = [
  {
    id: "requirements",
    label: "案件要件入力",
    icon: "clipboardList",
    title: "案件要件入力",
    description:
      "顧客の必須要件・歓迎要件・現場課題を、提案後に振り返れる形で構造化登録します。"
  },
  {
    id: "roadmap",
    label: "ロードマップ生成",
    icon: "map",
    title: "ロードマップ生成（受講者ごと）",
    description:
      "案件要件から逆算し、受講者ごとに 3 か月の育成ロードマップとロール、評価基準を割り当てます。"
  },
  {
    id: "review",
    label: "演習提出 / レビュー",
    icon: "shieldCheck",
    title: "演習提出 / レビュー",
    description:
      "AI 一次レビューで反応速度を、メンター承認で現場視点の妥当性を担保。再提出と評価観点が一画面で見えます。"
  },
  {
    id: "report",
    label: "実務証跡レポート",
    icon: "fileCheck2",
    title: "実務証跡レポート",
    description:
      "対象者プロフィール、案件適合度、提出物、評価、改善履歴、営業提案サマリーを構造化レポートとして出力します。"
  },
  {
    id: "summary",
    label: "営業提案サマリー",
    icon: "barChart3",
    title: "営業提案サマリー",
    description:
      "営業が顧客に提案する際に必要な、適合度・訴求ポイント・面談想定 Q&A をまとめた営業向けサマリーです。"
  }
];

function RequirementsPanel() {
  return (
    <div className={styles.mockApp}>
      <div className={styles.mockAppToolbar}>
        <span className={styles.mockBreadcrumb}>案件要件 / 新規登録</span>
        <span className={`${styles.mockStatus} ${styles.mockStatusInfo}`}>下書き</span>
      </div>
      <div className={styles.mockForm}>
        <label className={styles.mockField}>
          <span>案件名</span>
          <div className={styles.mockInput}>製造業向け 生成AI業務改善支援 PJ</div>
        </label>
        <div className={styles.mockFieldRow}>
          <label className={styles.mockField}>
            <span>顧客</span>
            <div className={styles.mockInput}>A製造株式会社（既存）</div>
          </label>
          <label className={styles.mockField}>
            <span>期間</span>
            <div className={styles.mockInput}>2026/07 - 2026/12</div>
          </label>
        </div>
        <div className={styles.mockField}>
          <span>必須スキル</span>
          <div className={styles.mockChipsRow}>
            <span className={`${styles.mockChip} ${styles.mockChipRequired}`}>Python（中級）</span>
            <span className={`${styles.mockChip} ${styles.mockChipRequired}`}>SQL（中級）</span>
            <span className={`${styles.mockChip} ${styles.mockChipRequired}`}>プロンプト設計</span>
            <span className={`${styles.mockChip} ${styles.mockChipRequired}`}>業務ヒアリング</span>
          </div>
        </div>
        <div className={styles.mockField}>
          <span>歓迎スキル</span>
          <div className={styles.mockChipsRow}>
            <span className={styles.mockChip}>RAG 評価</span>
            <span className={styles.mockChip}>AI-OCR 検証</span>
            <span className={styles.mockChip}>PMO 補助</span>
          </div>
        </div>
        <div className={styles.mockField}>
          <span>業務課題（顧客ヒアリング）</span>
          <div className={`${styles.mockInput} ${styles.mockInputArea}`}>
            問い合わせ分類の半自動化 / 月次 KPI レポートの自動生成 / 営業資料草案の生成 AI 活用検証。
          </div>
        </div>
      </div>
    </div>
  );
}

function RoadmapPanel() {
  const rows = [
    {
      learner: "K.Y.",
      role: "データ分析補助",
      fit: 78,
      m1: "業務分解 + プロンプト",
      m2: "データ抽出 + 改善提案",
      m3: "提案資料化 + 面談",
      status: { label: "提案候補", tone: "ok" as const }
    },
    {
      learner: "T.A.",
      role: "RAG 検証補助",
      fit: 61,
      m1: "RAG 基礎演習",
      m2: "評価指標設計",
      m3: "顧客報告書化",
      status: { label: "育成中", tone: "info" as const }
    },
    {
      learner: "S.N.",
      role: "Python 自動化補助",
      fit: 42,
      m1: "Python 業務スクリプト",
      m2: "自動化 + 引き継ぎ",
      m3: "案件アサイン保留",
      status: { label: "要補強", tone: "warn" as const }
    }
  ];

  return (
    <div className={styles.mockApp}>
      <div className={styles.mockAppToolbar}>
        <span className={styles.mockBreadcrumb}>育成ロードマップ / 案件A 割当</span>
        <span className={`${styles.mockStatus} ${styles.mockStatusOk}`}>3 名割当済み</span>
      </div>
      <div className={styles.mockTableScroll}>
        <table className={styles.mockTable}>
          <thead>
            <tr>
              <th>受講者</th>
              <th>育成ロール</th>
              <th>適合度</th>
              <th>1 か月目</th>
              <th>2 か月目</th>
              <th>3 か月目</th>
              <th>状態</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.learner}>
                <td>
                  <strong>{row.learner}</strong>
                </td>
                <td>{row.role}</td>
                <td>
                  <span className={styles.mockFitBar}>
                    <span
                      className={styles.mockFitBarFill}
                      style={{ width: `${row.fit}%` }}
                      aria-hidden
                    />
                  </span>
                  <span className={styles.mockFitNumber}>{row.fit}%</span>
                </td>
                <td>{row.m1}</td>
                <td>{row.m2}</td>
                <td>{row.m3}</td>
                <td>
                  <span
                    className={`${styles.mockStatus} ${
                      row.status.tone === "ok"
                        ? styles.mockStatusOk
                        : row.status.tone === "warn"
                          ? styles.mockStatusWarn
                          : styles.mockStatusInfo
                    }`}
                  >
                    {row.status.label}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ReviewPanel() {
  return (
    <div className={styles.mockApp}>
      <div className={styles.mockAppToolbar}>
        <span className={styles.mockBreadcrumb}>演習提出 / 課題: 顧客問い合わせ分類の自動化</span>
        <span className={`${styles.mockStatus} ${styles.mockStatusInfo}`}>再提出 2 回目 / 期限内</span>
      </div>
      <div className={styles.mockReviewGrid}>
        <div className={styles.mockReviewLeft}>
          <p className={styles.mockSubLabel}>提出ファイル</p>
          <ul className={styles.mockFileList}>
            <li>
              <AppIcon name="fileCode2" size={14} />
              <span>classify_tickets.ipynb</span>
              <span className={`${styles.mockStatus} ${styles.mockStatusOk}`}>更新済</span>
            </li>
            <li>
              <AppIcon name="notebookText" size={14} />
              <span>report_v2.md</span>
              <span className={`${styles.mockStatus} ${styles.mockStatusOk}`}>更新済</span>
            </li>
            <li>
              <AppIcon name="fileSearch" size={14} />
              <span>evaluation_log.csv</span>
              <span className={`${styles.mockStatus} ${styles.mockStatusInfo}`}>追加</span>
            </li>
          </ul>
          <p className={styles.mockSubLabel}>評価観点（ルーブリック）</p>
          <div className={styles.mockRubric}>
            <div>
              <span>正確性</span>
              <span className={styles.mockRubricBar}>
                <span style={{ width: "82%" }} />
              </span>
              <strong>82</strong>
            </div>
            <div>
              <span>再現性</span>
              <span className={styles.mockRubricBar}>
                <span style={{ width: "78%" }} />
              </span>
              <strong>78</strong>
            </div>
            <div>
              <span>報告力</span>
              <span className={styles.mockRubricBar}>
                <span style={{ width: "85%" }} />
              </span>
              <strong>85</strong>
            </div>
          </div>
        </div>
        <div className={styles.mockReviewRight}>
          <p className={styles.mockSubLabel}>AIレビュー（一次）</p>
          <article className={`${styles.mockComment} ${styles.mockCommentAi}`}>
            <span className={styles.mockCommentAuthor}>
              <AppIcon name="bot" size={12} />
              AI Reviewer
            </span>
            <p>
              分類精度は十分。改善提案の根拠ログが行単位で揃っており再現性が向上。
              次回は誤分類のサンプル 3 件を report に明記すると提案資料化が容易です。
            </p>
          </article>
          <p className={styles.mockSubLabel}>メンター承認</p>
          <article className={`${styles.mockComment} ${styles.mockCommentMentor}`}>
            <span className={styles.mockCommentAuthor}>
              <AppIcon name="shieldCheck" size={12} />
              メンター・H.M.
            </span>
            <p>
              現場での顧客報告フォーマットに近づきました。証跡化に進めます。
              次月: 営業同席ロールプレイで質疑応答の再現性を確認しましょう。
            </p>
            <span className={`${styles.mockStatus} ${styles.mockStatusOk}`}>承認 → 証跡化</span>
          </article>
        </div>
      </div>
    </div>
  );
}

function ReportPanel() {
  return (
    <div className={styles.mockApp}>
      <div className={styles.mockAppToolbar}>
        <span className={styles.mockBreadcrumb}>実務証跡レポート / EV-2026-0512</span>
        <span className={`${styles.mockStatus} ${styles.mockStatusOk}`}>営業共有可</span>
      </div>
      <div className={styles.mockReport}>
        <header className={styles.mockReportHead}>
          <div>
            <p className={styles.mockReportEyebrow}>Evidence Report</p>
            <h4>K.Y. / データ分析補助</h4>
            <p>育成期間: 2026/02 - 2026/04 ／ 担当メンター: H.M.</p>
          </div>
          <div className={styles.mockReportGrade}>
            <span>総合評価</span>
            <strong>B+</strong>
          </div>
        </header>
        <div className={styles.mockReportFit}>
          <div>
            <span>案件適合度（必須）</span>
            <span className={styles.mockFitBar}>
              <span className={styles.mockFitBarFill} style={{ width: "84%" }} />
            </span>
            <strong>84%</strong>
          </div>
          <div>
            <span>案件適合度（歓迎）</span>
            <span className={styles.mockFitBar}>
              <span className={styles.mockFitBarFill} style={{ width: "72%" }} />
            </span>
            <strong>72%</strong>
          </div>
        </div>
        <div className={styles.mockReportSection}>
          <h5>提案可能タスク</h5>
          <ul>
            <li>顧客問い合わせログのカテゴリ分類と件数集計</li>
            <li>売上データの月次レポート自動化（Python + SQL）</li>
            <li>プロンプト改善案の検証ログ作成と社内共有</li>
          </ul>
        </div>
        <div className={styles.mockReportSection}>
          <h5>改善履歴</h5>
          <ol className={styles.mockTimeline}>
            <li>
              <span>04/05</span>
              <p>AIレビュー: 根拠ログの粒度が粗い → 改善提案</p>
            </li>
            <li>
              <span>04/12</span>
              <p>再提出: 行単位の根拠ログを添付。再現性 70 → 78</p>
            </li>
            <li>
              <span>04/22</span>
              <p>メンター承認: 報告書を顧客提出フォーマットへ整備</p>
            </li>
          </ol>
        </div>
      </div>
    </div>
  );
}

function SummaryPanel() {
  return (
    <div className={styles.mockApp}>
      <div className={styles.mockAppToolbar}>
        <span className={styles.mockBreadcrumb}>営業提案サマリー / 案件A 向け</span>
        <span className={`${styles.mockStatus} ${styles.mockStatusOk}`}>面談前資料</span>
      </div>
      <div className={styles.mockSummary}>
        <div className={styles.mockSummaryHead}>
          <div>
            <p className={styles.mockReportEyebrow}>Sales Summary</p>
            <h4>K.Y. を案件A「生成AI業務改善支援」へ提案</h4>
          </div>
          <div className={styles.mockSummaryFit}>
            <span>必須適合</span>
            <strong>84%</strong>
          </div>
        </div>
        <div className={styles.mockSummarySection}>
          <h5>提案コメント</h5>
          <p>
            業務データの分類と改善提案を、実務演習で 3 回再現済み。
            報告書は顧客提出フォーマットでレビュー通過しており、
            面談初期から提案レベルの会話が可能です。
          </p>
        </div>
        <div className={styles.mockSummarySection}>
          <h5>面談想定 Q&A</h5>
          <div className={styles.mockQa}>
            <article>
              <span>Q.</span>
              <p>AI を使った業務改善の経験はありますか？</p>
            </article>
            <article>
              <span>A.</span>
              <p>
                問い合わせログの分類自動化を、AI レビュー＋メンター承認のもとで 3 度再現しました。
                改善提案の根拠ログを添付しており、運用に乗せる際の論点をそのまま再現できます。
              </p>
            </article>
          </div>
        </div>
        <div className={styles.mockSummaryFooter}>
          <span className={`${styles.mockStatus} ${styles.mockStatusOk}`}>PDF 出力済</span>
          <span className={`${styles.mockStatus} ${styles.mockStatusInfo}`}>共有 URL あり</span>
        </div>
      </div>
    </div>
  );
}

function renderPanel(tab: DemoTabId) {
  switch (tab) {
    case "requirements":
      return <RequirementsPanel />;
    case "roadmap":
      return <RoadmapPanel />;
    case "review":
      return <ReviewPanel />;
    case "report":
      return <ReportPanel />;
    case "summary":
      return <SummaryPanel />;
    default:
      return null;
  }
}

export function ProductDemoTabs({ reducedMotion }: { reducedMotion: boolean }) {
  const [active, setActive] = useState<DemoTabId>(TABS[0].id);
  const tabListRef = useRef<HTMLDivElement | null>(null);
  const [indicator, setIndicator] = useState({ left: 0, width: 0 });

  const activeTab = useMemo(() => TABS.find((tab) => tab.id === active) ?? TABS[0], [active]);

  useEffect(() => {
    const root = tabListRef.current;
    if (!root) {
      return;
    }
    const activeButton = root.querySelector<HTMLButtonElement>(`button[data-tab-id="${active}"]`);
    if (!activeButton) {
      return;
    }
    const rootRect = root.getBoundingClientRect();
    const buttonRect = activeButton.getBoundingClientRect();
    setIndicator({ left: buttonRect.left - rootRect.left, width: buttonRect.width });
  }, [active]);

  const handleSelect = (id: DemoTabId) => {
    if (id === active) {
      return;
    }
    setActive(id);
    trackLpEvent("product_demo_tab_changed", { tab: id });
  };

  return (
    <div className={styles.demoSection}>
      <div ref={tabListRef} className={styles.tabList} role="tablist" aria-label="Product Demo">
        {TABS.map((tab) => {
          const isActive = active === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={isActive}
              aria-controls={`panel-${tab.id}`}
              id={`tab-${tab.id}`}
              data-tab-id={tab.id}
              className={`${styles.tabButton} ${isActive ? styles.tabButtonActive : ""}`}
              onClick={() => handleSelect(tab.id)}
            >
              <AppIcon name={tab.icon} size={14} />
              <span>{tab.label}</span>
            </button>
          );
        })}
        <span
          className={styles.tabIndicator}
          style={{
            width: indicator.width,
            transform: `translateX(${indicator.left}px)`,
            transition: reducedMotion ? "none" : undefined
          }}
          aria-hidden
        />
      </div>

      <article
        key={activeTab.id}
        id={`panel-${activeTab.id}`}
        role="tabpanel"
        aria-labelledby={`tab-${activeTab.id}`}
        className={`${styles.tabPanel} ${reducedMotion ? styles.tabPanelStatic : styles.tabPanelAnimated}`}
      >
        <div className={styles.tabPanelCopy}>
          <p className={styles.tabEyebrow}>Product Demo</p>
          <h3>{activeTab.title}</h3>
          <p>{activeTab.description}</p>
        </div>
        <div className={styles.tabPanelVisual}>{renderPanel(activeTab.id)}</div>
      </article>
    </div>
  );
}
