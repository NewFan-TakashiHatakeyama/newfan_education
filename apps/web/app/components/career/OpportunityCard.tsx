import type { Opportunity } from "@newfan/contracts";

export function OpportunityCard({
  item,
  onOpen
}: {
  item: Opportunity;
  onOpen: (item: Opportunity) => void;
}) {
  return (
    <li className="opportunity-card">
      <div className="opportunity-head">
        <strong>{item.title}</strong>
        <span className={`status-pill ${item.type === "employment" ? "" : "pill-warm"}`}>
          {item.type === "employment" ? "求人" : "業務委託案件"}
        </span>
      </div>
      <p className="muted">提供者: {item.provider}</p>
      <p className="muted">契約形態: {item.contractType}</p>
      <p className="muted">報酬: {item.compensation}</p>
      <p className="muted">スキル一致: {item.skillMatchScore}%</p>
      <p className="muted">注意事項: {item.caution}</p>
      <div className="inline-actions">
        <button type="button" onClick={() => onOpen(item)}>
          詳細を見る
        </button>
        <button type="button" className="ghost-button">
          {item.type === "employment" ? "応募" : "提案"}
        </button>
      </div>
    </li>
  );
}
