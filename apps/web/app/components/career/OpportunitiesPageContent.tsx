"use client";

import { useEffect, useMemo, useState } from "react";
import {
  applyOpportunity,
  getMyOpportunityApplications,
  getOpportunities,
  withdrawOpportunity
} from "@/lib/api";
import { EmptyState } from "@/app/components/product/EmptyState";
import { OpportunityCard } from "@/app/components/career/OpportunityCard";
import type { Opportunity, OpportunityApplicationState, OpportunityType } from "@newfan/contracts";

type CareerTab = "employment" | "freelance" | "recommended" | "saved" | "in_progress";
const APPLICATION_STATE_LABEL: Record<OpportunityApplicationState, string> = {
  none: "未対応",
  applied: "応募済み",
  screening: "書類選考",
  interview: "面接",
  offer: "内定",
  proposed: "提案済み",
  proposal_review: "提案審査",
  negotiation: "条件調整",
  contracted: "契約完了"
};

export default function OpportunitiesPageContent({ heading }: { heading: string }) {
  const [tab, setTab] = useState<CareerTab>("employment");
  const [selected, setSelected] = useState<Opportunity | null>(null);
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [applicationStateById, setApplicationStateById] = useState<
    Record<string, OpportunityApplicationState>
  >({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        setError(null);
        setLoading(true);
        const [opportunitySummary, applicationSummary] = await Promise.all([
          getOpportunities(),
          getMyOpportunityApplications()
        ]);
        setOpportunities(opportunitySummary.items);
        setApplicationStateById(applicationSummary.applications);
      } catch (e) {
        setError(e instanceof Error ? e.message : "求人/案件の取得に失敗しました");
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, []);

  const filtered = useMemo(() => {
    if (tab === "recommended") {
      return opportunities.filter((item) => item.isRecommended);
    }
    if (tab === "saved") {
      return opportunities.filter((item) => item.isSaved);
    }
    if (tab === "in_progress") {
      return opportunities.filter((item) => (applicationStateById[item.id] ?? "none") !== "none");
    }
    const map: Record<"employment" | "freelance", OpportunityType> = {
      employment: "employment",
      freelance: "freelance"
    };
    return opportunities.filter((item) => item.type === map[tab]);
  }, [applicationStateById, opportunities, tab]);

  function getApplicationState(item: Opportunity): OpportunityApplicationState {
    return applicationStateById[item.id] ?? "none";
  }

  function getActionLabel(item: Opportunity, state: OpportunityApplicationState) {
    if (state === "none") {
      return item.type === "employment" ? "応募する" : "提案する";
    }
    return APPLICATION_STATE_LABEL[state];
  }

  async function submitFromDrawer(item: Opportunity) {
    try {
      setError(null);
      const updated = await applyOpportunity(item.id, item.type);
      setApplicationStateById((prev) => ({ ...prev, [item.id]: updated.state }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "応募/提案処理に失敗しました");
    }
  }

  async function withdrawFromDrawer(item: Opportunity) {
    try {
      setError(null);
      const updated = await withdrawOpportunity(item.id);
      setApplicationStateById((prev) => ({ ...prev, [item.id]: updated.state }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "取り下げ処理に失敗しました");
    }
  }

  return (
    <main>
      <div className="page-header">
        <h1>{heading}</h1>
        <p className="muted">雇用求人と業務委託案件を明確に分離し、スキル証跡に合う機会を提示します。</p>
      </div>
      {error && <p className="error">{error}</p>}

      <section>
        <h2>タブ</h2>
        <div className="inline-actions">
          <button
            type="button"
            className={tab === "employment" ? "tab-button tab-button-active" : "tab-button"}
            onClick={() => setTab("employment")}
          >
            求人
          </button>
          <button
            type="button"
            className={tab === "freelance" ? "tab-button tab-button-active" : "tab-button"}
            onClick={() => setTab("freelance")}
          >
            業務委託案件
          </button>
          <button
            type="button"
            className={tab === "recommended" ? "tab-button tab-button-active" : "tab-button"}
            onClick={() => setTab("recommended")}
          >
            おすすめ
          </button>
          <button
            type="button"
            className={tab === "saved" ? "tab-button tab-button-active" : "tab-button"}
            onClick={() => setTab("saved")}
          >
            保存済み
          </button>
          <button
            type="button"
            className={tab === "in_progress" ? "tab-button tab-button-active" : "tab-button"}
            onClick={() => setTab("in_progress")}
          >
            応募/提案中
          </button>
        </div>
      </section>

      <div className="career-layout">
        <section>
          <h2>一覧カード</h2>
          {loading ? (
            <div>
              <div className="skeleton" />
              <div className="skeleton" />
              <div className="skeleton" />
            </div>
          ) : null}
          {!loading && filtered.length === 0 ? (
            <EmptyState
              title="候補なし"
              message="条件に一致する求人/案件がありません。タブを変更してください。"
            />
          ) : (
            <ul className="card-list">
              {filtered.map((item) => (
                <OpportunityCard key={item.id} item={item} onOpen={setSelected} />
              ))}
            </ul>
          )}
        </section>

        <aside className="drawer-panel">
          <h2>詳細ドロワー</h2>
          {!selected ? (
            <p className="muted">一覧カードを選択すると詳細を表示します。</p>
          ) : (
            <div>
              <h3>{selected.title}</h3>
              <p>{selected.summary}</p>
              <p className="muted">契約: {selected.contractType}</p>
              <p className="muted">報酬: {selected.compensation}</p>
              <p className="muted">支払い条件: {selected.paymentTerms}</p>
              <h4>必要スキル</h4>
              <ul>
                {selected.requiredSkills.map((skill) => (
                  <li key={skill}>{skill}</li>
                ))}
              </ul>
              <div className="inline-actions">
                <button type="button" onClick={() => submitFromDrawer(selected)}>
                  {getActionLabel(selected, getApplicationState(selected))}
                </button>
                {getApplicationState(selected) !== "none" && (
                  <button type="button" className="ghost-button" onClick={() => withdrawFromDrawer(selected)}>
                    取り下げ
                  </button>
                )}
              </div>
              <p className="muted">
                現在状態: {APPLICATION_STATE_LABEL[getApplicationState(selected)]}
              </p>
            </div>
          )}
        </aside>
      </div>

      <section>
        <p className="muted">
          注意: 雇用求人と業務委託案件は法務要件が異なるため、表示・導線・契約情報を明確に分けています。
        </p>
      </section>
    </main>
  );
}
