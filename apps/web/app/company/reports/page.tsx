"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";

import type {
  LearnerSummary,
  Requirement,
  SalesSummaryReport
} from "@newfan/contracts";

import {
  createSalesSummaryReport,
  exportReport,
  getLearners,
  getRequirements
} from "@/lib/api";

import { PageHero } from "@/app/components/ui/PageHero";
import { Section } from "@/app/components/ui/Section";
import { EmptyState } from "@/app/components/ui/EmptyState";
import { SkeletonRow } from "@/app/components/ui/Skeleton";
import { SkillChipList } from "@/app/components/ui/SkillChip";
import { ReadinessBadge, normalizeReadiness } from "@/app/components/ui/ReadinessBadge";
import { AppIcon, IconText } from "@/app/components/ui/Icon";

import styles from "@/app/components/ui/ui.module.css";

type GeneratedReport = SalesSummaryReport & {
  requirementId: string;
  learnerId: string;
  generatedAt: string;
};

export default function CompanyReportsPage() {
  const [requirements, setRequirements] = useState<Requirement[] | null>(null);
  const [learners, setLearners] = useState<LearnerSummary[] | null>(null);
  const [requirementId, setRequirementId] = useState<string>("");
  const [learnerId, setLearnerId] = useState<string>("");
  const [report, setReport] = useState<GeneratedReport | null>(null);
  const [history, setHistory] = useState<GeneratedReport[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [exportMessage, setExportMessage] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    Promise.allSettled([getRequirements(), getLearners()]).then((results) => {
      if (!active) return;
      const [r, l] = results;
      if (r.status === "fulfilled") {
        setRequirements(r.value.items);
        if (r.value.items[0]) setRequirementId(r.value.items[0].id);
      } else setRequirements([]);
      if (l.status === "fulfilled") {
        setLearners(l.value.items);
        if (l.value.items[0]) setLearnerId(l.value.items[0].id);
      } else setLearners([]);
    });
    return () => {
      active = false;
    };
  }, []);

  const selectedRequirement = useMemo(
    () => (requirements ?? []).find((r) => r.id === requirementId) ?? null,
    [requirements, requirementId]
  );
  const selectedLearner = useMemo(
    () => (learners ?? []).find((l) => l.id === learnerId) ?? null,
    [learners, learnerId]
  );

  const handleGenerate = async () => {
    if (!selectedRequirement || !selectedLearner) return;
    setSubmitting(true);
    setError(null);
    try {
      const result = await createSalesSummaryReport({
        requirementId: selectedRequirement.id,
        learnerId: selectedLearner.id
      });
      const enriched: GeneratedReport = {
        ...result,
        requirementId: selectedRequirement.id,
        learnerId: selectedLearner.id,
        generatedAt: new Date().toISOString()
      };
      setReport(enriched);
      setHistory((prev) => [enriched, ...prev]);
      setCopied(false);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "営業提案サマリーの生成に失敗しました。必要な権限を持つアカウントでサインインしてください。"
      );
    } finally {
      setSubmitting(false);
    }
  };

  const handleCopy = async () => {
    if (!report) return;
    try {
      await navigator.clipboard.writeText(`${report.title}\n\n${report.summary}`);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      setCopied(false);
    }
  };

  const handleDownload = () => {
    if (!report) return;
    const blob = new Blob([`# ${report.title}\n\n${report.summary}\n`], {
      type: "text/markdown"
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${report.id}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleExport = async (reportFormat: "csv" | "pdf") => {
    if (!report) return;
    setExportMessage(null);
    try {
      const job = await exportReport(report.id, reportFormat);
      setExportMessage(`${reportFormat.toUpperCase()} export completed: ${job.resultUrl}`);
    } catch (err) {
      setExportMessage(err instanceof Error ? err.message : "レポートエクスポートに失敗しました");
    }
  };

  const isLoading = requirements === null || learners === null;

  return (
    <main className={styles.page}>
      <PageHero
        theme="company"
        ariaLabel="営業提案サマリー"
        eyebrow="営業提案サマリー"
        title="実務証跡と案件要件から営業提案サマリーを自動生成"
        lead={
          <>
            待機人材の実務証跡と案件要件の適合度をもとに、SES 営業向けの提案資料を自動生成します。
            生成結果はコピー / Markdown ダウンロードで、案件面談・営業提案ですぐ使えます。
          </>
        }
        metrics={[
          {
            label: "登録済み案件要件",
            value: requirements?.length ?? 0,
            suffix: "件",
            hint: "受注案件の要件数"
          },
          {
            label: "待機人材",
            value: learners?.length ?? 0,
            suffix: "名",
            hint: "提案候補として選択可能"
          },
          {
            label: "本セッションで生成",
            value: history.length,
            suffix: "件",
            hint: "リロードで消えます"
          }
        ]}
        actions={
          <>
            <Link href="/company/evidence" className={styles.actionGhost}>
              <IconText icon="fileCheck2">実務証跡を確認</IconText>
            </Link>
            <Link href="/company/requirements" className={styles.actionGhost}>
              <IconText icon="clipboardList">案件要件を登録</IconText>
            </Link>
          </>
        }
      />

      {error ? (
        <div className={styles.section} role="alert">
          <p className="muted" style={{ margin: 0 }}>
            {error}
          </p>
        </div>
      ) : null}
      {exportMessage ? (
        <div className={styles.section}>
          <p className="muted" style={{ margin: 0 }}>
            {exportMessage}
          </p>
        </div>
      ) : null}

      <Section
        title="営業提案サマリーを生成"
        meta="案件要件と待機人材を選び、実務証跡に基づく提案文を確認します。"
        theme="company"
        icon="barChart3"
      >
        {isLoading ? (
          <SkeletonRow widths={["50%", "60%", "55%"]} />
        ) : (
          <div className={styles.formGrid}>
            <div className={styles.formGridTwo}>
              <div className={styles.field}>
                <label htmlFor="rep-req" className={styles.fieldLabel}>
                  案件要件
                </label>
                <select
                  id="rep-req"
                  className={styles.fieldSelect}
                  value={requirementId}
                  onChange={(e) => setRequirementId(e.target.value)}
                >
                  {(requirements ?? []).map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.title}
                    </option>
                  ))}
                  {(requirements ?? []).length === 0 ? (
                    <option value="">(案件要件がありません)</option>
                  ) : null}
                </select>
              </div>
              <div className={styles.field}>
                <label htmlFor="rep-learner" className={styles.fieldLabel}>
                  待機人材
                </label>
                <select
                  id="rep-learner"
                  className={styles.fieldSelect}
                  value={learnerId}
                  onChange={(e) => setLearnerId(e.target.value)}
                >
                  {(learners ?? []).map((l) => (
                    <option key={l.id} value={l.id}>
                      {l.name} — {l.targetRole}
                    </option>
                  ))}
                  {(learners ?? []).length === 0 ? (
                    <option value="">(待機人材がいません)</option>
                  ) : null}
                </select>
              </div>
            </div>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
                gap: "0.8rem"
              }}
            >
              {selectedRequirement ? (
                <div className={`${styles.kpiTile} ${styles.kpiTileAccent}`}>
                  <p className={styles.kpiLabel}>選択案件要件</p>
                  <p
                    style={{
                      margin: "0.2rem 0 0.4rem",
                      fontSize: "1rem",
                      fontWeight: 700,
                      color: "#0f172a"
                    }}
                  >
                    {selectedRequirement.title}
                  </p>
                  <p className={styles.kpiHint}>{selectedRequirement.description}</p>
                  <div style={{ marginTop: "0.5rem" }}>
                    <SkillChipList skills={selectedRequirement.requiredSkills} />
                  </div>
                </div>
              ) : null}
              {selectedLearner ? (
                <div className={`${styles.kpiTile}`}>
                  <p className={styles.kpiLabel}>選択待機人材</p>
                  <p
                    style={{
                      margin: "0.2rem 0 0.4rem",
                      fontSize: "1rem",
                      fontWeight: 700,
                      color: "#0f172a"
                    }}
                  >
                    {selectedLearner.name}
                  </p>
                  <p className={styles.kpiHint}>
                    {selectedLearner.teamName} · {selectedLearner.targetRole} · ロードマップ進捗{" "}
                    {selectedLearner.roadmapCompletionRate ?? 0}%
                  </p>
                  <div
                    style={{
                      marginTop: "0.45rem",
                      display: "flex",
                      gap: "0.4rem",
                      flexWrap: "wrap",
                      alignItems: "center"
                    }}
                  >
                    <ReadinessBadge level={normalizeReadiness(selectedLearner.readiness)} />
                  </div>
                </div>
              ) : null}
            </div>

            <div className={styles.actionRow}>
              <button
                type="button"
                className={styles.actionPrimary}
                onClick={handleGenerate}
                disabled={!selectedRequirement || !selectedLearner || submitting}
              >
                {submitting ? "生成中…" : <IconText icon="send">営業提案サマリーを生成</IconText>}
              </button>
            </div>
          </div>
        )}
      </Section>

      <Section
        title="最新の生成結果"
        meta="案件面談・営業提案でそのままコピー / Markdown としてダウンロードできます。"
        theme="company"
        icon="notebookText"
      >
        {report ? (
          <article
            style={{
              border: "1px solid var(--border)",
              borderRadius: 22,
              background:
                "linear-gradient(180deg, #ffffff 0%, #f5f3ff 100%)",
              padding: "1.25rem 1.35rem",
              boxShadow: "0 18px 36px -22px rgba(79, 70, 229, 0.45)",
              display: "grid",
              gap: "0.7rem"
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "flex-start",
                gap: "0.6rem",
                flexWrap: "wrap"
              }}
            >
              <h3 style={{ margin: 0, fontSize: "1.05rem", color: "#1a21bc" }}>{report.title}</h3>
              <div className={styles.actionRow}>
                <button type="button" className={styles.actionGhost} onClick={handleCopy}>
                  {copied ? "✓ コピー済" : <IconText icon="clipboardList">コピー</IconText>}
                </button>
                <button type="button" className={styles.actionPrimary} onClick={handleDownload}>
                  <IconText icon="fileCode2">Markdown ダウンロード</IconText>
                </button>
                <button type="button" className={styles.actionGhost} onClick={() => void handleExport("csv")}>
                  <IconText icon="fileCode2">CSVエクスポート</IconText>
                </button>
                <button type="button" className={styles.actionGhost} onClick={() => void handleExport("pdf")}>
                  <IconText icon="fileCode2">PDFエクスポート</IconText>
                </button>
              </div>
            </div>
            <p
              style={{
                margin: 0,
                fontSize: 13.5,
                color: "#334466",
                lineHeight: 1.8,
                whiteSpace: "pre-wrap"
              }}
            >
              {report.summary}
            </p>
            <div
              style={{
                fontSize: 12,
                color: "#5d667d",
                display: "flex",
                gap: "0.8rem",
                flexWrap: "wrap"
              }}
            >
              <span>レポートID: {report.id}</span>
              <span>案件: {report.requirementId}</span>
              <span>待機人材: {report.learnerId}</span>
              <span>生成: {report.generatedAt.slice(0, 19).replace("T", " ")}</span>
            </div>
          </article>
        ) : (
          <EmptyState
            icon={<AppIcon name="circleDashed" size={24} />}
            title="まだ生成していません"
            message="案件要件と待機人材を選んで『営業提案サマリーを生成』を押すと、ここに表示されます。"
          />
        )}
      </Section>

      <Section
        title="生成履歴 (本セッション)"
        meta="本セッション内の生成履歴です。ページ再読み込みで消えます。"
        theme="company"
        icon="calendarDays"
      >
        {history.length === 0 ? (
          <EmptyState
            icon={<AppIcon name="circleDashed" size={24} />}
            title="履歴なし"
            message="まだ生成された営業提案サマリーはありません。"
          />
        ) : (
          <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gap: "0.5rem" }}>
            {history.map((h) => (
              <li
                key={h.generatedAt + h.id}
                style={{
                  border: "1px solid var(--border)",
                  borderRadius: 14,
                  padding: "0.7rem 0.95rem",
                  background: "var(--surface)",
                  display: "flex",
                  gap: "0.7rem",
                  flexWrap: "wrap",
                  alignItems: "center"
                }}
              >
                <span className={styles.evidenceMetaLabel}>{h.generatedAt.slice(0, 10)}</span>
                <strong style={{ fontSize: 13 }}>{h.title}</strong>
                <span className={styles.cellNameSub}>{h.id}</span>
                <button
                  type="button"
                  className={styles.actionGhost}
                  style={{ marginLeft: "auto", fontSize: 12 }}
                  onClick={() => {
                    setReport(h);
                    setCopied(false);
                  }}
                >
                  最新欄に表示
                </button>
              </li>
            ))}
          </ul>
        )}
      </Section>
    </main>
  );
}
