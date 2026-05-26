"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";

import type {
  AssignRoadmapResult,
  LearnerSummary,
  RoleTemplate
} from "@newfan/contracts";

import { assignRoadmap, getLearners, getRoleTemplates } from "@/lib/api";

import { PageHero } from "@/app/components/ui/PageHero";
import { Section } from "@/app/components/ui/Section";
import { EmptyState } from "@/app/components/ui/EmptyState";
import { SkeletonRow } from "@/app/components/ui/Skeleton";
import { SkillChipList } from "@/app/components/ui/SkillChip";
import { normalizeReadiness, ReadinessBadge } from "@/app/components/ui/ReadinessBadge";
import { AppIcon, IconText } from "@/app/components/ui/Icon";

import styles from "@/app/components/ui/ui.module.css";

type AssignmentHistoryEntry = {
  id: string;
  templateId: string;
  templateName: string;
  learnerId: string;
  learnerName: string;
  status: string;
  at: string;
};

export default function CompanyRoadmapsPage() {
  const [templates, setTemplates] = useState<RoleTemplate[] | null>(null);
  const [learners, setLearners] = useState<LearnerSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);
  const [selectedLearnerId, setSelectedLearnerId] = useState<string | null>(null);
  const [history, setHistory] = useState<AssignmentHistoryEntry[]>([]);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let active = true;
    Promise.allSettled([getRoleTemplates(), getLearners()]).then((results) => {
      if (!active) return;
      const [t, l] = results;
      if (t.status === "fulfilled") {
        setTemplates(t.value.items);
        if (t.value.items[0]) setSelectedTemplateId(t.value.items[0].id);
      } else {
        setTemplates([]);
        setError("ロールテンプレートを取得できませんでした。必要な権限を持つアカウントでサインインして再読み込みしてください。");
      }
      if (l.status === "fulfilled") {
        setLearners(l.value.items);
        if (l.value.items[0]) setSelectedLearnerId(l.value.items[0].id);
      } else {
        setLearners([]);
      }
    });
    return () => {
      active = false;
    };
  }, []);

  const selectedTemplate = useMemo(
    () => (templates ?? []).find((t) => t.id === selectedTemplateId) ?? null,
    [templates, selectedTemplateId]
  );

  const selectedLearner = useMemo(
    () => (learners ?? []).find((l) => l.id === selectedLearnerId) ?? null,
    [learners, selectedLearnerId]
  );

  const handleAssign = async () => {
    if (!selectedTemplate || !selectedLearner) return;
    setSubmitting(true);
    setError(null);
    try {
      const result: AssignRoadmapResult = await assignRoadmap({
        learnerId: selectedLearner.id,
        roleTemplateId: selectedTemplate.id
      });
      setHistory((prev) => [
        {
          id: result.roadmapId,
          templateId: selectedTemplate.id,
          templateName: selectedTemplate.name,
          learnerId: selectedLearner.id,
          learnerName: selectedLearner.name,
          status: result.status,
          at: new Date().toISOString()
        },
        ...prev
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "育成ロードマップの割当に失敗しました。");
    } finally {
      setSubmitting(false);
    }
  };

  const isLoading = templates === null;

  return (
    <main className={styles.page}>
      <PageHero
        theme="company"
        ariaLabel="ロードマップ割当"
        eyebrow="ロードマップ割当"
        title="待機人材へ、案件要件から逆算した育成ロードマップを割り当てる"
        lead={
          <>
            AI/DXロール別テンプレを選び、待機人材へ案件に近づく育成タスクを割り当てます。
            案件で求められるスキルを30〜90分のスモールタスクに分解し、実務証跡の蓄積と配属準備度の向上につなげます。
          </>
        }
        metrics={[
          {
            label: "ロールテンプレート",
            value: templates?.length ?? 0,
            suffix: "種",
            hint: "AI/DXロール別の育成テンプレ"
          },
          {
            label: "待機人材",
            value: learners?.length ?? 0,
            suffix: "名",
            hint: "待機人材一覧と同期"
          },
          {
            label: "本セッションの割当",
            value: history.length,
            suffix: "件",
            hint: "再読み込みで消えます"
          }
        ]}
        actions={
          <>
            <Link href="/company/learners" className={styles.actionGhost}>
              <IconText icon="users">待機人材一覧へ</IconText>
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

      <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1.2fr) minmax(0, 1fr)", gap: "1rem" }}>
        <Section
          title="ロールテンプレートを選ぶ"
          meta="AI/DXロール別に、案件適合に必要なスキルと育成タスクが定義済みです。"
          theme="company"
          icon="target"
        >
          {isLoading ? (
            <SkeletonRow widths={["70%", "50%", "60%"]} />
          ) : (templates ?? []).length === 0 ? (
            <EmptyState
              icon={<AppIcon name="circleDashed" size={24} />}
              title="ロールテンプレートを取得できません"
              message="必要な権限を持つアカウントでサインインしてください。"
              action={
                <Link href="/auth/sign-in" className={styles.actionPrimary}>
                  <IconText icon="userRound">サインインを開く</IconText>
                </Link>
              }
            />
          ) : (
            <div style={{ display: "grid", gap: "0.7rem" }}>
              {(templates ?? []).map((t) => {
                const active = t.id === selectedTemplateId;
                return (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => setSelectedTemplateId(t.id)}
                    aria-pressed={active}
                    style={{
                      textAlign: "left",
                      border: `1px solid ${active ? "#4f46e5" : "var(--border)"}`,
                      borderRadius: 18,
                      background: active
                        ? "linear-gradient(180deg, #f5f3ff 0%, #eef2ff 100%)"
                        : "var(--surface)",
                      padding: "0.95rem 1.1rem",
                      cursor: "pointer",
                      transition: "all 0.18s ease",
                      display: "grid",
                      gap: "0.4rem",
                      boxShadow: active
                        ? "0 10px 24px -16px rgba(79, 70, 229, 0.55)"
                        : "0 8px 22px -22px rgba(26, 33, 188, 0.25)"
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        gap: "0.5rem",
                        flexWrap: "wrap"
                      }}
                    >
                      <strong style={{ fontSize: 15, color: "#0f172a" }}>{t.name}</strong>
                      <span className={styles.evidenceMetaLabel}>{t.code}</span>
                    </div>
                    <p style={{ margin: 0, fontSize: 13, color: "#475569", lineHeight: 1.6 }}>
                      {t.description}
                    </p>
                    <SkillChipList skills={t.targetSkills} />
                  </button>
                );
              })}
            </div>
          )}
        </Section>

        <Section
          title="待機人材に割り当てる"
          meta="選択したテンプレの育成タスクを待機人材へ割当。割当履歴はこのセッション中のみ保持されます。"
          theme="company"
          icon="users"
        >
          {(learners ?? []).length === 0 ? (
            <EmptyState
              icon={<AppIcon name="circleDashed" size={24} />}
              title="待機人材がまだ登録されていません"
              message="待機人材一覧から登録・招待してください。"
              action={
                <Link href="/company/learners" className={styles.actionGhost}>
                  <IconText icon="users">待機人材一覧へ</IconText>
                </Link>
              }
            />
          ) : (
            <>
              <div className={styles.field}>
                <label htmlFor="assign-learner" className={styles.fieldLabel}>
                  割当対象の待機人材
                </label>
                <select
                  id="assign-learner"
                  className={styles.fieldSelect}
                  value={selectedLearnerId ?? ""}
                  onChange={(e) => setSelectedLearnerId(e.target.value)}
                >
                  {(learners ?? []).map((l) => (
                    <option key={l.id} value={l.id}>
                      {l.name} ({l.teamName}) — {l.targetRole}
                    </option>
                  ))}
                </select>
              </div>

              {selectedLearner ? (
                <div
                  style={{
                    border: "1px solid var(--border)",
                    borderRadius: 16,
                    padding: "0.85rem 1rem",
                    background: "#f7f9ff",
                    display: "grid",
                    gap: "0.45rem"
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      flexWrap: "wrap",
                      gap: "0.5rem"
                    }}
                  >
                    <strong>{selectedLearner.name}</strong>
                    <ReadinessBadge level={normalizeReadiness(selectedLearner.readiness)} />
                  </div>
                  <span className={styles.cellNameSub}>
                    {selectedLearner.teamName} · 目標ロール {selectedLearner.targetRole} · ロードマップ進捗{" "}
                    {selectedLearner.roadmapCompletionRate ?? 0}%
                  </span>
                  {selectedTemplate ? (
                    <p className={styles.fieldHelp} style={{ margin: 0 }}>
                      <strong>{selectedTemplate.name}</strong> の育成ロードマップを割り当てます。重点スキル:{" "}
                      {selectedTemplate.targetSkills.join(", ") || "—"}
                    </p>
                  ) : (
                    <p className={styles.fieldHelp} style={{ margin: 0 }}>
                      左の一覧からロールテンプレートを選んでください。
                    </p>
                  )}
                </div>
              ) : null}

              <div className={styles.actionRow} style={{ marginTop: "0.7rem" }}>
                <button
                  type="button"
                  className={styles.actionPrimary}
                  onClick={handleAssign}
                  disabled={!selectedTemplate || !selectedLearner || submitting}
                >
                  {submitting ? "割当中…" : <IconText icon="map">育成ロードマップを割当する</IconText>}
                </button>
              </div>
            </>
          )}
        </Section>
      </div>

      <Section
        title="割当履歴 (本セッション)"
        meta="再読み込みすると履歴は消えます。恒久的な記録は今後対応予定です。"
        theme="company"
        icon="calendarDays"
      >
        {history.length === 0 ? (
          <EmptyState
            icon={<AppIcon name="circleDashed" size={24} />}
            title="まだ割当がありません"
            message="左でテンプレを選び、右で待機人材を選んで「育成ロードマップを割当する」を押すと、ここに記録されます。"
          />
        ) : (
          <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gap: "0.5rem" }}>
            {history.map((h) => (
              <li
                key={h.id}
                style={{
                  border: "1px solid var(--border)",
                  borderRadius: 14,
                  padding: "0.7rem 0.9rem",
                  background: "var(--surface)",
                  display: "flex",
                  gap: "0.8rem",
                  alignItems: "center",
                  flexWrap: "wrap"
                }}
              >
                <span className={styles.evidenceMetaLabel}>{h.at.slice(0, 10)}</span>
                <strong style={{ fontSize: 13 }}>{h.learnerName}</strong>
                <span className={styles.cellNameSub}>→ {h.templateName}</span>
                <span className="status-pill status-success">{h.status}</span>
              </li>
            ))}
          </ul>
        )}
      </Section>
    </main>
  );
}
