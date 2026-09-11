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
  getReports,
  downloadReportExport,
  getLearners,
  getRequirements
} from "@/lib/api";

import { PageHero } from "@/app/components/ui/PageHero";
import { Disclosure } from "@/app/components/ui/Disclosure";
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
    getReports().then(result => { if (active) { setHistory(result.items); setReport(result.items[0] ?? null); } }).catch(err => { if (active) setError(err instanceof Error ? err.message : "帳票履歴の取得に失敗しました"); });
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
          : "プロジェクト提案レポートの生成に失敗しました。必要な権限を持つアカウントでサインインしてください。"
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
      await downloadReportExport(job.resultUrl, `${report.id}.${reportFormat}`);
      setExportMessage(`${reportFormat.toUpperCase()}をダウンロードしました。`);
    } catch (err) {
      setExportMessage(err instanceof Error ? err.message : "レポートエクスポートに失敗しました");
    }
  };

  const isLoading = requirements === null || learners === null;

  return (
    <main className={styles.page}>
      <PageHero
        theme="company"
        ariaLabel="プロジェクト提案"
        eyebrow="プロジェクト提案"
        title="プロジェクト提案"
        lead="業務課題と成果物をもとに、提案のたたき台を作成します。"
        metrics={[
          {
            label: "登録済み業務課題",
            value: requirements?.length ?? 0,
            suffix: "件",
            hint: "社内の業務課題数"
          },
          {
            label: "受講者",
            value: learners?.length ?? 0,
            suffix: "名",
            hint: "候補として選択可能"
          },
          {
            label: "保存済みレポート",
            value: history.length,
            suffix: "件",
            hint: "保存した内容と証跡を保持"
          }
        ]}
        actions={
          <>
            <Link href="/company/evidence" className={styles.actionGhost}>
              <IconText icon="fileCheck2">成果物を確認</IconText>
            </Link>
            <Link href="/company/requirements" className={styles.actionGhost}>
              <IconText icon="clipboardList">業務課題を登録</IconText>
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
        title="1. 課題と受講者を選ぶ"
        meta="業務課題と受講者を選んでください。"
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
                  業務課題
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
                    <option value="">(業務課題がありません)</option>
                  ) : null}
                </select>
              </div>
              <div className={styles.field}>
                <label htmlFor="rep-learner" className={styles.fieldLabel}>
                  受講者
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
                    <option value="">(受講者がいません)</option>
                  ) : null}
                </select>
              </div>
            </div>

            <Disclosure title="選択内容を確認">
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
                gap: "0.8rem"
              }}
            >
              {selectedRequirement ? (
                <div className={`${styles.kpiTile} ${styles.kpiTileAccent}`}>
                  <p className={styles.kpiLabel}>選択業務課題</p>
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
                  <p className={styles.kpiLabel}>選択受講者</p>
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

            </Disclosure>
            <div className={styles.actionRow}>
              <button
                type="button"
                className={styles.actionPrimary}
                onClick={handleGenerate}
                disabled={!selectedRequirement || !selectedLearner || submitting}
              >
                {submitting ? "生成中…" : <IconText icon="send">提案を作成</IconText>}
              </button>
            </div>
          </div>
        )}
      </Section>

      <Section
        title="2. 提案を確認・ダウンロード"
        meta="内容を確認してから共有してください。"
        theme="company"
        icon="notebookText"
      >
        {report ? (
          <article
            style={{
              border: "1px solid var(--border)",
              borderRadius: 10,
              background:
                "#ffffff",
              padding: "1.25rem 1.35rem",
              boxShadow: "none",
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
                  <IconText icon="fileCode2">Markdown</IconText>
                </button>
                <button type="button" className={styles.actionGhost} onClick={() => void handleExport("csv")}>
                  <IconText icon="fileCode2">CSVを保存</IconText>
                </button>
                <button type="button" className={styles.actionGhost} onClick={() => void handleExport("pdf")}>
                  <IconText icon="fileCode2">PDFを保存</IconText>
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
              <span>業務課題: {report.requirementId}</span>
              <span>受講者: {report.learnerId}</span>
              <span>生成: {report.generatedAt.slice(0, 19).replace("T", " ")}</span>
            </div>
          </article>
        ) : (
          <EmptyState
            icon={<AppIcon name="circleDashed" size={24} />}
            title="提案は未作成です"
            message="業務課題と受講者を選んで『提案を作成』を押すと、ここに表示されます。"
          />
        )}
      </Section>

      <Section
        title="作成履歴"
        meta="保存した提案を開き直せます。"
        theme="company"
        icon="calendarDays"
      >
        {history.length === 0 ? (
          <EmptyState
            icon={<AppIcon name="circleDashed" size={24} />}
            title="履歴はありません"
            message="まだ生成されたプロジェクト提案レポートはありません。"
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
