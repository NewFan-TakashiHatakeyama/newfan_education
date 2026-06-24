"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { AppIcon, type AppIconName } from "@/app/components/ui";

import { trackLpEvent } from "@/lib/lp-analytics";

import styles from "./aiFieldReadyLanding.module.css";

type DemoTabId = "issue" | "theme" | "data" | "poc" | "review";

type DemoTab = {
  id: DemoTabId;
  label: string;
  icon: AppIconName;
  title: string;
  description: string;
};

const TABS: DemoTab[] = [
  {
    id: "issue",
    label: "業務課題登録",
    icon: "clipboardList",
    title: "業務課題登録",
    description: "As-Is業務、課題、KPI、関係者、制約を入力し、AI化の前提を整理します。"
  },
  {
    id: "theme",
    label: "AIテーマ化",
    icon: "scanSearch",
    title: "AIテーマ化",
    description: "業務課題をRAG、AI-OCR、データ分析、エージェント、自動化に分類し、PoC候補を選定します。"
  },
  {
    id: "data",
    label: "データ棚卸し",
    icon: "fileSearch",
    title: "データ/ナレッジ棚卸し",
    description: "利用可能データ、文書、アクセス権、品質、更新頻度を整理し、AI活用の準備度を把握します。"
  },
  {
    id: "poc",
    label: "PoC計画",
    icon: "map",
    title: "PoC計画",
    description: "仮説、検証範囲、成功条件、評価指標、体制を設計し、経営判断に使えるPoC計画書を作成します。"
  },
  {
    id: "review",
    label: "成果物レビュー",
    icon: "shieldCheck",
    title: "成果物レビュー",
    description: "AIレビュー、メンターコメント、改善履歴、承認状態を一画面で管理します。"
  }
];

function IssuePanel() {
  return (
    <div className={styles.mockApp}>
      <div className={styles.mockAppToolbar}>
        <span className={styles.mockBreadcrumb}>業務課題 / 新規登録</span>
        <span className={`${styles.mockStatus} ${styles.mockStatusInfo}`}>下書き</span>
      </div>
      <div className={styles.mockForm}>
        <label className={styles.mockField}>
          <span>対象部門</span>
          <div className={styles.mockInput}>カスタマーサポート</div>
        </label>
        <label className={styles.mockField}>
          <span>課題</span>
          <div className={styles.mockInput}>問い合わせ一次回答に時間がかかる</div>
        </label>
        <div className={styles.mockFieldRow}>
          <label className={styles.mockField}>
            <span>現行KPI</span>
            <div className={styles.mockInput}>平均初回回答時間 8時間</div>
          </label>
          <label className={styles.mockField}>
            <span>改善目標</span>
            <div className={styles.mockInput}>初回回答時間を30%削減</div>
          </label>
        </div>
        <div className={styles.mockField}>
          <span>利用可能データ</span>
          <div className={styles.mockChipsRow}>
            <span className={styles.mockChip}>FAQ</span>
            <span className={styles.mockChip}>製品マニュアル</span>
            <span className={styles.mockChip}>問い合わせ履歴</span>
          </div>
        </div>
        <div className={styles.mockField}>
          <span>制約</span>
          <div className={`${styles.mockInput} ${styles.mockInputArea}`}>
            個人情報を含む問い合わせ文の取り扱い。回答根拠の提示が必須。
          </div>
        </div>
      </div>
    </div>
  );
}

function ThemePanel() {
  return (
    <div className={styles.mockApp}>
      <div className={styles.mockAppToolbar}>
        <span className={styles.mockBreadcrumb}>AIテーマ診断 / 課題-CS-001</span>
        <span className={`${styles.mockStatus} ${styles.mockStatusOk}`}>推奨テーマ確定</span>
      </div>
      <div className={styles.mockForm}>
        <div className={styles.mockField}>
          <span>推奨AI活用テーマ</span>
          <div className={styles.mockInput}>RAG / 社内ナレッジ検索</div>
        </div>
        <div className={styles.mockField}>
          <span>理由</span>
          <div className={`${styles.mockInput} ${styles.mockInputArea}`}>
            FAQ・マニュアル・問い合わせ履歴が存在し、回答根拠の提示が重要なため
          </div>
        </div>
        <div className={styles.mockFieldRow}>
          <label className={styles.mockField}>
            <span>PoC候補</span>
            <div className={styles.mockInput}>問い合わせ回答支援AI</div>
          </label>
          <label className={styles.mockField}>
            <span>優先度</span>
            <div className={styles.mockInput}>高（効果大・データ準備済）</div>
          </label>
        </div>
        <div className={styles.mockField}>
          <span>想定成果</span>
          <div className={styles.mockChipsRow}>
            <span className={`${styles.mockChip} ${styles.mockChipRequired}`}>回答作成時間削減</span>
            <span className={styles.mockChip}>回答品質の平準化</span>
            <span className={styles.mockChip}>教育工数削減</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function DataPanel() {
  return (
    <div className={styles.mockApp}>
      <div className={styles.mockAppToolbar}>
        <span className={styles.mockBreadcrumb}>データ/文書棚卸し</span>
        <span className={`${styles.mockStatus} ${styles.mockStatusInfo}`}>3件 要確認</span>
      </div>
      <div className={styles.mockTableScroll}>
        <table className={styles.mockTable}>
          <thead>
            <tr>
              <th>データ/文書</th>
              <th>品質</th>
              <th>権限</th>
              <th>更新頻度</th>
              <th>利用可否</th>
            </tr>
          </thead>
          <tbody>
            {[
              ["FAQ", "良好", "CS全員", "月次", "可"],
              ["製品マニュアル", "良好", "全社", "四半期", "可"],
              ["問い合わせ履歴", "要整理", "CS+情シス", "日次", "要承認"]
            ].map(([name, quality, access, freq, status]) => (
              <tr key={name}>
                <td><strong>{name}</strong></td>
                <td>{quality}</td>
                <td>{access}</td>
                <td>{freq}</td>
                <td>
                  <span className={`${styles.mockStatus} ${status === "可" ? styles.mockStatusOk : styles.mockStatusWarn}`}>
                    {status}
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

function PocPanel() {
  return (
    <div className={styles.mockApp}>
      <div className={styles.mockAppToolbar}>
        <span className={styles.mockBreadcrumb}>PoC計画書 / 問い合わせ回答支援AI</span>
        <span className={`${styles.mockStatus} ${styles.mockStatusInfo}`}>レビュー中</span>
      </div>
      <div className={styles.mockForm}>
        <div className={styles.mockField}>
          <span>検証仮説</span>
          <div className={`${styles.mockInput} ${styles.mockInputArea}`}>
            RAGによる回答ドラフト生成で、初回回答時間を30%削減できる
          </div>
        </div>
        <div className={styles.mockFieldRow}>
          <label className={styles.mockField}>
            <span>成功条件</span>
            <div className={styles.mockInput}>回答作成時間30%削減</div>
          </label>
          <label className={styles.mockField}>
            <span>評価指標</span>
            <div className={styles.mockInput}>根拠提示率90%</div>
          </label>
        </div>
        <div className={styles.mockField}>
          <span>検証範囲</span>
          <div className={styles.mockChipsRow}>
            <span className={styles.mockChip}>対象: 製品問い合わせ</span>
            <span className={styles.mockChip}>期間: 2か月</span>
            <span className={styles.mockChip}>体制: CS3名+DX1名</span>
          </div>
        </div>
        <div className={styles.mockField}>
          <span>リスク</span>
          <div className={`${styles.mockInput} ${styles.mockInputArea}`}>
            個人情報、誤回答、文書更新運用。人間による最終確認を必須とする。
          </div>
        </div>
      </div>
    </div>
  );
}

function ReviewPanel() {
  return (
    <div className={styles.mockApp}>
      <div className={styles.mockAppToolbar}>
        <span className={styles.mockBreadcrumb}>成果物レビュー / PoC計画書</span>
        <span className={`${styles.mockStatus} ${styles.mockStatusOk}`}>メンター承認済</span>
      </div>
      <div className={styles.mockReviewGrid}>
        <div className={styles.mockReviewLeft}>
          <p className={styles.mockSubLabel}>提出物</p>
          <ul className={styles.mockFileList}>
            <li>
              <AppIcon name="fileCheck2" size={14} />
              <span>業務課題定義書 v2</span>
              <span className={`${styles.mockStatus} ${styles.mockStatusOk}`}>承認</span>
            </li>
            <li>
              <AppIcon name="fileCheck2" size={14} />
              <span>データ棚卸し表</span>
              <span className={`${styles.mockStatus} ${styles.mockStatusOk}`}>承認</span>
            </li>
            <li>
              <AppIcon name="notebookText" size={14} />
              <span>PoC計画書 v1</span>
              <span className={`${styles.mockStatus} ${styles.mockStatusInfo}`}>再提出1</span>
            </li>
          </ul>
        </div>
        <div className={styles.mockReviewRight}>
          <p className={styles.mockSubLabel}>AIレビュー</p>
          <article className={`${styles.mockComment} ${styles.mockCommentAi}`}>
            <span className={styles.mockCommentAuthor}>
              <AppIcon name="bot" size={12} />
              AI Reviewer
            </span>
            <p>成功条件と評価指標は明確。リスク欄に個人情報対応を追記すると完成度が向上します。</p>
          </article>
          <p className={styles.mockSubLabel}>メンターレビュー</p>
          <article className={`${styles.mockComment} ${styles.mockCommentMentor}`}>
            <span className={styles.mockCommentAuthor}>
              <AppIcon name="shieldCheck" size={12} />
              メンター・T.K.
            </span>
            <p>経営提案に使える水準。PoC候補として承認。次は実装ロードマップの作成へ。</p>
            <span className={`${styles.mockStatus} ${styles.mockStatusOk}`}>承認 → PoC候補</span>
          </article>
        </div>
      </div>
    </div>
  );
}

function renderPanel(tab: DemoTabId) {
  switch (tab) {
    case "issue":
      return <IssuePanel />;
    case "theme":
      return <ThemePanel />;
    case "data":
      return <DataPanel />;
    case "poc":
      return <PocPanel />;
    case "review":
      return <ReviewPanel />;
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
    if (!root) return;
    const activeButton = root.querySelector<HTMLButtonElement>(`button[data-tab-id="${active}"]`);
    if (!activeButton) return;
    const rootRect = root.getBoundingClientRect();
    const buttonRect = activeButton.getBoundingClientRect();
    setIndicator({ left: buttonRect.left - rootRect.left, width: buttonRect.width });
  }, [active]);

  const handleSelect = (id: DemoTabId) => {
    if (id === active) return;
    setActive(id);
    trackLpEvent("program_demo_tab_changed", { tab: id });
  };

  return (
    <div className={styles.demoSection}>
      <div ref={tabListRef} className={styles.tabList} role="tablist" aria-label="Program Demo">
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
          <p className={styles.tabEyebrow}>Program Demo</p>
          <h3>{activeTab.title}</h3>
          <p>{activeTab.description}</p>
        </div>
        <div className={styles.tabPanelVisual}>{renderPanel(activeTab.id)}</div>
      </article>
    </div>
  );
}
