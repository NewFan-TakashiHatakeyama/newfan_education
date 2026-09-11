"use client";
import { useState } from "react";
import Link from "next/link";
import type { VentureSummary } from "@newfan/contracts";
import { Disclosure } from "@/app/components/ui/Disclosure";
import styles from "./ventures.module.css";

const GROUPS = [
  { name: "計画・事業判断", pattern: /hypothesis|kpi|cash|econom|roi|business|estimate/ },
  { name: "評価・承認", pattern: /eval|gate|condition/ },
  { name: "担当・スキル", pattern: /staff|assignment/ },
  { name: "データ・設計・リスク", pattern: /data|model|privacy|arch|risk|feature|contract/ },
  { name: "運用・その他", pattern: /.*/ }
];

export function LedgerDirectory({ ventureId, ledgers }: { ventureId: string; ledgers: VentureSummary["ledgers"] }) {
  const [query, setQuery] = useState("");
  const matching = ledgers.filter(ledger => ledger.name.toLocaleLowerCase().includes(query.trim().toLocaleLowerCase()));
  const links = (rows: typeof ledgers) => <div className={styles.ledgerLinks}>{rows.map(ledger => <Link key={ledger.key} href={`/ventures/${ventureId}/ledgers/${ledger.key}`} className={styles.ledgerLink}>
    <span className={styles.ledgerName}>{ledger.name}</span><span className={styles.muted}>{ledger.total === 0 ? "未登録" : `入力あり ${ledger.filled} / ${ledger.total}`}</span>
  </Link>)}</div>;
  return <>
    <label className={styles.field}>台帳を検索<input type="search" placeholder="例：評価、リスク、配置" value={query} onChange={event => setQuery(event.target.value)} /></label>
    {query.trim() ? (matching.length ? links(matching) : <p>該当する台帳はありません。</p>) : GROUPS.map((group, index) => {
      const rows = ledgers.filter(ledger => GROUPS.findIndex(item => item.pattern.test(ledger.key)) === index);
      return rows.length ? <Disclosure key={group.name} title={`${group.name}（${rows.length}）`}>{links(rows)}</Disclosure> : null;
    })}
  </>;
}
