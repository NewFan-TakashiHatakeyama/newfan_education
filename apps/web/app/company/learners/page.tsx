"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";

import type { LearnerSummary } from "@newfan/contracts";

import { getLearners } from "@/lib/api";

import { PageHero } from "@/app/components/ui/PageHero";
import { Section } from "@/app/components/ui/Section";
import { EmptyState } from "@/app/components/ui/EmptyState";
import { SkeletonRow } from "@/app/components/ui/Skeleton";
import { FilterChips, type FilterOption } from "@/app/components/ui/FilterChips";
import { SkillChip } from "@/app/components/ui/SkillChip";
import {
  ReadinessBadge,
  normalizeReadiness,
  type ReadinessLevel
} from "@/app/components/ui/ReadinessBadge";
import { AppIcon, IconText } from "@/app/components/ui/Icon";

import styles from "@/app/components/ui/ui.module.css";

type ReadinessFilter = "all" | ReadinessLevel;

const READINESS_FILTERS: Array<FilterOption<ReadinessFilter>> = [
  { value: "all", label: "すべて" },
  { value: "Ready", label: "Ready（PoC着手可）" },
  { value: "Almost", label: "Almost（メンター伴走）" },
  { value: "Need Training", label: "Need Training（追加育成）" },
  { value: "Not Started", label: "Not Started（未着手）" }
];

export default function CompanyLearnersPage() {
  const [learners, setLearners] = useState<LearnerSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [teamFilter, setTeamFilter] = useState<string>("all");
  const [roleFilter, setRoleFilter] = useState<string>("all");
  const [readinessFilter, setReadinessFilter] = useState<ReadinessFilter>("all");

  useEffect(() => {
    let active = true;
    getLearners()
      .then((res) => {
        if (active) {
          setLearners(res.items);
          setError(null);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setLearners([]);
          setError(
            err instanceof Error
              ? err.message
              : "受講者一覧の取得に失敗しました。"
          );
        }
      });
    return () => {
      active = false;
    };
  }, []);

  const teamOptions: Array<FilterOption<string>> = useMemo(() => {
    const counts = new Map<string, number>();
    (learners ?? []).forEach((l) => {
      counts.set(l.teamName, (counts.get(l.teamName) ?? 0) + 1);
    });
    return [
      { value: "all", label: "すべて", count: learners?.length ?? 0 },
      ...Array.from(counts.entries())
        .sort((a, b) => b[1] - a[1])
        .map(([team, count]) => ({ value: team, label: team, count }))
    ];
  }, [learners]);

  const roleOptions: Array<FilterOption<string>> = useMemo(() => {
    const counts = new Map<string, number>();
    (learners ?? []).forEach((l) => {
      counts.set(l.targetRole, (counts.get(l.targetRole) ?? 0) + 1);
    });
    return [
      { value: "all", label: "すべて", count: learners?.length ?? 0 },
      ...Array.from(counts.entries())
        .sort((a, b) => b[1] - a[1])
        .map(([role, count]) => ({ value: role, label: role, count }))
    ];
  }, [learners]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return (learners ?? []).filter((l) => {
      if (teamFilter !== "all" && l.teamName !== teamFilter) return false;
      if (roleFilter !== "all" && l.targetRole !== roleFilter) return false;
      if (readinessFilter !== "all" && normalizeReadiness(l.readiness) !== readinessFilter)
        return false;
      if (q) {
        const haystack = `${l.name} ${l.teamName} ${l.targetRole} ${
          (l.strongSkills ?? []).join(" ")
        } ${(l.gapSkills ?? []).join(" ")}`.toLowerCase();
        if (!haystack.includes(q)) return false;
      }
      return true;
    });
  }, [learners, search, teamFilter, roleFilter, readinessFilter]);

  const summary = useMemo(() => {
    const safe = learners ?? [];
    const ready = safe.filter((l) => l.readiness === "Ready").length;
    const almost = safe.filter((l) => l.readiness === "Almost").length;
    const need = safe.filter((l) => l.readiness === "Need Training").length;
    return { total: safe.length, ready, almost, need };
  }, [learners]);

  const isLoading = learners === null;

  return (
    <main className={styles.page}>
      <PageHero
        theme="company"
        ariaLabel="受講者一覧"
        eyebrow="受講者一覧"
        title="受講者の育成進捗と実務準備度を一覧で確認"
        lead={
          <>
            受講者の氏名・所属・目標ロール・ロードマップ進捗・レビュー待ち提出・到達スキル・実務準備度を
            横断的に比較します。PoC着手可・メンター伴走が必要なメンバーを素早く特定できます。
          </>
        }
        metrics={[
          { label: "受講者", value: summary.total, suffix: "名", hint: "育成対象として登録済み" },
          { label: "Ready", value: summary.ready, suffix: "名", hint: "PoC着手可" },
          { label: "Almost", value: summary.almost, suffix: "名", hint: "メンター伴走" },
          {
            label: "Need Training",
            value: summary.need,
            suffix: "名",
            hint: "追加育成が必要"
          }
        ]}
        actions={
          <>
            <Link href="/company/roadmaps" className={styles.actionPrimary}>
              <IconText icon="map">ロードマップを割り当て</IconText>
            </Link>
            <Link href="/company/reports" className={styles.actionGhost}>
              <IconText icon="barChart3">AIプロジェクト候補を生成</IconText>
            </Link>
          </>
        }
      />

      {error ? (
        <div className={styles.section} role="alert">
          <p className="muted" style={{ margin: 0 }}>
            {error}{" "}
            必要な権限を持つアカウントでサインインして再読み込みしてください。
          </p>
        </div>
      ) : null}

      <Section
        title="絞り込み"
        meta="氏名・所属・目標ロール・実務準備度で絞り込みできます。"
        theme="company"
        icon="funnel"
      >
        <div style={{ display: "grid", gap: "0.85rem" }}>
          <div className={styles.field}>
            <label htmlFor="learner-search" className={styles.fieldLabel}>
              キーワード検索
            </label>
            <input
              id="learner-search"
              type="search"
              className={styles.fieldInput}
              placeholder="氏名・スキル・所属で検索"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <FilterChips
            label="所属"
            options={teamOptions}
            selected={teamFilter}
            onChange={setTeamFilter}
          />
          <FilterChips
            label="目標ロール"
            options={roleOptions}
            selected={roleFilter}
            onChange={setRoleFilter}
          />
          <FilterChips
            label="実務準備度"
            options={READINESS_FILTERS}
            selected={readinessFilter}
            onChange={setReadinessFilter}
          />
        </div>
      </Section>

      <Section
        title={`受講者一覧 (${filtered.length} 名)`}
        meta="詳細画面からロードマップ・成果物・AIテーマ適合・プロジェクト候補を確認できます。"
        theme="company"
        icon="users"
      >
        {isLoading ? (
          <SkeletonRow widths={["80%", "60%", "70%", "50%"]} />
        ) : filtered.length === 0 ? (
          (learners?.length ?? 0) === 0 ? (
            <EmptyState
              icon={<AppIcon name="circleDashed" size={24} />}
              title="受講者がまだ登録されていません"
              message="必要な権限を持つアカウントでサインインし、受講者を招待してください。"
              action={
                <Link href="/auth/sign-in" className={styles.actionPrimary}>
                  <IconText icon="userRound">サインインを開く</IconText>
                </Link>
              }
            />
          ) : (
            <EmptyState
              icon={<AppIcon name="funnel" size={24} />}
              title="該当する受講者がありません"
              message="絞り込み条件を緩めるか、別のキーワードでお試しください。"
              action={
                <button
                  type="button"
                  className={styles.actionGhost}
                  onClick={() => {
                    setSearch("");
                    setTeamFilter("all");
                    setRoleFilter("all");
                    setReadinessFilter("all");
                  }}
                >
                  フィルタをリセット
                </button>
              }
            />
          )
        ) : (
          <div className={styles.tableScroll}>
            <table className={styles.dataTable}>
              <thead>
                <tr>
                  <th scope="col">氏名 / 所属</th>
                  <th scope="col">目標ロール</th>
                  <th scope="col">育成進捗</th>
                  <th scope="col">レビュー待ち提出</th>
                  <th scope="col">到達スキル</th>
                  <th scope="col">実務準備度</th>
                  <th scope="col">操作</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((l) => (
                  <tr key={l.id}>
                    <td>
                      <div className={styles.cellName}>
                        <span className={styles.cellNameMain}>{l.name}</span>
                        <span className={styles.cellNameSub}>{l.teamName}</span>
                      </div>
                    </td>
                    <td>{l.targetRole}</td>
                    <td style={{ minWidth: 120 }}>
                      <div className={styles.miniProgress}>
                        <div className={styles.miniProgressTrack}>
                          <div
                            className={styles.miniProgressFill}
                            style={{
                              width: `${Math.min(100, Math.max(2, l.roadmapCompletionRate ?? 0))}%`
                            }}
                          />
                        </div>
                        <span className={styles.miniProgressLabel}>
                          {l.roadmapCompletionRate ?? 0}%
                        </span>
                      </div>
                    </td>
                    <td>
                      <span style={{ fontWeight: 600 }}>{l.pendingSubmissionCount ?? 0}</span>
                      <span style={{ color: "#94a3b8", fontSize: 11, marginLeft: 4 }}>件</span>
                    </td>
                    <td>
                      <div className={styles.skillChips}>
                        {(l.strongSkills ?? []).slice(0, 3).map((s) => (
                          <SkillChip key={`${l.id}-s-${s}`} label={s} tone="strong" />
                        ))}
                        {(l.gapSkills ?? []).slice(0, 2).map((s) => (
                          <SkillChip key={`${l.id}-g-${s}`} label={s} tone="gap" />
                        ))}
                      </div>
                    </td>
                    <td>
                      <ReadinessBadge level={normalizeReadiness(l.readiness)} />
                    </td>
                    <td>
                      <div className={styles.actionRow}>
                        <Link
                          href={`/company/learners/${l.id}`}
                          className={styles.actionGhost}
                          style={{ fontSize: 12, padding: "0.35rem 0.7rem" }}
                        >
                          <IconText icon="search">詳細を見る</IconText>
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>
    </main>
  );
}
